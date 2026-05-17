"""Pydantic schemas for Hils Marketing.

Re-exports the most commonly imported schemas so route handlers can write:

    from models import (
        ForgotPasswordRequest, LoginRequest, MessageResponse,
        RegisterRequest, ResetPasswordRequest, Token, UserResponse,
    )
"""

from models.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
)
from models.property import (
    PropertyCreate,
    PropertyResponse,
    PropertyStatus,
    PropertyType,
    PropertyUpdate,
    Purpose,
)
from models.user import Role, Token, UserResponse

__all__ = [
    "ForgotPasswordRequest",
    "LoginRequest",
    "MessageResponse",
    "PropertyCreate",
    "PropertyResponse",
    "PropertyStatus",
    "PropertyType",
    "PropertyUpdate",
    "Purpose",
    "RegisterRequest",
    "ResetPasswordRequest",
    "Role",
    "Token",
    "UserResponse",
]
