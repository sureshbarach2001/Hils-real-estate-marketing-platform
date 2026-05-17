"""
Authentication utilities for Hils Marketing.

Provides:
    - hash_password(plain)           -> str       bcrypt hash
    - verify_password(plain, hashed) -> bool      constant-time compare
    - create_access_token(subject)   -> str       12h JWT (type="access")
    - create_refresh_token(subject)  -> str       7d  JWT (type="refresh")
    - decode_token(token, expected_type=None) -> dict   validates + returns claims

Approach
--------
- Passwords: bcrypt library directly (cost factor 12, random salt per hash).
  passlib was dropped — it is unmaintained and logs spurious errors against
  modern bcrypt (missing ``__about__.__version__``).
- JWT:       python-jose with HS256 (symmetric, simple, fast). Tokens always
             carry a `type` claim ("access" or "refresh") so an access token
             can NEVER be presented in place of a refresh token.

Security notes (see also DOCS/security.md)
------------------------------------------
- `JWT_SECRET` is read lazily from the environment so this module can be
  imported in tooling that doesn't have secrets configured (e.g. CI smoke
  tests, `python -c "from utils.auth import hash_password; ..."`).
- Tokens include `iat`, `exp`, `sub`, `jti`, `type` — `jti` is unique per
  token so the refresh-token rotation flow can revoke old ones server-side.
- `decode_token` raises `InvalidTokenError` on any verification failure;
  callers should map this to HTTP 401 — never leak the underlying reason
  to the client.
- NEVER log the raw token. If you must, mask to first 6 chars: `tok[:6] + "..."`.

Quick test
----------
    >>> h = hash_password("hunter2")
    >>> verify_password("hunter2", h)
    True
    >>> verify_password("wrong", h)
    False
"""

from __future__ import annotations

import base64
import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

import bcrypt
from jose import JWTError, jwt

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
TokenType = Literal["access", "refresh"]

# Bcrypt work factor (2^12 iterations). Do not lower — see hash_password docstring.
_BCRYPT_ROUNDS = 12


def _prehash(plain: str) -> bytes:
    """SHA-256 + base64-encode the password before handing it to bcrypt.

    Why
    ---
    bcrypt has a hard 72-byte input limit (4.x raises ValueError, older
    versions silently truncated). Pre-hashing with SHA-256 produces a
    fixed-length 44-byte (base64) digest, so passwords of any length work
    consistently. This is the standard "bcrypt + SHA-256" construction
    used by Dropbox, Auth0, and many others.

    Trade-off: this changes hash semantics — hashes generated WITHOUT the
    pre-hash will not verify. Applied during init phase before any users
    exist, so no migration is needed.
    """
    digest = hashlib.sha256(plain.encode("utf-8")).digest()
    return base64.b64encode(digest)


class InvalidTokenError(Exception):
    """Raised when a JWT is missing, malformed, expired, or of the wrong type.

    Callers (route handlers) should translate this into an HTTP 401 response
    with a generic message like "Invalid or expired token" — do NOT leak the
    underlying reason.
    """


# ----------------------------------------------------------------------------
# Configuration — read lazily so the module imports without env set
# ----------------------------------------------------------------------------
def _jwt_config() -> dict[str, Any]:
    """Return JWT config from env, raising clearly if `JWT_SECRET` is missing.

    Called by every token op (create/decode). Read-time access means a
    deployment can rotate the secret without rebuilding the image — just set
    the new value and restart the process.
    """
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET env var is required for token operations. "
            "Generate one with: openssl rand -hex 32"
        )
    return {
        "secret": secret,
        "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
        "access_hours": int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "12")),
        "refresh_days": int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "7")),
    }


# ============================================================================
# Password hashing
# ============================================================================
def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt (cost factor 12, with random salt).

    Parameters
    ----------
    plain : str
        The user-supplied plaintext password. Length is NOT enforced here —
        do that in the Pydantic model (`UserCreate.password`).

    Returns
    -------
    str
        A self-contained bcrypt hash like
        ``$2b$12$KIXxPfnK9PfgRz3hKLwvzeQ8q...`` which encodes the algorithm,
        cost factor, salt, and digest. Safe to store in MongoDB as-is.

    Security
    --------
    - Bcrypt is intentionally slow (~250 ms / hash on modern hardware) to
      resist offline brute-force. Do NOT lower the cost factor.
    - Each call uses a fresh random salt, so two identical passwords produce
      two different hashes. Never compare hashes directly — always use
      :func:`verify_password`.
    - NEVER log either `plain` or the returned hash.

    Example
    -------
        >>> h = hash_password("hunter2")
        >>> h.startswith("$2b$")
        True
    """
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(_prehash(plain), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time compare a plaintext password against a bcrypt hash.

    Parameters
    ----------
    plain : str
        The plaintext password from the login form.
    hashed : str
        The bcrypt hash previously produced by :func:`hash_password`
        (typically loaded from ``users.password_hash`` in MongoDB).

    Returns
    -------
    bool
        ``True`` if the password matches, ``False`` otherwise.
        Catches malformed hashes internally and returns ``False`` rather
        than raising — login routes should treat any failure identically
        to avoid leaking which step failed.

    Security
    --------
    - ``bcrypt.checkpw`` uses constant-time comparison to resist timing attacks.
    - Always return the SAME generic error message ("invalid credentials")
      regardless of whether the email exists or the password is wrong —
      otherwise you leak account existence.
    """
    try:
        return bcrypt.checkpw(_prehash(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed hash on file — treat as a non-match, never raise to caller.
        return False


# ============================================================================
# JWT helpers
# ============================================================================
def _create_token(subject: str, token_type: TokenType, expires_in: timedelta) -> str:
    """Internal: build + sign a JWT with the standard Hils claim set."""
    cfg = _jwt_config()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_in).timestamp()),
        "jti": uuid.uuid4().hex,            # rotation id — track in `sessions`
        "type": token_type,
    }
    return jwt.encode(payload, cfg["secret"], algorithm=cfg["algorithm"])


def create_access_token(subject: str) -> str:
    """Create a short-lived access JWT (default 12 h).

    Parameters
    ----------
    subject : str
        Stable identifier for the principal — typically the Mongo
        ``str(user["_id"])``. Stored in the ``sub`` claim.

    Returns
    -------
    str
        A signed compact JWT (`header.payload.signature`) suitable for
        storing in an ``access_token`` httpOnly cookie.

    Security
    --------
    - Access tokens are deliberately short-lived to limit blast radius if
      stolen. Refresh via :func:`create_refresh_token` rather than extending.
    - The ``type="access"`` claim means this token will be rejected on the
      ``/auth/refresh`` endpoint (which calls ``decode_token(..., expected_type="refresh")``).
    - Token TTL is read from ``JWT_ACCESS_TOKEN_HOURS`` (default 12).

    Example
    -------
        >>> token = create_access_token("65abf...e09")      # doctest: +SKIP
        >>> decode_token(token, expected_type="access")["sub"]  # doctest: +SKIP
        '65abf...e09'
    """
    cfg = _jwt_config()
    return _create_token(subject, "access", timedelta(hours=cfg["access_hours"]))


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh JWT (default 7 d).

    Parameters
    ----------
    subject : str
        Stable identifier for the principal (Mongo user id).

    Returns
    -------
    str
        A signed compact JWT. Store in the ``refresh_token`` httpOnly cookie
        scoped to ``/api/auth/refresh`` so it's never sent on other routes.

    Security
    --------
    - The ``type="refresh"`` claim prevents this token from being used as
      an access token on protected endpoints.
    - Each token has a unique ``jti``. The refresh route should persist the
      latest valid ``jti`` per user and reject any older one (rotation +
      reuse-detection: if an old `jti` appears, force-logout the user).
    - Token TTL is read from ``JWT_REFRESH_TOKEN_DAYS`` (default 7).
    """
    cfg = _jwt_config()
    return _create_token(subject, "refresh", timedelta(days=cfg["refresh_days"]))


def decode_token(token: str, expected_type: Optional[TokenType] = None) -> dict[str, Any]:
    """Verify a JWT's signature + expiry and return its claims.

    Parameters
    ----------
    token : str
        The compact JWT string to verify.
    expected_type : {"access", "refresh"} or None, optional
        If given, also reject tokens whose ``type`` claim does not match.
        Pass ``"access"`` on protected routes and ``"refresh"`` on the
        refresh endpoint.

    Returns
    -------
    dict
        The decoded payload — at minimum contains ``sub``, ``iat``, ``exp``,
        ``jti``, and ``type``. Never returns ``None``.

    Raises
    ------
    InvalidTokenError
        If the token is missing, malformed, signed with a different key,
        expired, or of the wrong ``type``. Map this to HTTP 401 — do NOT
        forward the underlying message to the client.

    Security
    --------
    - Signature + ``exp`` validation are handled by ``jose.jwt.decode``.
    - We re-check ``type`` because a stolen access token must not be usable
      to mint new refresh tokens (and vice versa).
    - On any failure, return the SAME 401 response — leaking which check
      failed gives attackers a side-channel.
    """
    cfg = _jwt_config()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            cfg["secret"],
            algorithms=[cfg["algorithm"]],
        )
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise InvalidTokenError(
            f"token type mismatch (expected {expected_type!r})"
        )

    return payload
