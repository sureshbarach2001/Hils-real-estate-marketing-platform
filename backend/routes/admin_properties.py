"""
Admin property write surface — create / update / soft-delete.

All routes require an authenticated admin (``utils.security.require_admin``).
The public catalogue lives in :mod:`routes.properties`.

Storage invariants we maintain
------------------------------
1. ``property_id`` is a string UUID4 generated server-side on create. Clients
   never set it. Lookups everywhere use this field, never Mongo's ``_id``.
2. ``location_geo`` is a GeoJSON Point built from ``latitude`` + ``longitude``
   on every write. The ``2dsphere`` index lives there; it must stay in sync
   with the flat fields or ``$nearSphere`` queries will lie.
3. Delete = ``status="inactive"`` + ``updated_at = now``. We never ``delete_one``.
   Listings are part of the business audit trail; we tombstone, never erase.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.property import PropertyCreate, PropertyResponse, PropertyUpdate
from utils.db import get_db
from utils.security import require_admin

log = logging.getLogger("hils.routes.admin_properties")

router = APIRouter(
    prefix="/api/admin/properties",
    tags=["admin", "properties"],
    dependencies=[Depends(require_admin)],
)

_PROJECTION_DROP = {"_id": 0, "location_geo": 0}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _geo_point(lat: float, lng: float) -> dict:
    """Build the GeoJSON Point that backs the 2dsphere index.

    Mongo expects ``coordinates: [longitude, latitude]`` — note the order.
    Getting this backwards is the single most common 2dsphere bug.
    """
    return {"type": "Point", "coordinates": [lng, lat]}


# ---------------------------------------------------------------------------
# POST /api/admin/properties
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new property (admin).",
)
async def create_property(
    body: PropertyCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Insert a property. ``property_id`` is generated; the client never sets it."""
    now = _utcnow()
    doc: dict[str, Any] = body.model_dump()
    doc["property_id"] = str(uuid4())
    doc["location_geo"] = _geo_point(body.latitude, body.longitude)
    doc["created_at"] = now
    doc["updated_at"] = now

    await db.properties.insert_one(doc)

    saved = await db.properties.find_one({"property_id": doc["property_id"]}, _PROJECTION_DROP)
    if not saved:  # paranoia — index race, lost write, ...
        raise HTTPException(status_code=500, detail="Failed to persist property")
    return saved


# ---------------------------------------------------------------------------
# PUT /api/admin/properties/{property_id}
# ---------------------------------------------------------------------------
@router.put(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Update an existing property (admin).",
    responses={
        400: {"description": "Empty body — supply at least one field to update."},
        404: {"description": "No property with that id."},
    },
)
async def update_property(
    property_id: str,
    body: PropertyUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Partial update — only supplied keys are written.

    If ``latitude`` OR ``longitude`` is changed we rebuild ``location_geo``
    from the resulting pair (reading the current values for whichever side
    wasn't supplied). This keeps the 2dsphere index honest.
    """
    update_fields = body.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required.",
        )

    existing = await db.properties.find_one({"property_id": property_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if "latitude" in update_fields or "longitude" in update_fields:
        lat = update_fields.get("latitude", existing.get("latitude"))
        lng = update_fields.get("longitude", existing.get("longitude"))
        update_fields["location_geo"] = _geo_point(lat, lng)

    update_fields["updated_at"] = _utcnow()

    await db.properties.update_one({"property_id": property_id}, {"$set": update_fields})

    saved = await db.properties.find_one({"property_id": property_id}, _PROJECTION_DROP)
    if not saved:  # extremely unlikely after a successful $set on a found doc
        raise HTTPException(status_code=500, detail="Failed to read back property")
    return saved


# ---------------------------------------------------------------------------
# DELETE /api/admin/properties/{property_id}
# ---------------------------------------------------------------------------
@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a property (admin) — flips status to 'inactive'.",
    responses={404: {"description": "No property with that id."}},
)
async def delete_property(
    property_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    """Soft delete.

    We never ``delete_one`` listings — they're part of the business audit
    trail (price history, agent attribution, settled deals). Flipping the
    status to ``inactive`` removes the listing from the public catalogue
    while preserving the record for analytics + dispute handling.
    """
    result = await db.properties.update_one(
        {"property_id": property_id},
        {"$set": {"status": "inactive", "updated_at": _utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
