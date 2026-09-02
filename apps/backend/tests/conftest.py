import os
from collections.abc import AsyncGenerator

# Rate limiting is Redis-backed and shared across requests within its TTL
# window; tests fire many requests in quick succession against the same key
# (remote address), so it must be disabled here — set *before* importing
# `app.main` (and anything it imports), since `app.core.rate_limit` builds
# its `Limiter` once at import time from `get_settings()`.
os.environ["RATE_LIMIT_ENABLED"] = "false"

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import CurrentUser, get_current_user
from app.core.db import Base, get_db
from app.core.redis import get_redis
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


def _override_current_user(sub: str) -> CurrentUser:
    def _inner() -> CurrentUser:
        return CurrentUser(sub=sub)

    return _inner


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # A fresh fake Redis per test, so cache state (e.g. the todos list cache)
    # never leaks between tests.
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user("user-1")
    app.dependency_overrides[get_redis] = lambda: fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def other_user_override():
    """Helper to switch the authenticated identity mid-test (ownership isolation)."""

    def _apply() -> None:
        app.dependency_overrides[get_current_user] = _override_current_user("user-2")

    return _apply
