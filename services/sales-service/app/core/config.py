import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Sales-service settings (skill fastapi-templates: core/config)."""

    DATABASE_URL: str = "sqlite:///./sales.db"
    API_V1_STR: str = "/api/v1"
    STOCK_SERVICE_URL: str = "http://localhost:8002"
    STOCK_TIMEOUT_SECONDS: float = 5.0
    JWT_SECRET: str = "change-me-dev-only"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me-admin"

    model_config = {"env_prefix": "SALES_", "env_file": ".env"}


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    if os.getenv("POS_ENV", "dev") == "prod" and settings.JWT_SECRET == "change-me-dev-only":
        raise RuntimeError("SALES_JWT_SECRET debe definirse en producción")
    return settings
