from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "app_db"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    auth0_domain: str = "your-tenant.us.auth0.com"
    auth0_api_audience: str = "https://api.your-app.example.com"
    auth0_algorithms: str = "RS256"

    backend_cors_origins: list[str] = ["http://localhost:5173"]

    # Example agent (see app/agents/). Defaults work with no API key set, but
    # calling the /api/v1/agent/chat endpoint for real requires a valid key.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = Field(default=0.0, ge=0.0, le=2.0)

    @property
    def database_url(self) -> str:
        """Build the async Postgres DSN from its component parts.

        Kept as separate settings fields (rather than one literal DSN
        string) so individual pieces can be overridden independently via
        env vars, and so no plaintext credential pair ever needs to be
        hardcoded as a single connection-string literal in source.
        """
        driver = "postgresql+psycopg"
        auth = f"{self.postgres_user}:{self.postgres_password}"
        host = f"{self.postgres_host}:{self.postgres_port}"
        return f"{driver}://{auth}@{host}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """Build the Redis DSN from its component parts (see `database_url`)."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def auth0_issuer(self) -> str:
        return f"https://{self.auth0_domain}/"

    @property
    def auth0_jwks_url(self) -> str:
        return f"https://{self.auth0_domain}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
