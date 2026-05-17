"""
HTTP-level security helpers — auth dependency + client-IP extraction.

``get_current_user`` is the canonical FastAPI dependency for protected
routes. It reads a JWT from the ``access_token`` cookie (preferred) or the
``Authorization: Bearer ...`` header, validates it, and loads the user
document from Mongo.

``get_client_ip`` honours ``X-Forwarded-For`` only when the request reached
us through a known reverse proxy — otherwise it falls back to the socket
peer. Mis-trusting ``X-Forwarded-For`` would let any caller spoof a fake IP
to bypass per-IP rate limits.
"""

from __future__ import annotations

from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from utils.auth import InvalidTokenError, decode_token
from utils.cookies import ACCESS_COOKIE
from utils.db import get_db

# Generic 401 — never tell the caller WHICH check failed (token vs user vs disabled).
_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


def _extract_access_token(request: Request) -> Optional[str]:
    """Return the JWT from cookie or ``Authorization`` header, or None."""
    cookie = request.cookies.get(ACCESS_COOKIE)
    if cookie:
        return cookie
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


async def get_current_user(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """FastAPI dependency: validate the JWT and return the user document.

    Raises ``HTTPException(401)`` with a generic message on ANY failure
    (no token, bad signature, expired, missing user, disabled user).
    Route handlers must NOT translate the underlying error — the generic
    response is the whole point.
    """
    token = _extract_access_token(request)
    if not token:
        raise _UNAUTH

    try:
        payload = decode_token(token, expected_type="access")
    except InvalidTokenError:
        raise _UNAUTH from None

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise _UNAUTH

    try:
        user_id = ObjectId(subject)
    except (InvalidId, TypeError):
        raise _UNAUTH from None

    user = await db.users.find_one({"_id": user_id})
    if not user or user.get("disabled"):
        raise _UNAUTH

    return user


async def require_admin(
    user: dict = Depends(get_current_user),
) -> dict:
    """FastAPI dependency: deny unless the authenticated user is an admin.

    Layered on top of :func:`get_current_user` so a missing / expired token
    still returns 401 (handled there); only the role check produces a 403,
    matching the standard "authenticated but not authorised" semantics.

    Returns the same user document on success so handlers can both authorise
    and consume the user in one dependency.
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user


def get_client_ip(request: Request) -> str:
    """Best-effort client IP for rate limiting.

    Reads ``X-Forwarded-For`` only when ``TRUST_PROXY_HEADERS`` is truthy
    (set this in production behind a reverse proxy like Cloudflare / Nginx).
    Otherwise falls back to the socket peer address. Returns ``"unknown"``
    if neither is available.
    """
    import os  # local import — keeps test patching surface small

    if os.getenv("TRUST_PROXY_HEADERS", "false").lower() in ("1", "true", "yes"):
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            # Left-most non-empty entry is the original client.
            first = xff.split(",")[0].strip()
            if first:
                return first

    client = request.client
    if client and client.host:
        return client.host
    return "unknown"
