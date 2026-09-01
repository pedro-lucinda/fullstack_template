from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import todos
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Fullstack Template API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
