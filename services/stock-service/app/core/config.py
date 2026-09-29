from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Stock-service settings (skill fastapi-templates: core/config)."""

    DATABASE_URL: str = "sqlite:///./stock.db"
    API_V1_STR: str = "/api/v1"

    model_config = {"env_prefix": "STOCK_", "env_file": ".env"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
