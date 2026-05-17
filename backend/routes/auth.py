"""
Authentication endpoints for Hils Marketing.

Endpoints
---------
================  ===================================================
``POST``          ``/api/auth/register``       create account + cookies
``POST``          ``/api/auth/login``          credentials + lockout
``POST``          ``/api/auth/logout``         revoke refresh + clear
``GET``           ``/api/auth/me``             current user profile
``POST``          ``/api/auth/forgot-password``  start reset (dev: log token)
``POST``          ``/api/auth/reset-password``   complete reset
================  ===================================================

Security model (also see DOCS/auth.md and DOCS/security.md)
-----------------------------------------------------------
- Passwords: bcrypt cost 12, SHA-256-prehashed in ``utils.auth``.
- JWT: HS256, access 12 h, refresh 7 d (env-overridable). Both delivered
  as httpOnly cookies AND in the response body for non-browser clients.
- Per-IP-per-email lockout on ``/login``: 5 failures lock the pair for
  15 minutes. Stored in ``login_attempts`` Mongo collection (TTL = 1 h).
- Refresh tokens: ``jti`` stored in ``refresh_tokens`` so logout / reset
  can revoke (sets ``revoked_at``). TTL index drops expired rows.
- Password reset: token plaintext sent to user; only the SHA-256 ``hash``
  is stored. 1-hour expiry, single use. Dev environment logs the
  plaintext to stdout in lieu of email.
- ``/forgot-password`` always returns 204, regardless of whether the
  email exists, to avoid account enumeration.

Example curl
------------
::

    # 1. Register a new customer
    curl -X POST http://localhost:8000/api/auth/register \\
      -H 'Content-Type: application/json' \\
      -c cookies.txt \\
      -d '{"email":"test@hils.pk","password":"Test@123","name":"Test User"}'

    # 2. Login (cookies are stored in cookies.txt)
    curl -X POST http://localhost:8000/api/auth/login \\
      -H 'Content-Type: application/json' \\
      -c cookies.txt -b cookies.txt \\
      -d '{"email":"test@hils.pk","password":"Test@123"}'

    # 3. Authenticated read
    curl http://localhost:8000/api/auth/me -b cookies.txt

    # 4. Logout
    curl -X POST http://localhost:8000/api/auth/logout -b cookies.txt

    # 5. Forgot / reset password
    curl -X POST http://localhost:8000/api/auth/forgot-password \\
      -H 'Content-Type: application/json' \\
      -d '{"email":"test@hils.pk"}'
    # (look at backend stdout for "DEV ONLY — password reset token ...")
    curl -X POST http://localhost:8000/api/auth/reset-password \\
      -H 'Content-Type: application/json' \\
      -d '{"token":"<paste-here>","new_password":"Newer@123"}'
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from models import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    Token,
    UserResponse,
)
from utils.auth import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from utils.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from utils.db import get_db
from utils.security import get_client_ip, get_current_user

log = logging.getLogger("hils.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ----------------------------------------------------------------------------
# Tunables (env-overridable but with sane defaults)
# ----------------------------------------------------------------------------
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

# Generic credential-failure HTTPException — used for BOTH "no such user" and
# "wrong password" so the response shape leaks nothing about which step failed.
_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password",
)


# ============================================================================
# Helpers
# ============================================================================
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _access_seconds() -> int:
    return int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "12")) * 3600


def _refresh_seconds() -> int:
    return int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "7")) * 86400


def _reset_ttl_minutes() -> int:
    return int(os.getenv("RESET_TOKEN_TTL_MINUTES", "60"))


def _to_user_response(doc: dict[str, Any]) -> UserResponse:
    """Build a safe public projection from a Mongo user document.

    Strips ``password_hash`` and other internal fields; converts ``_id`` to
    the string form clients expect.
    """
    return UserResponse(
        id=str(doc["_id"]),
        email=doc["email"],
        name=doc["name"],
        role=doc.get("role", "customer"),
        phone=doc.get("phone"),
        created_at=doc["created_at"],
    )


async def _issue_tokens(
    db: AsyncIOMotorDatabase,
    user_id: str,
    response: Response,
) -> Token:
    """Mint access + refresh JWTs, set cookies, persist refresh ``jti``."""
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    # Persist the refresh token's jti so logout / reset can revoke.
    refresh_payload = decode_token(refresh_token, expected_type="refresh")
    await db.refresh_tokens.insert_one({
        "user_id": user_id,
        "jti": refresh_payload["jti"],
        "issued_at": datetime.fromtimestamp(refresh_payload["iat"], tz=timezone.utc),
        "expires_at": datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
        "revoked_at": None,
    })

    access_seconds = _access_seconds()
    set_auth_cookies(
        response,
        access_token=access_token,
        refresh_token=refresh_token,
        access_seconds=access_seconds,
        refresh_seconds=_refresh_seconds(),
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_seconds,
    )


# ---------------------------------------------------------------------------
# Login-attempt tracking (per-IP-per-email lockout)
# ---------------------------------------------------------------------------
def _login_identifier(ip: str, email: str) -> str:
    return f"{ip}:{email.lower()}"


async def _check_login_lockout(db: AsyncIOMotorDatabase, identifier: str) -> None:
    """Raise 429 if the (ip, email) pair is currently locked out."""
    doc = await db.login_attempts.find_one({"_id": identifier})
    if not doc:
        return
    locked_until = doc.get("locked_until")
    if locked_until and locked_until > _utcnow():
        retry_after = int((locked_until - _utcnow()).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
            headers={"Retry-After": str(max(retry_after, 1))},
        )


async def _record_login_failure(db: AsyncIOMotorDatabase, identifier: str) -> None:
    """Increment the failure counter; lock the pair if it crosses the threshold."""
    now = _utcnow()
    doc = await db.login_attempts.find_one_and_update(
        {"_id": identifier},
        {
            "$inc": {"attempts": 1},
            "$set": {"updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if doc and doc.get("attempts", 0) >= LOGIN_MAX_ATTEMPTS:
        await db.login_attempts.update_one(
            {"_id": identifier},
            {"$set": {"locked_until": now + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)}},
        )


async def _clear_login_failures(db: AsyncIOMotorDatabase, identifier: str) -> None:
    """Wipe the failure record on a successful login."""
    await db.login_attempts.delete_one({"_id": identifier})


# ============================================================================
# Endpoints
# ============================================================================
@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Create a customer account and return JWT cookies + body tokens.",
)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Token:
    email = body.email.lower()

    if await db.users.find_one({"email": email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    now = _utcnow()
    user_doc = {
        "email": email,
        "password_hash": hash_password(body.password),
        "name": body.name,
        "role": "customer",
        "phone": body.phone,
        "disabled": False,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(user_doc)

    log.info("user.registered id=%s email_hash=%s", result.inserted_id, hashlib.sha256(email.encode()).hexdigest()[:12])
    return await _issue_tokens(db, str(result.inserted_id), response)


@router.post(
    "/login",
    response_model=Token,
    summary="Verify credentials; rate-limited per (IP, email) pair.",
)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Token:
    email = body.email.lower()
    identifier = _login_identifier(get_client_ip(request), email)

    await _check_login_lockout(db, identifier)

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        await _record_login_failure(db, identifier)
        raise _INVALID_CREDENTIALS

    if user.get("disabled"):
        # Disabled users register as "credential failure" so we don't reveal
        # account existence vs. account-disabled to outsiders.
        await _record_login_failure(db, identifier)
        raise _INVALID_CREDENTIALS

    await _clear_login_failures(db, identifier)
    log.info("user.login id=%s", user["_id"])
    return await _issue_tokens(db, str(user["_id"]), response)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear auth cookies and revoke the presented refresh token.",
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    raw_refresh = request.cookies.get(REFRESH_COOKIE)
    if raw_refresh:
        try:
            payload = decode_token(raw_refresh, expected_type="refresh")
            await db.refresh_tokens.update_one(
                {"jti": payload["jti"]},
                {"$set": {"revoked_at": _utcnow()}},
            )
        except InvalidTokenError:
            # Token is malformed/expired/wrong type — still clear cookies below.
            pass

    # Must return the SAME `response` object we mutated — returning a fresh
    # Response(204) drops the Set-Cookie headers that clear the jar.
    clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the authenticated user's profile (no password_hash).",
)
async def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(current_user)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Start the password-reset flow. Always returns 204 (no enumeration).",
)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    email = body.email.lower()
    user = await db.users.find_one({"email": email})

    # Always 204 — same response shape whether the email exists or not.
    if user:
        token = secrets.token_urlsafe(48)              # 64-char URL-safe
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = _utcnow() + timedelta(minutes=_reset_ttl_minutes())

        await db.password_reset_tokens.insert_one({
            "user_id": str(user["_id"]),
            "token_hash": token_hash,
            "expires_at": expires_at,
            "used_at": None,
            "created_at": _utcnow(),
        })

        app_env = os.getenv("APP_ENV", "development")
        if app_env != "production":
            # DEV ONLY — in prod this goes via SMTP (utils/email.py, future).
            log.warning(
                "DEV ONLY — password reset token for %s: %s (expires %s)",
                email,
                token,
                expires_at.isoformat(),
            )
        else:
            # TODO(email): send via SMTP once utils/email.py lands.
            log.info("password.reset.requested email_hash=%s", hashlib.sha256(email.encode()).hexdigest()[:12])

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Complete the password-reset flow with a valid one-time token.",
)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    now = _utcnow()

    record = await db.password_reset_tokens.find_one({
        "token_hash": token_hash,
        "used_at": None,
        "expires_at": {"$gt": now},
    })
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid, expired, or has already been used",
        )

    from bson import ObjectId
    new_hash = hash_password(body.new_password)

    await db.users.update_one(
        {"_id": ObjectId(record["user_id"])},
        {"$set": {"password_hash": new_hash, "updated_at": now}},
    )
    await db.password_reset_tokens.update_one(
        {"_id": record["_id"]},
        {"$set": {"used_at": now}},
    )
    # Security: invalidate every outstanding refresh token for this user, so
    # an attacker who stole one before the reset can't keep using it.
    await db.refresh_tokens.update_many(
        {"user_id": record["user_id"], "revoked_at": None},
        {"$set": {"revoked_at": now}},
    )

    log.info("password.reset.completed user_id=%s", record["user_id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)
