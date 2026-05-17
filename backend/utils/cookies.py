"""
HTTP-cookie helpers for the auth flow.

Approach
--------
- Two cookies: ``access_token`` (scope ``/``) and ``refresh_token`` (scope
  ``/api/auth`` — never sent to other routes, so it can't leak via XSS on
  unrelated endpoints).
- All flags are env-driven so dev (HTTP localhost) and prod (cross-origin
  HTTPS) configure differently without code changes.

Env vars
--------
- ``COOKIE_SAMESITE``  ``"lax"`` (default) / ``"strict"`` / ``"none"``
    Use ``"none"`` only when the frontend and API live on different
    registrable domains (e.g. ``hils.pk`` + ``api.somewhere.dev``).
- ``COOKIE_SECURE``    ``"true"`` / ``"false"`` — defaults to ``true`` in
    production, ``false`` in development. Forced to ``true`` if SameSite=none
    (browsers reject it otherwise).
- ``COOKIE_DOMAIN``    optional — set to the parent domain (``.hils.pk``)
    to share cookies across subdomains.

See DOCS/auth.md §cookies for the threat-model reasoning.
"""

from __future__ import annotations

import os
from typing import Literal

from fastapi import Response

# Cookie names — referenced by both auth.py (set) and security.py (read).
ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

# Path scopes: refresh cookie is locked to the auth router, access cookie
# travels with every API call.
ACCESS_COOKIE_PATH = "/"
REFRESH_COOKIE_PATH = "/api/auth"


def _samesite() -> Literal["lax", "strict", "none"]:
    """Read and validate the SameSite policy from env (default ``lax``)."""
    raw = os.getenv("COOKIE_SAMESITE", "lax").lower()
    if raw not in ("lax", "strict", "none"):
        return "lax"
    return raw  # type: ignore[return-value]


def _secure() -> bool:
    """Read the Secure flag from env. Forced True when SameSite=none."""
    is_prod = os.getenv("APP_ENV", "development") == "production"
    default = "true" if is_prod else "false"
    explicit = os.getenv("COOKIE_SECURE", default).lower() in ("1", "true", "yes")
    return explicit or _samesite() == "none"


def _domain() -> str | None:
    """Optional cookie domain (e.g. ``.hils.pk`` for subdomain sharing)."""
    value = os.getenv("COOKIE_DOMAIN")
    return value if value else None


def set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    access_seconds: int,
    refresh_seconds: int,
) -> None:
    """Attach access + refresh cookies to ``response`` with safe flags."""
    common = {
        "httponly": True,
        "secure": _secure(),
        "samesite": _samesite(),
        "domain": _domain(),
    }
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=access_seconds,
        path=ACCESS_COOKIE_PATH,
        **common,
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=refresh_seconds,
        path=REFRESH_COOKIE_PATH,
        **common,
    )


def clear_auth_cookies(response: Response) -> None:
    """Remove access + refresh cookies (used by ``/auth/logout``).

    Uses both ``delete_cookie`` and an explicit ``max_age=0`` set so clients
    (including ``curl -c cookies.txt``) reliably drop the jar entries — some
    stacks ignore ``delete_cookie`` when path/samesite don't match exactly.
    """
    common = {
        "httponly": True,
        "secure": _secure(),
        "samesite": _samesite(),
        "domain": _domain(),
    }
    for key, cookie_path in (
        (ACCESS_COOKIE, ACCESS_COOKIE_PATH),
        (REFRESH_COOKIE, REFRESH_COOKIE_PATH),
    ):
        response.delete_cookie(key=key, path=cookie_path, **common)
        # Belt-and-suspenders: empty value + zero max-age overwrites the jar entry.
        response.set_cookie(
            key=key,
            value="",
            max_age=0,
            path=cookie_path,
            **common,
        )
