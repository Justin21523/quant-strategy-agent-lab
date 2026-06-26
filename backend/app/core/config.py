from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
PROJECT_DIRECTORY = BACKEND_DIRECTORY.parent


class Settings(BaseSettings):
    project_name: str = "Quant Strategy Agent Lab API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    market_database_path: Path = BACKEND_DIRECTORY / "data" / "cache" / "market_data.sqlite3"
    market_csv_seed_dir: Path = BACKEND_DIRECTORY / "data" / "seed"
    market_seed_demo_data: bool = True
    market_max_response_bars: int = Field(default=10_000, ge=100, le=100_000)
    market_yfinance_enabled: bool = True
    market_provider_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    finmind_token: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_prefix="QSA_",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("market_database_path", "market_csv_seed_dir", mode="before")
    @classmethod
    def resolve_project_path(cls, value: Any) -> Any:
        """Resolve relative paths consistently from either repo root or backend cwd."""

        if value is None:
            return value
        path = Path(value).expanduser()
        if path.is_absolute():
            return path
        if path.parts and path.parts[0] == "backend":
            return (PROJECT_DIRECTORY / path).resolve()
        return (BACKEND_DIRECTORY / path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
