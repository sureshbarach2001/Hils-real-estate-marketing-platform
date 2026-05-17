"""
Public property routes — read-only catalogue surface.

Endpoints
---------
- ``GET /api/properties``               list w/ filters + text + geo search
- ``GET /api/properties/{property_id}`` fetch a single active listing

Admin write surface lives in ``routes/admin_properties.py``.

Filtering contract
------------------
All filters are AND-ed together. ``status`` is always pinned to ``active``
here; admins fetch other states via the admin routes (out of scope for the
public catalogue).

Why geo lives on a derived field
--------------------------------
Mongo's ``2dsphere`` index needs a GeoJSON Point, not two scalars. Every
property document is stored with both the spec'd flat ``latitude`` /
``longitude`` (for client convenience) AND a derived ``location_geo`` Point
(for ``$nearSphere``). See ``DOCS/properties.md §geo`` for the full picture.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.property import PropertyResponse
from utils.db import get_db

log = logging.getLogger("hils.routes.properties")

router = APIRouter(prefix="/api/properties", tags=["properties"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# Fields the public API never wants on the wire. ``_id`` is Mongo-internal;
# ``location_geo`` is an index-only derivative of latitude/longitude.
_PUBLIC_PROJECTION_DROP = {"_id": 0, "location_geo": 0}


def _serialize(doc: dict) -> dict:
    """Best-effort map of a raw Mongo doc -> PropertyResponse-compatible dict.

    We rely on the projection above to have already dropped Mongo internals;
    this function just exists as a single place to add any future field
    renames or computed fields (e.g. a formatted price string).
    """
    return doc


# ---------------------------------------------------------------------------
# GET /api/properties
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[PropertyResponse],
    summary="List active properties with filters, text search, and geo radius.",
)
async def list_properties(
    db: AsyncIOMotorDatabase = Depends(get_db),
    city: Optional[str] = Query(default=None, description="Exact match, case-insensitive."),
    purpose: Optional[str] = Query(default=None, pattern="^(buy|rent)$"),
    property_type: Optional[str] = Query(
        default=None, pattern="^(house|apartment|plot|commercial)$"
    ),
    min_price: Optional[int] = Query(default=None, ge=0),
    max_price: Optional[int] = Query(default=None, ge=0),
    bedrooms: Optional[int] = Query(default=None, ge=0, le=50),
    featured: Optional[bool] = Query(default=None),
    q: Optional[str] = Query(default=None, min_length=1, max_length=120, description="Full-text search across title + description + location."),
    lat: Optional[float] = Query(default=None, ge=-90.0, le=90.0),
    lng: Optional[float] = Query(default=None, ge=-180.0, le=180.0),
    radius_km: float = Query(default=5.0, gt=0, le=200.0, description="Search radius — applied only when both lat and lng are supplied."),
    limit: int = Query(default=24, ge=1, le=100),
) -> list[dict]:
    """List active properties.

    Behaviour notes
    ---------------
    - All filters AND together. Missing filters are skipped.
    - ``q`` uses the ``$text`` index (title + description + location).
    - ``lat`` + ``lng`` together enable a ``$nearSphere`` radius filter
      (radius defaults to 5 km). Supplying only one is treated as "no geo".
    - Results sort by ``featured`` (gold-listings first) then ``created_at``
      desc — unless ``q`` is set, in which case Mongo's text score wins.
    - ``status`` is hard-pinned to ``active``; admins use ``/api/admin/properties``.
    """
    query: dict[str, Any] = {"status": "active"}

    if city:
        # case-insensitive exact match — anchored regex avoids accidental partials.
        query["city"] = {"$regex": f"^{_re_escape(city)}$", "$options": "i"}
    if purpose:
        query["purpose"] = purpose
    if property_type:
        query["property_type"] = property_type
    if bedrooms is not None:
        query["bedrooms"] = {"$gte": bedrooms}
    if featured is not None:
        query["featured"] = featured

    if min_price is not None or max_price is not None:
        price_range: dict[str, int] = {}
        if min_price is not None:
            price_range["$gte"] = min_price
        if max_price is not None:
            price_range["$lte"] = max_price
        query["price"] = price_range

    if q:
        query["$text"] = {"$search": q}

    if lat is not None and lng is not None:
        # 2dsphere $nearSphere requires GeoJSON + meters. radius_km defaults to 5.
        query["location_geo"] = {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": int(radius_km * 1000),
            }
        }

    projection: dict[str, Any] = dict(_PUBLIC_PROJECTION_DROP)
    sort_spec: list[tuple] | None
    if q:
        projection["score"] = {"$meta": "textScore"}
        sort_spec = [("score", {"$meta": "textScore"}), ("featured", -1), ("created_at", -1)]
    elif "location_geo" in query:
        # $nearSphere already returns nearest-first; explicit sort would conflict.
        sort_spec = None
    else:
        sort_spec = [("featured", -1), ("created_at", -1)]

    cursor = db.properties.find(query, projection)
    if sort_spec is not None:
        cursor = cursor.sort(sort_spec)
    cursor = cursor.limit(limit)

    docs = await cursor.to_list(length=limit)
    return [_serialize(d) for d in docs]


# ---------------------------------------------------------------------------
# GET /api/properties/{property_id}
# ---------------------------------------------------------------------------
@router.get(
    "/{property_id}",
    response_model=PropertyResponse,
    responses={404: {"description": "No active property with that id."}},
    summary="Fetch a single active property by its UUID.",
)
async def get_property(
    property_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Return a single active property.

    Inactive / soft-deleted / sold / rented listings return 404 on this
    public route — admins read them via ``/api/admin/properties/{id}``.
    """
    doc = await db.properties.find_one(
        {"property_id": property_id, "status": "active"},
        _PUBLIC_PROJECTION_DROP,
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return _serialize(doc)


# ---------------------------------------------------------------------------
# Tiny utility — avoid pulling in `re` everywhere
# ---------------------------------------------------------------------------
def _re_escape(value: str) -> str:
    import re

    return re.escape(value)
