"""Unit tests for the global exception handlers in `app.core.errors`.

These call the handler functions directly rather than trying to trigger a
real 429 through the live Redis-backed limiter (which isn't reachable in the
test environment, and rate limiting is disabled for the rest of the test
suite via `RATE_LIMIT_ENABLED=false` — see `conftest.py`).
"""

from unittest.mock import MagicMock

import pytest
from starlette.requests import Request

from app.core.errors import rate_limit_exceeded_handler


def _make_request() -> Request:
    scope = {
        "type": "http",
        "headers": [],
        "method": "POST",
        "path": "/api/v1/agent/chat",
    }
    request = Request(scope)
    request.state.request_id = "test-request-id"
    return request


@pytest.mark.asyncio
async def test_rate_limit_exceeded_handler_returns_429_with_shared_error_shape():
    fake_exc = MagicMock(detail="10 per 1 minute")

    response = await rate_limit_exceeded_handler(_make_request(), fake_exc)

    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    body = response.body.decode()
    assert "rate_limited" in body
    assert "test-request-id" in body
    assert "10 per 1 minute" in body
