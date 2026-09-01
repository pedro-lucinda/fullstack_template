from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/app_db"

    auth0_domain: str = "your-tenant.us.auth0.com"
    auth0_api_audience: str = "https://api.your-app.example.com"
    auth0_algorithms: str = "RS256"

    backend_cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def auth0_issuer(self) -> str:
        return f"https://{self.auth0_domain}/"

    @property
    def auth0_jwks_url(self) -> str:
        return f"https://{self.auth0_domain}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
