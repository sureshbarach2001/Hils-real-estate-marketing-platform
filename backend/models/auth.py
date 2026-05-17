"""
Pydantic request / response models for the auth feature.

All inbound models set ``extra="forbid"`` so clients cannot smuggle in
fields like ``role`` or ``is_admin`` (privilege escalation defence).

Password rules
--------------
- min 8 chars (matches the spec's ``Test@123`` example). May tighten to
  10–12 chars once HIBP integration lands; tracked in DOCS/auth.md §future.
- max 256 chars — bcrypt's 72-byte hard limit is sidestepped by SHA-256
  pre-hashing in ``utils.auth._prehash``, so any length is safe.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.user import PK_PHONE_PATTERN

# 8 is the floor; 256 is a sanity cap. See module docstring for rationale.
_PWD_MIN = 8
_PWD_MAX = 256


class RegisterRequest(BaseModel):
    """Body for ``POST /api/auth/register``."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(examples=["customer@hils.pk"])
    password: str = Field(min_length=_PWD_MIN, max_length=_PWD_MAX, examples=["Test@123"])
    name: str = Field(
        min_length=2,
        max_length=120,
        description="Display name shown in the UI.",
        examples=["Ali Raza"],
    )
    phone: Optional[str] = Field(
        default=None,
        pattern=PK_PHONE_PATTERN,
        description="Pakistani mobile in E.164 (+92...) or local (03...) form.",
        examples=["+923001234567", "03001234567"],
    )


class LoginRequest(BaseModel):
    """Body for ``POST /api/auth/login``."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(examples=["customer@hils.pk"])
    password: str = Field(min_length=1, max_length=_PWD_MAX, examples=["Test@123"])


class ForgotPasswordRequest(BaseModel):
    """Body for ``POST /api/auth/forgot-password``."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(examples=["customer@hils.pk"])


class ResetPasswordRequest(BaseModel):
    """Body for ``POST /api/auth/reset-password``."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(
        min_length=10,
        max_length=256,
        description="Opaque token from the password-reset email.",
    )
    new_password: str = Field(
        min_length=_PWD_MIN,
        max_length=_PWD_MAX,
        description="The new plaintext password (will be bcrypt-hashed).",
    )


class MessageResponse(BaseModel):
    """Generic ``{ "message": "..." }`` body used by 200-success endpoints."""

    message: str
