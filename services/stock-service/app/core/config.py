import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Stock-service settings (skill fastapi-templates: core/config)."""

    DATABASE_URL: str = "sqlite:///./stock.db"
    API_V1_STR: str = "/api/v1"
    JWT_SECRET: str = "change-me-dev-only"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:5173"
    RATE_WRITE: str = "60/minute"

    model_config = {"env_prefix": "STOCK_", "env_file": ".env"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    if os.getenv("POS_ENV", "dev") == "prod":
        if settings.JWT_SECRET == "change-me-dev-only":
            raise RuntimeError("STOCK_JWT_SECRET debe definirse en producción")
        if "*" in settings.cors_origins_list:
            raise RuntimeError("STOCK_CORS_ORIGINS no puede ser '*' en producción")
    return settings
