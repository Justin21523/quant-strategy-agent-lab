from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_market_data_service
from app.schemas.system import Capability, MarketCacheStatsResponse, SystemInfoResponse
from app.services.market_data_service import MarketDataService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse, summary="Project phase capabilities")
def system_info(
    service: Annotated[MarketDataService, Depends(get_market_data_service)],
) -> SystemInfoResponse:
    stats = service.cache_stats()
    return SystemInfoResponse(
        phase="1",
        phase_name="Market Data Layer",
        cache=MarketCacheStatsResponse(
            symbols=stats.symbols,
            bars=stats.bars,
            sync_records=stats.sync_records,
        ),
        capabilities=[
            Capability(
                key="frontend_shell",
                label="Modular Vanilla JavaScript shell",
                status="ready",
            ),
            Capability(
                key="market_catalog",
                label="AAPL / SPY / QQQ symbol catalog",
                status="ready",
            ),
            Capability(
                key="sqlite_cache",
                label="Normalized SQLite OHLCV cache",
                status="ready",
            ),
            Capability(
                key="csv_fallback",
                label="Deterministic offline CSV fallback",
                status="ready",
            ),
            Capability(
                key="yfinance_sync",
                label="Optional yfinance synchronization",
                status="ready",
            ),
            Capability(
                key="indicator_engine",
                label="Technical indicator engine",
                status="planned",
            ),
            Capability(
                key="backtest_engine",
                label="Backtest engine",
                status="planned",
            ),
        ],
    )
