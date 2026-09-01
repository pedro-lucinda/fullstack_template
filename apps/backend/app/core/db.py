from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# psycopg async driver uses the same "postgresql+psycopg" URL for sync and async;
# SQLAlchemy's create_async_engine picks the async psycopg implementation.
engine = create_async_engine(settings.database_url, echo=settings.env == "development")

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped async DB session."""
    async with async_session_factory() as session:
        yield session
