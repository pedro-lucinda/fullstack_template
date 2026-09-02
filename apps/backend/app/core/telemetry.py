"""OpenTelemetry tracing setup. Opt-in via `settings.otel_enabled` (default
`False`) so it's a zero-cost addition until a contributor actually wants
traces — enable it locally with `OTEL_ENABLED=true` and the `jaeger` compose
service (`docker compose --profile observability up`), which exposes a UI at
http://localhost:16686.

Instruments FastAPI (request spans), SQLAlchemy (query spans) and httpx
(outbound calls to Auth0/OpenAI), so a single request's full chain — API ->
Postgres/Redis -> third-party call — shows up as one connected trace.
"""

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import get_settings
from app.core.db import engine


def setup_tracing(app: FastAPI) -> None:
    """Configure the global tracer provider and instrument the app in-place.

    No-op unless `settings.otel_enabled` is set, so importing/calling this is
    always safe (e.g. in tests) without needing a collector running.
    """
    settings = get_settings()
    if not settings.otel_enabled:
        return

    resource = Resource.create({SERVICE_NAME: settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
