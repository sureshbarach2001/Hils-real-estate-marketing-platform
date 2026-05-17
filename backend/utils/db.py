"""
Database accessors — keeps Motor coupling out of route handlers.

Approach:
  The Motor client is constructed in ``server.py``'s lifespan and stashed on
  ``app.state.db``. Routes use the :func:`get_db` dependency to receive it,
  which makes tests trivial — just override the dependency.

Usage in a route::

    from fastapi import APIRouter, Depends
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from utils.db import get_db

    router = APIRouter(prefix="/api/example")

    @router.get("")
    async def list_things(db: AsyncIOMotorDatabase = Depends(get_db)):
        return await db.things.find().to_list(None)
"""

from __future__ import annotations

from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorDatabase


def get_db(request: Request) -> AsyncIOMotorDatabase:
    """Return the per-app MongoDB handle set up in the lifespan."""
    return request.app.state.db
