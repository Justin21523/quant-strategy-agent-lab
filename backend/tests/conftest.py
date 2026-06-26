from pathlib import Path

import pytest
from app.core.config import BACKEND_DIRECTORY, Settings
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        market_database_path=tmp_path / "market.sqlite3",
        market_csv_seed_dir=BACKEND_DIRECTORY / "data" / "seed",
        market_seed_demo_data=True,
        market_yfinance_enabled=False,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    with TestClient(create_app(settings)) as test_client:
        yield test_client
