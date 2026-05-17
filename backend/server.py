"""
Hils Marketing — FastAPI entry point.

Approach:
    1. Load environment from `.env` via python-dotenv on import.
    2. Build the FastAPI app and wire CORS from env (see security.mdc rule).
    3. Manage the async MongoDB (Motor) client through the `lifespan` context:
       connect on startup, ping for health, close cleanly on shutdown.
    4. Expose `/` (service banner) and `/api/health` (DB-aware liveness probe).
    5. Feature routers (auth, listings, payments, …) get mounted further down
       as each module lands.

Run locally:
    cp .env.example .env                                    # then fill secrets
    uvicorn server:app --reload --port 8000

Verify:
    curl http://localhost:8000/                             # service banner
    curl http://localhost:8000/api/health                   # {"status":"ok","db":"up"}
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# ----------------------------------------------------------------------------
# Environment + logging
# ----------------------------------------------------------------------------
# Load `.env` if present; missing file is fine (env vars may come from the host).
load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
log = logging.getLogger("hils.server")


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _cors_origins() -> list[str]:
    """Parse the comma-separated CORS_ORIGINS env var.

    Defaults to the local Vite dev server. In production this MUST be set
    explicitly to the real frontend URL — never `*` (see DOCS/security.md).
    """
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


# ----------------------------------------------------------------------------
# Lifespan — manages the Motor client + DB handle for the app's lifetime
# ----------------------------------------------------------------------------
async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create the indexes the app relies on (idempotent).

    Auth collections
    ~~~~~~~~~~~~~~~~
    - ``users.email``                       unique — prevents duplicate accounts
    - ``login_attempts.updated_at``         TTL 1h — auto-clears stale lockouts
    - ``refresh_tokens.jti``                unique — logout / rotation lookup
    - ``refresh_tokens.expires_at``         TTL 0  — purges expired tokens
    - ``password_reset_tokens.token_hash``  unique — find-by-token
    - ``password_reset_tokens.expires_at``  TTL 0  — purges expired tokens

    Property catalogue
    ~~~~~~~~~~~~~~~~~~
    - ``properties.property_id``            unique — canonical public id
    - ``properties.city``                   B-tree — drives the most common filter
    - ``properties.purpose``                B-tree — narrow buy/rent split
    - ``properties.property_type``          B-tree — house / apartment / plot / commercial
    - ``properties.status``                 B-tree — filter active vs tombstoned
    - ``properties.location_geo``           2dsphere — $nearSphere radius queries
    - ``properties.{title,description,location}`` text — $text full-text search

    Text index notes
    ~~~~~~~~~~~~~~~~
    Mongo only allows ONE text index per collection. The fields below are
    weighted so the title dominates relevance (3x), description carries the
    bulk (2x), and the location/area name nudges results that mention a
    specific neighbourhood.
    """
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("updated_at", expireAfterSeconds=3600)
    await db.refresh_tokens.create_index("jti", unique=True)
    await db.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.password_reset_tokens.create_index("token_hash", unique=True)
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)

    await db.properties.create_index("property_id", unique=True)
    await db.properties.create_index("city")
    await db.properties.create_index("purpose")
    await db.properties.create_index("property_type")
    await db.properties.create_index("status")
    await db.properties.create_index([("location_geo", "2dsphere")])
    await db.properties.create_index(
        [("title", "text"), ("description", "text"), ("location", "text")],
        weights={"title": 3, "description": 2, "location": 1},
        name="properties_text_idx",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect Motor on startup, ping Mongo to fail fast, close on shutdown."""
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "hils_marketing")

    log.info("Connecting to MongoDB at %s (db=%s)", mongo_url, db_name)
    client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
    db: AsyncIOMotorDatabase = client[db_name]

    try:
        await client.admin.command("ping")
        log.info("MongoDB connection OK")
        try:
            await _ensure_indexes(db)
            log.info("MongoDB indexes ensured")
        except Exception as exc:  # noqa: BLE001 — index errors must not crash boot
            log.error("Failed to ensure indexes: %s", exc)
    except Exception as exc:
        # Don't crash startup — health check will report `db: "down"` and
        # operators can fix the URL without rebooting the container.
        log.error("MongoDB ping failed: %s", exc)

    # Expose on app state so routers can do `request.app.state.db`.
    app.state.mongo_client = client
    app.state.db = db

    yield

    log.info("Closing MongoDB connection")
    client.close()


# ----------------------------------------------------------------------------
# App
# ----------------------------------------------------------------------------
app = FastAPI(
    title="Hils Marketing API",
    version="0.1.0",
    description="Backend for the Hils Marketing premium real-estate platform (Pakistan).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,                 # required for httpOnly cookie JWTs
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
# Meta endpoints
# ----------------------------------------------------------------------------
@app.get("/", tags=["meta"])
async def root() -> dict[str, Any]:
    """Service banner — useful for a quick browser smoke test."""
    return {
        "service": "hils-marketing-api",
        "version": app.version,
        "status": "ok",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health", tags=["meta"])
async def health() -> dict[str, Any]:
    """Liveness + DB readiness probe.

    Returns 200 as long as the process is up. The `db` field reports whether
    MongoDB is reachable right now (`"up"` / `"down"`), so monitoring can alert
    on DB outages without flapping the whole service.
    """
    db_status = "down"
    try:
        await app.state.db.command("ping")
        db_status = "up"
    except Exception as exc:  # noqa: BLE001 — we explicitly want to swallow
        log.warning("Health ping to MongoDB failed: %s", exc)

    return {"status": "ok", "service": "hils-marketing-api", "db": db_status}


# ----------------------------------------------------------------------------
# Feature routers
# ----------------------------------------------------------------------------
from routes import admin_properties, auth, properties  # noqa: E402

app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(admin_properties.router)

# TODO(features): mount as each lands.
# from routes import payments, users
# app.include_router(users.router)
# app.include_router(payments.router)
