from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_market_data_service, get_strategy_template_service
from app.schemas.system import Capability, MarketCacheStatsResponse, SystemInfoResponse
from app.services.market_data_service import MarketDataService
from app.services.strategy_template_service import StrategyTemplateService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse, summary="Project phase capabilities")
def system_info(
    market_service: Annotated[MarketDataService, Depends(get_market_data_service)],
    strategy_service: Annotated[StrategyTemplateService, Depends(get_strategy_template_service)],
) -> SystemInfoResponse:
    stats = market_service.cache_stats()
    return SystemInfoResponse(
        phase="3",
        phase_name="Strategy Template System",
        cache=MarketCacheStatsResponse(
            symbols=stats.symbols,
            bars=stats.bars,
            sync_records=stats.sync_records,
        ),
        strategy_templates=len(strategy_service.list_templates()),
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
                key="indicator_engine",
                label="SMA, EMA, RSI, MACD, Bollinger Bands, and ATR",
                status="ready",
            ),
            Capability(
                key="strategy_templates",
                label="Five deterministic strategy templates",
                status="ready",
            ),
            Capability(
                key="strategy_json_dsl",
                label="Template-to-Strategy JSON DSL renderer",
                status="ready",
            ),
            Capability(
                key="strategy_validation",
                label="Backend Strategy DSL validation",
                status="ready",
            ),
            Capability(
                key="strategy_template_system",
                label="Deterministic templates render Strategy JSON DSL",
                status="ready",
            ),
            Capability(
                key="strategy_builder_ui",
                label="Vanilla JS template selector and live JSON preview",
                status="ready",
            ),
            Capability(
                key="backtest_engine",
                label="Backtest engine",
                status="planned",
            ),
        ],
    )
