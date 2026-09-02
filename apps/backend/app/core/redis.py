"""Async Redis client used for cross-process caching (e.g. the Auth0 JWKS
cache in `app/core/auth.py`).

A single connection pool is built once per process and reused across
requests, mirroring the SQLAlchemy async engine pattern in `app/core/db.py`.
Redis (rather than an in-memory dict) is used so the cache is shared across
multiple uvicorn worker processes and survives individual worker restarts.
"""

from functools import lru_cache

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_redis() -> redis.Redis:
    """Build (and cache) the process-wide Redis client.

    FastAPI dependency (see `app/api/routes`) and also called directly by
    non-route code (e.g. `app/core/auth.py`). Cached with `lru_cache` so it's
    built once per process; tests override it via `monkeypatch.setattr` or
    `app.dependency_overrides`, the same pattern used for `get_agent`.
    """
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)
