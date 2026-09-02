from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import request_context_middleware
from app.core.rate_limit import limiter
from app.core.redis import get_redis
from app.core.sentry import setup_sentry
from app.core.telemetry import setup_tracing
from app.modules.agent.router import router as agent_router
from app.modules.todos.router import router as todos_router

settings = get_settings()

configure_logging()
setup_sentry()

logger = get_logger(__name__)

app = FastAPI(title="Fullstack Template API", version="0.1.0")

setup_tracing(app)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_context_middleware)
register_exception_handlers(app)

app.include_router(todos_router)
app.include_router(agent_router)


@app.get("/health/live", tags=["health"])
async def health_live() -> dict[str, str]:
    """Liveness probe: is the process itself up? Never checks dependencies —
    a dependency outage should not cause an orchestrator to restart a
    perfectly healthy process (see `/health/ready` for that check)."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def health_ready(
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> JSONResponse:
    """Readiness probe: can this instance actually serve traffic right now?

    Pings Postgres and Redis directly (unlike `/health/live`, which is a
    static response) so an orchestrator can route around an instance whose
    dependencies are unreachable, e.g. mid-database-restart. Depends on the
    same `get_db`/`get_redis` dependencies used elsewhere so tests can swap
    in fakes the same way they do for every other route.
    """
    checks: dict[str, str] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report dependency failure, don't crash the probe
        checks["postgres"] = f"error: {exc}"

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report dependency failure, don't crash the probe
        checks["redis"] = f"error: {exc}"

    healthy = all(check == "ok" for check in checks.values())
    if not healthy:
        logger.warning("readiness_check_failed", checks=checks)

    body = {"status": "ok" if healthy else "unavailable", "checks": checks}
    code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=body, status_code=code)
