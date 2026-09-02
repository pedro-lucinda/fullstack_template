"""Structured logging setup (structlog), configured once at process start.

Every log line is a structured event (dict), rendered either as JSON
(`log_format=json`, prod-friendly for log aggregators) or as a human-readable
console string (`log_format=console`, the local-dev default). The request-ID
bound by `RequestIDLogMiddleware` (see `app/core/middleware.py`) is
automatically merged into every log line emitted during that request via
structlog's contextvars, so a single `request_id` can be grepped across every
log line — and, once OTel tracing is enabled, correlated with the matching
trace/span.
"""

import logging
import sys

import structlog

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure stdlib logging + structlog. Call once, at app startup."""
    settings = get_settings()

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if settings.log_format == "json"
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.log_level.upper())

    # Route uvicorn's own loggers through the same structured handler instead
    # of letting them print their default unstructured access-log lines.
    for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(uvicorn_logger).handlers = [handler]
        logging.getLogger(uvicorn_logger).propagate = False


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger. Thin wrapper kept so callers only import from `app.core`."""
    return structlog.get_logger(name)
