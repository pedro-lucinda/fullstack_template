import pytest
from httpx import AsyncClient

from app.core.db import get_db
from app.core.redis import get_redis
from app.main import app


@pytest.mark.asyncio
async def test_health_live_is_always_ok(client: AsyncClient):
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ready_ok_when_dependencies_up(client: AsyncClient):
    response = await client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"] == {"postgres": "ok", "redis": "ok"}


@pytest.mark.asyncio
async def test_health_ready_reports_503_when_redis_down(client: AsyncClient):
    class _BrokenRedis:
        async def ping(self):
            raise ConnectionError("redis unreachable")

    app.dependency_overrides[get_redis] = _BrokenRedis

    response = await client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["checks"]["postgres"] == "ok"
    assert "error" in body["checks"]["redis"]


@pytest.mark.asyncio
async def test_health_ready_reports_503_when_db_down(client: AsyncClient):
    class _BrokenSession:
        async def execute(self, *args, **kwargs):
            raise ConnectionError("db unreachable")

    async def _override_get_db():
        yield _BrokenSession()

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert "error" in body["checks"]["postgres"]
