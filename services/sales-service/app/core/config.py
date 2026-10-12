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
    CORS_ORIGINS: str = "http://localhost:5173"
    RATE_LOGIN: str = "5/minute"
    RATE_REFRESH: str = "20/minute"
    RATE_WRITE: str = "60/minute"

    model_config = {"env_prefix": "SALES_", "env_file": ".env"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    if os.getenv("POS_ENV", "dev") == "prod":
        if settings.JWT_SECRET == "change-me-dev-only":
            raise RuntimeError("SALES_JWT_SECRET debe definirse en producción")
        if settings.ADMIN_PASSWORD == "change-me-admin":
            raise RuntimeError("SALES_ADMIN_PASSWORD debe definirse en producción")
        if "*" in settings.cors_origins_list:
            raise RuntimeError("SALES_CORS_ORIGINS no puede ser '*' en producción")
    return settings
