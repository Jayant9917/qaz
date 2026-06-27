"""Typed application configuration."""

from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated NOVO runtime settings."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_prefix="NOVO_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    app_name: str = "NOVO API"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    frontend_origin: str = "http://localhost:3000"
    require_infrastructure_for_readiness: bool = False

    postgres_host: str = "localhost"
    postgres_port: int = Field(default=5433, ge=1, le=65535)
    postgres_db: str = "novo"
    postgres_user: str = "novo"
    postgres_password: str = "change-me-development-only"

    redis_host: str = "localhost"
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_db: int = Field(default=0, ge=0)

    bootstrap_owner_email: str = "owner@novo.example"
    bootstrap_owner_display_name: str = "Jay Rana"
    bootstrap_owner_password: str = "novo-owner-1234"
    session_ttl_hours: int = Field(default=168, ge=1, le=24 * 30)
    audit_page_size_default: int = Field(default=100, ge=1, le=500)

    login_rate_limit: int = Field(default=5, ge=1, le=1000)
    login_rate_limit_window_seconds: int = Field(default=60, ge=1, le=86400)
    mutation_rate_limit: int = Field(default=30, ge=1, le=1000)
    mutation_rate_limit_window_seconds: int = Field(default=60, ge=1, le=86400)

    @property
    def postgres_dsn(self) -> str:
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return (
            f"postgresql+asyncpg://{user}:{password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""

    return Settings()
