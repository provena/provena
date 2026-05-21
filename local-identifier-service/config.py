"""Configuration for local identifier service."""
from pydantic import BaseSettings
from typing import Optional
from functools import lru_cache


class Config(BaseSettings):
    """Configuration loaded from environment."""
    database_url: str = "postgresql://postgres:postgres@localhost:5432/identifier_db"
    handle_prefix: str = "20.5000"
    resolve_base_url: Optional[str] = None  # e.g. https://registry.example.com/item

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Config:
    return Config()
