"""
Idempotent property seeder.

Reads ``../memory/seed-properties.json`` (resolved relative to the repo root),
validates each record against :class:`models.property.PropertyCreate`, derives
the ``location_geo`` GeoJSON Point, and upserts by ``property_id``.

Approach
--------
1. Validate the file's ``properties`` array with Pydantic — surfaces typos
   (wrong enum, bad phone format) before any DB write.
2. For each record, assemble the storage document (flat fields + derived
   ``location_geo`` + timestamps).
3. ``replace_one(filter, doc, upsert=True)`` keyed on ``property_id`` so
   re-running the script overwrites old data, preserves the ``_id``, and
   never inserts duplicates.

Usage
-----
    cd backend
    python -m scripts.seed_properties                       # idempotent upsert
    python -m scripts.seed_properties --drop                # wipe first

Expected output
---------------
    [seed] connected to mongodb://localhost:27017 / hils_marketing
    [seed] 12 properties parsed
    [seed] upserted 12 (modified 0, inserted 12)
    [seed] done in 0.42s

Verify
------
    curl 'http://localhost:8000/api/properties?city=Karachi&purpose=buy&max_price=50000000' | jq '.[].title'
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Make the seeder runnable both as a module (`python -m scripts.seed_properties`)
# and as a plain file (`python scripts/seed_properties.py`) by ensuring the
# backend root is on sys.path before importing local packages.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from models.property import PropertyCreate  # noqa: E402

load_dotenv(_BACKEND_ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="[seed] %(message)s")
log = logging.getLogger("hils.seed.properties")

SEED_PATH = _BACKEND_ROOT.parent / "memory" / "seed-properties.json"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_doc(raw: dict) -> dict:
    """Validate one seed record + assemble the Mongo document."""
    # Strip the optional seed-only `property_id` before validation, then put
    # it back on the storage doc — PropertyCreate doesn't know about that field.
    requested_id = raw.pop("property_id", None)

    parsed = PropertyCreate.model_validate(raw)
    doc = parsed.model_dump()

    doc["property_id"] = requested_id or str(uuid4())
    doc["location_geo"] = {
        "type": "Point",
        "coordinates": [parsed.longitude, parsed.latitude],  # GeoJSON: [lng, lat]
    }
    now = _utcnow()
    doc["created_at"] = now
    doc["updated_at"] = now
    return doc


async def main(drop: bool) -> None:
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "hils_marketing")

    log.info("connected to %s / %s", mongo_url, db_name)
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
    db = client[db_name]

    try:
        await client.admin.command("ping")
    except Exception as exc:
        log.error("could not reach MongoDB: %s", exc)
        sys.exit(1)

    if drop:
        deleted = (await db.properties.delete_many({})).deleted_count
        log.info("dropped %d existing properties", deleted)

    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    records = raw.get("properties") or []
    log.info("%d properties parsed", len(records))

    started = time.perf_counter()
    upserts = inserts = modifies = 0
    for r in records:
        doc = _build_doc(r)
        result = await db.properties.replace_one(
            {"property_id": doc["property_id"]},
            doc,
            upsert=True,
        )
        upserts += 1
        if result.upserted_id is not None:
            inserts += 1
        else:
            modifies += int(result.modified_count)

    elapsed = time.perf_counter() - started
    log.info("upserted %d (modified %d, inserted %d)", upserts, modifies, inserts)
    log.info("done in %.2fs", elapsed)

    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the properties collection.")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Delete all existing properties before inserting (destructive).",
    )
    args = parser.parse_args()
    asyncio.run(main(drop=args.drop))
