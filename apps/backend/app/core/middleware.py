"""Request-ID / access-log middleware.

Every request gets a correlation ID (reused from the incoming `X-Request-ID`
header if the caller already set one, e.g. from an upstream gateway) that is:
  - echoed back on the response as `X-Request-ID`, so a client can report it
    back when filing a bug,
  - bound into structlog's contextvars for the lifetime of the request, so
    every log line emitted while handling it (including from deep inside
    `service.py` functions, with no need to thread a request object through)
    carries the same `request_id` and can be grepped/correlated together.

A single access-log line is emitted per request on completion, replacing
uvicorn's default unstructured access log (disabled in `app/core/logging.py`).
"""

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response

logger = structlog.get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


async def request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """ASGI middleware: assign/propagate a request ID and log request start/end."""
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
    start = time.perf_counter()

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "request_failed",
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
        )
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers[REQUEST_ID_HEADER] = request_id
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response
