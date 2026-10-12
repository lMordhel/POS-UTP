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

    model_config = {"env_prefix": "STOCK_", "env_file": ".env"}


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    if os.getenv("POS_ENV", "dev") == "prod" and settings.JWT_SECRET == "change-me-dev-only":
        raise RuntimeError("STOCK_JWT_SECRET debe definirse en producción")
    return settings
