"""Rate limiting (`slowapi`, backed by the same Redis instance used
elsewhere — see `app/core/redis.py` — so limits are shared across every
uvicorn worker process, not tracked per-process).

Keyed by remote IP by default (`get_remote_address`); good enough for a
public/unauthenticated-adjacent endpoint like the example agent chat. If a
route needs per-authenticated-user limits instead, write a small custom
`key_func` that reads the `sub` claim (without needing the full
`get_current_user` dependency, since `slowapi`'s `key_func` only receives the
raw `Request`) and pass it via `Limiter(key_func=...)` — not needed yet, so
kept simple for now.

Disabled entirely via `settings.rate_limit_enabled=False` (the test suite
does this — see `tests/conftest.py` — so test runs never share rate-limit
state between test functions or need a real Redis instance for `slowapi`'s
own storage backend).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    enabled=settings.rate_limit_enabled,
    default_limits=[settings.rate_limit_default],
)
