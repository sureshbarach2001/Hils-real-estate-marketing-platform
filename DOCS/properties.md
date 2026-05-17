# Properties

The property catalogue is the core read-heavy surface of Hils Marketing.
This document covers the storage shape, geospatial search, the public + admin
endpoints, and the seed workflow.

> **Modules**: `backend/routes/properties.py`, `backend/routes/admin_properties.py`
> **Models**: `backend/models/property.py`
> **Seed**:  `backend/scripts/seed_properties.py` + `memory/seed-properties.json`

---

## 1. Diagram — read path

```mermaid
flowchart LR
    User[Browser] -->|GET /api/properties?city=...| FE[React]
    FE -->|axios + cookies| API[FastAPI<br/>/routes/properties.py]
    API -->|filter dict| DB[(MongoDB<br/>properties)]
    DB -->|2dsphere $nearSphere| DB
    DB -->|text $text| DB
    DB -->|cursor| API
    API -->|PropertyResponse[]| FE
    FE -->|map + cards| User
```

---

## 2. Document shape (storage vs wire)

The wire model — what clients see — exposes `latitude` and `longitude` as
flat floats. Internally Mongo also stores a derived **`location_geo`**
GeoJSON Point so the `2dsphere` index has something to chew on:

```json
{
  "_id": "ObjectId(...)",                                    // Mongo internal
  "property_id": "11111111-1111-4111-8111-111111111101",     // public UUID
  "title": "Modern Villa, DHA Phase 6 Karachi",
  "city": "Karachi",
  "location": "DHA Phase 6",
  "latitude": 24.8009,                                       // wire
  "longitude": 67.0739,                                      // wire
  "location_geo": {                                          // derived, index-only
    "type": "Point",
    "coordinates": [67.0739, 24.8009]                        // GeoJSON: [lng, lat]
  },
  "price": 48000000,
  "status": "active",
  "created_at": "2026-05-17T...",
  "updated_at": "2026-05-17T..."
}
```

**Invariant**: write paths in `admin_properties.py` always rebuild
`location_geo` from the supplied `latitude` / `longitude`. The 2dsphere
index never gets out of sync with the public fields. The `_id` and
`location_geo` keys are dropped from every public projection.

> **GeoJSON gotcha**: coordinates are `[longitude, latitude]`, not
> `[latitude, longitude]`. This is the single most common 2dsphere bug —
> see `_geo_point()` in `routes/admin_properties.py`.

---

## 3. Indexes

Created once on startup by `server.py::_ensure_indexes()`:

| Field | Type | Purpose |
|---|---|---|
| `property_id` | unique B-tree | public ID lookup; rejects duplicates |
| `city` | B-tree | most common filter |
| `purpose` | B-tree | buy / rent split |
| `property_type` | B-tree | house / apartment / plot / commercial |
| `status` | B-tree | filter `active` vs tombstoned |
| `location_geo` | **2dsphere** | `$nearSphere` radius queries |
| `(title, description, location)` | **text** | `$text` full-text search, weights 3 / 2 / 1 |

Mongo allows only **one text index per collection**. The single index
covers the three searchable fields with weighted relevance — see the
`weights={...}` arg in `_ensure_indexes()`.

---

## 4. How `2dsphere` enables "within 5 km" queries

`$nearSphere` takes a centre point and a `$maxDistance` in **metres**, and
returns docs ordered by ascending distance:

```python
query["location_geo"] = {
    "$nearSphere": {
        "$geometry": {"type": "Point", "coordinates": [lng, lat]},
        "$maxDistance": int(radius_km * 1000),
    }
}
```

Behind the scenes Mongo's 2dsphere index uses a spherical model of Earth,
so the distance correctly accounts for the curvature (PostGIS does the
same thing — the math is identical for short ranges). The index is
B-tree-cheap to traverse, so a "within 5 km" query stays sub-millisecond
even at 100k+ listings.

A few practical notes:

- **`$nearSphere` is already sorted** by distance ascending — adding an
  explicit `.sort()` would conflict. The route layer skips its default
  sort when a geo query is in play.
- **Pair with `$text`**: legal in modern Mongo but text-score sort wins
  unless you `$meta` it explicitly.
- **`$maxDistance` is in metres** (not km, not miles). The route accepts
  `radius_km` and multiplies — clearer for the client.

---

## 5. Endpoint catalogue

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/api/properties` | — | Filters: `city`, `purpose`, `property_type`, `min_price`, `max_price`, `bedrooms`, `featured`, `q`, `lat`+`lng`+`radius_km`, `limit` |
| GET | `/api/properties/{property_id}` | — | 404 if not `active` |
| POST | `/api/admin/properties` | admin | Returns 201 + `PropertyResponse` |
| PUT | `/api/admin/properties/{property_id}` | admin | Partial update; empty body → 400 |
| DELETE | `/api/admin/properties/{property_id}` | admin | **Soft delete** — flips `status="inactive"`, returns 204 |

### Why soft delete?

We never `delete_one()` a listing. Three reasons:

1. **Business audit trail** — agent attribution, price history, and
   settled-deal commissions must be reconstructible months after a
   listing leaves the public catalogue.
2. **Dispute handling** — buyers, sellers, and regulators occasionally
   need the exact published version of a listing at a given moment.
3. **Search graph integrity** — external links (Google index, shared
   WhatsApp messages) shouldn't 500 because someone clicked "delete".
   `status="inactive"` returns a clean 404 while the row survives.

If a listing genuinely needs to be erased (e.g. for legal compliance),
that goes through a separate `purge` workflow with explicit human approval
— not the standard CRUD path.

---

## 6. Price formatting (PKR)

**Storage**: always integer PKR (whole rupees). No decimals. No symbol.
A property at 4.8 crore is stored as `48000000`, not `"Rs 4.8 Cr"`.

**Display**: always via `shared/utils.js::formatPKR()` which wraps
`Intl.NumberFormat('en-PK', {...})`. Locale `en-PK` produces the
Pakistani thousand-grouping conventions:

```js
import { formatPKR } from '@shared/utils.js';

formatPKR(48000000);                       // "Rs 4,80,00,000"
formatPKR(48000000, { withSymbol: false }); // "4,80,00,000"
```

Why not store the formatted string? Three reasons:

- Filters / sorts need a number, not a locale-encoded string.
- Internationalisation later (USD-toggling for diaspora buyers) needs
  the raw number.
- A locale change in the formatter must not require a data migration.

---

## 7. Seed workflow

Re-runnable, no flag needed:

```powershell
cd backend
python -m scripts.seed_properties
```

Wipe + re-seed (destructive):

```powershell
python -m scripts.seed_properties --drop
```

The seed file (`memory/seed-properties.json`) carries fixed
`property_id` UUIDs so every run upserts the same 12 records — useful
for stable test data + screenshot reproducibility. Add new entries
without an ID and the script will generate one on first run.

### Expected output

```
[seed] connected to mongodb://localhost:27017 / hils_marketing
[seed] 12 properties parsed
[seed] upserted 12 (modified 0, inserted 12)
[seed] done in 0.42s
```

### Verify

```powershell
curl 'http://localhost:8000/api/properties?city=Karachi&purpose=buy&max_price=50000000'
```

Should return at least two records (DHA Phase 6 villa at 48M, DHA City
plot at 18M, Bahria Town house at 32M).

---

## 8. Troubleshooting

| Symptom | Most-likely cause | Fix |
|---|---|---|
| `$nearSphere requires a 2dsphere index` | Server started without the index | Restart uvicorn — `_ensure_indexes()` runs on startup |
| Geo query returns nothing | `coordinates` order swapped on a write | Update via PUT; route auto-rebuilds `location_geo` |
| `$text` returns no hits | Text index missing (only one per collection) | Check `db.properties.getIndexes()` for `properties_text_idx` |
| 401 on `POST /api/admin/properties` | Not logged in | Sign in with an admin account first |
| 403 on the same | Logged in but role is not `admin` | Promote: `db.users.updateOne({email:'...'}, {$set:{role:'admin'}})` |

---

## 9. Future work

- **`featured`-only carousel** — a tiny dedicated endpoint that bypasses
  filters, returning the top N featured listings sorted by `created_at`.
- **Cursor pagination** — current `limit` is offsetless; for large
  catalogues we'll add an opaque `after` cursor keyed on `(featured, _id)`.
- **Photo CDN + AVIF** — Unsplash URLs are fine for seed/demo. Real listings
  should upload to S3/Cloudflare R2 and serve via the image CDN with
  per-viewport `srcset`.
- **Polygon search** — `$geoWithin` on user-drawn polygons (e.g. "show
  me everything inside DHA Phase 6 outline"). The 2dsphere index already
  supports it; just needs a route + UI.
- **Status workflow** — admin endpoint to flip between
  `active` / `sold` / `rented` without hitting `delete`.
