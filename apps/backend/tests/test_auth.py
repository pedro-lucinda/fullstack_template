import fakeredis.aioredis
import pytest
from jose import jwt

from app.core import auth as auth_module


@pytest.fixture
def fake_redis(monkeypatch):
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(auth_module, "get_redis", lambda: client)
    return client


@pytest.mark.asyncio
async def test_get_signing_key_caches_jwks_in_redis(fake_redis, monkeypatch):
    jwks = {"keys": [{"kid": "abc", "kty": "RSA", "n": "...", "e": "AQAB"}]}
    fetch_calls: list[int] = []

    async def fake_fetch_jwks() -> dict:
        fetch_calls.append(1)
        return jwks

    monkeypatch.setattr(auth_module, "_fetch_jwks", fake_fetch_jwks)

    token = jwt.encode({"sub": "user-1"}, "secret", algorithm="HS256", headers={"kid": "abc"})

    first = await auth_module._get_signing_key(token)
    second = await auth_module._get_signing_key(token)

    assert first == second == jwks["keys"][0]
    # The second call should be served from the Redis cache, not the network.
    assert len(fetch_calls) == 1
    assert await fake_redis.get(auth_module.JWKS_CACHE_KEY) is not None


@pytest.mark.asyncio
async def test_get_signing_key_refetches_on_unknown_kid(fake_redis, monkeypatch):
    """Simulates an Auth0 key rotation: the cached JWKS doesn't contain the
    `kid` referenced by a newly-issued token, so it must be refreshed once."""
    old_jwks = {"keys": [{"kid": "old", "kty": "RSA"}]}
    new_jwks = {"keys": [{"kid": "new", "kty": "RSA"}]}
    fetch_calls: list[dict] = []

    async def fake_fetch_jwks() -> dict:
        result = old_jwks if not fetch_calls else new_jwks
        fetch_calls.append(result)
        return result

    monkeypatch.setattr(auth_module, "_fetch_jwks", fake_fetch_jwks)

    token = jwt.encode({"sub": "user-1"}, "secret", algorithm="HS256", headers={"kid": "new"})

    key = await auth_module._get_signing_key(token)

    assert key == new_jwks["keys"][0]
    assert len(fetch_calls) == 2
