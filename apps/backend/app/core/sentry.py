"""Sentry error tracking setup. Opt-in via `settings.sentry_dsn` (empty by
default, which disables it entirely) so no external network calls happen
unless a contributor deliberately configures a DSN (e.g. in production).
"""

import sentry_sdk

from app.core.config import get_settings


def setup_sentry() -> None:
    """Initialize the Sentry SDK. No-op if no DSN is configured."""
    settings = get_settings()
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )
