"""Global exception handlers, registered once on the `app` in `app/main.py`.

Guarantees every error response — whatever raised it, anywhere in the app —
has the same JSON shape (`detail`, `type`, `request_id`), so frontend error
handling and API consumers don't need a special case per exception type.
`request_id` matches `X-Request-ID` (see `app/core/middleware.py`), so a
client-reported error can be grepped straight to the matching structured log
lines and (if enabled) Sentry event/OTel trace.
"""

import sentry_sdk
import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

logger = structlog.get_logger(__name__)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_body(*, detail: object, error_type: str, request_id: str | None) -> dict[str, object]:
    return {"detail": detail, "type": error_type, "request_id": request_id}


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Preserve the raised status code/detail, just add `type`/`request_id`."""
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            detail=exc.detail, error_type="http_error", request_id=_request_id(request)
        ),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Same shape as `http_exception_handler`, for Pydantic/FastAPI request-validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=_error_body(
            detail=exc.errors(), error_type="validation_error", request_id=_request_id(request)
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for anything else: log it, report it to Sentry (if configured), and
    return a generic message — never leak internal exception details/tracebacks to
    the client.
    """
    request_id = _request_id(request)
    logger.exception("unhandled_exception", request_id=request_id, path=request.url.path)
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(
            detail="Internal server error", error_type="internal_error", request_id=request_id
        ),
    )


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Same error shape as everything else, plus a `Retry-After` header."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=_error_body(
            detail=f"Rate limit exceeded: {exc.detail}",
            error_type="rate_limited",
            request_id=_request_id(request),
        ),
        headers={"Retry-After": "60"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire up all handlers. Call once on the app in `app/main.py`."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
