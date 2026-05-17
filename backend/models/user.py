"""
User-related Pydantic schemas.

Public surface
--------------
- :class:`UserResponse` — outgoing user shape (never exposes ``password_hash``)
- :class:`Token`        — outgoing JWT pair shape
- :data:`Role`          — Literal of allowed roles (matches shared/constants.js)

The inbound request shapes (``RegisterRequest``, ``LoginRequest`` etc.) live
in :mod:`models.auth` so this module stays focused on the user entity.

Design notes
------------
- Outgoing models set ``from_attributes=True`` so they can be built from
  Mongo documents (or any ORM-ish object) without intermediate dicts.
- Phone numbers are validated to a Pakistani-compatible E.164-ish shape
  when present; the field is optional during registration and is filled
  in later via ``PATCH /api/users/me``.
- ``password_hash`` lives ONLY on the internal storage layer and MUST NOT
  appear on any response model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------
Role = Literal["admin", "agent", "customer"]

# Accepts:
#   +923001234567        (E.164 — preferred)
#   923001234567         (intl without +)
#   03001234567          (PK local mobile)
PK_PHONE_PATTERN = r"^(?:\+?92|0)3\d{9}$"


# ---------------------------------------------------------------------------
# Outgoing payloads
# ---------------------------------------------------------------------------
class UserResponse(BaseModel):
    """Safe public projection of a user — never includes ``password_hash``.

    Used as ``response_model`` on every route that returns a user
    (``/auth/register``, ``/auth/me``, ``/users/me``, …).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Mongo ``_id`` as a hex string.")
    email: EmailStr = Field(description="Login email (stored lowercased).")
    name: str = Field(description="Display name.")
    role: Role = Field(default="customer", description="Authorization role.")
    phone: Optional[str] = Field(
        default=None,
        description="Pakistani mobile in E.164 (+92...) or local (03...) form.",
    )
    created_at: datetime = Field(description="UTC creation timestamp.")


class Token(BaseModel):
    """JWT pair returned by ``/auth/register`` and ``/auth/login``.

    Cookie strategy
    ---------------
    The API ALSO sets these as httpOnly cookies on the same response
    (see DOCS/auth.md §cookies). The body is returned so:
      1. Non-browser clients (curl, mobile) get an explicit token.
      2. Tests can assert against it without inspecting cookies.

    Fields
    ------
    access_token : str
        Short-lived (12 h default) JWT with ``type="access"``.
    refresh_token : str
        Long-lived (7 d default) JWT with ``type="refresh"``.
    token_type : str
        Always ``"bearer"``. Matches OAuth 2.0 convention.
    expires_in : int
        Seconds until ``access_token`` expires.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        description="Seconds until the access_token expires.",
        examples=[43200],
    )
