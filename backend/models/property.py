"""
Property-related Pydantic schemas.

Public surface
--------------
- :class:`PropertyCreate`   — admin POST body
- :class:`PropertyUpdate`   — admin PUT body (every field optional)
- :class:`PropertyResponse` — outgoing shape served by every property route

Storage shape (what actually lives in Mongo) vs. wire shape (these models)
-------------------------------------------------------------------------
- The wire model exposes ``latitude`` + ``longitude`` as flat fields because
  that's the natural client contract for a map widget.
- Mongo additionally stores a derived ``location_geo`` GeoJSON Point — the
  ``2dsphere`` index lives on that field, so ``$nearSphere`` works:
      { "type": "Point", "coordinates": [<lng>, <lat>] }
  The route layer is responsible for keeping these two representations in
  sync on write (see ``routes/admin_properties.py``). Reads never touch
  ``location_geo`` directly.

City list
---------
``city`` is intentionally a free-form string here (not an enum) so the API
can accept new launch cities without a code change. The frontend should
populate dropdowns from :data:`shared/constants.js::CITIES` — that's the
SoT for the *current* market.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums — kept as Literal types so OpenAPI surfaces them as enums for free
# ---------------------------------------------------------------------------
Purpose = Literal["buy", "rent"]
PropertyType = Literal["house", "apartment", "plot", "commercial"]
PropertyStatus = Literal["active", "inactive", "sold", "rented"]


# Pakistani mobile — duplicated rather than imported from models.user to keep
# this module standalone (so it can be reused by tooling without dragging in
# the user schema). Kept in sync with ``models.user.PK_PHONE_PATTERN``.
PK_PHONE_PATTERN = r"^(?:\+?92|0)3\d{9}$"


# ---------------------------------------------------------------------------
# Inbound — admin create / update
# ---------------------------------------------------------------------------
class _PropertyBase(BaseModel):
    """Fields shared by Create + Update. Update marks them all optional."""

    title: str = Field(min_length=4, max_length=200, examples=["Luxury Villa, DHA Phase 6"])
    description: str = Field(min_length=20, max_length=4000)
    purpose: Purpose = Field(examples=["buy"])
    property_type: PropertyType = Field(examples=["house"])
    city: str = Field(min_length=2, max_length=60, examples=["Karachi"])
    location: str = Field(
        min_length=2,
        max_length=120,
        description="Human-readable neighbourhood / area, e.g. 'DHA Phase 6'.",
    )
    price: int = Field(ge=0, le=10_000_000_000, description="Asking price in PKR (whole rupees).")
    area: int = Field(ge=0, le=1_000_000, description="Built / plot area in square feet.")
    bedrooms: int = Field(ge=0, le=50)
    bathrooms: int = Field(ge=0, le=50)
    images: List[str] = Field(default_factory=list, max_length=20)
    amenities: List[str] = Field(default_factory=list, max_length=40)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    featured: bool = Field(default=False)
    status: PropertyStatus = Field(default="active")
    agent_name: str = Field(min_length=2, max_length=120)
    agent_phone: str = Field(
        pattern=PK_PHONE_PATTERN,
        description="Pakistani mobile in E.164 (+92...) or local (03...) form.",
        examples=["+923001234567"],
    )
    deposit_usd: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Optional USD deposit hint, surfaced to international buyers on "
            "high-value listings. Stored as float; informational only."
        ),
    )


class PropertyCreate(_PropertyBase):
    """Body for ``POST /api/admin/properties``."""

    model_config = ConfigDict(extra="forbid")


class PropertyUpdate(BaseModel):
    """Body for ``PUT /api/admin/properties/{property_id}``.

    Every field is optional — only supplied keys are written. Empty body is
    rejected by the route layer (would be a no-op).
    """

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=4, max_length=200)
    description: Optional[str] = Field(default=None, min_length=20, max_length=4000)
    purpose: Optional[Purpose] = None
    property_type: Optional[PropertyType] = None
    city: Optional[str] = Field(default=None, min_length=2, max_length=60)
    location: Optional[str] = Field(default=None, min_length=2, max_length=120)
    price: Optional[int] = Field(default=None, ge=0, le=10_000_000_000)
    area: Optional[int] = Field(default=None, ge=0, le=1_000_000)
    bedrooms: Optional[int] = Field(default=None, ge=0, le=50)
    bathrooms: Optional[int] = Field(default=None, ge=0, le=50)
    images: Optional[List[str]] = Field(default=None, max_length=20)
    amenities: Optional[List[str]] = Field(default=None, max_length=40)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    featured: Optional[bool] = None
    status: Optional[PropertyStatus] = None
    agent_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    agent_phone: Optional[str] = Field(default=None, pattern=PK_PHONE_PATTERN)
    deposit_usd: Optional[float] = Field(default=None, ge=0)


# ---------------------------------------------------------------------------
# Outgoing
# ---------------------------------------------------------------------------
class PropertyResponse(_PropertyBase):
    """Public projection of a property.

    Differs from :class:`PropertyCreate` only in that it carries the
    server-assigned ``property_id`` and ``created_at`` timestamp. Field
    inheritance keeps these two shapes in lock-step.
    """

    model_config = ConfigDict(from_attributes=True)

    property_id: str = Field(description="Stable public UUID; use this everywhere.")
    created_at: datetime
