"""Application settings loaded from environment variables."""

import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API application."""

    model_config = SettingsConfigDict(
        env_prefix="QSA_",
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Quant Strategy Agent Lab API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("api_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        """Ensure the API prefix is stable and has no trailing slash."""
        normalized = f"/{value.strip('/')}"
        return normalized if normalized != "/" else ""

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated or JSON-array CORS origins from the environment."""
        value = self.cors_origins.strip()
        if not value:
            return []
        if value.startswith("["):
            parsed = json.loads(value)
            if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                raise ValueError("QSA_CORS_ORIGINS JSON value must be an array of strings.")
            return [item.strip() for item in parsed if item.strip()]
        return [origin.strip() for origin in value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings object per process."""
    return Settings()
