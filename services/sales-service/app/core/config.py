from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Sales-service settings (skill fastapi-templates: core/config)."""

    DATABASE_URL: str = "sqlite:///./sales.db"
    API_V1_STR: str = "/api/v1"
    STOCK_SERVICE_URL: str = "http://localhost:8002"
    STOCK_TIMEOUT_SECONDS: float = 5.0

    model_config = {"env_prefix": "SALES_", "env_file": ".env"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
