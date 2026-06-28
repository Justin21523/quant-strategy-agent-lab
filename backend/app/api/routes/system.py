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
        phase="9F",
        phase_name="Guided Site Onboarding",
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
                label="Synthetic market catalog with 20-stock sample universe",
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
                key="backtest_engine",
                label="Deterministic long-only backtest engine",
                status="ready",
            ),
            Capability(
                key="trade_ledger",
                label="Closed trade ledger with fees and slippage",
                status="ready",
            ),
            Capability(
                key="equity_drawdown",
                label="Equity and drawdown curve output",
                status="ready",
            ),
            Capability(
                key="backtest_lab_ui",
                label="Interactive Backtest Lab with candle markers",
                status="ready",
            ),
            Capability(
                key="agent_timeline",
                label="Inspectable Agent workflow timeline",
                status="ready",
            ),
            Capability(
                key="market_universes",
                label="US common-stock universe and chunked synchronization",
                status="ready",
            ),
            Capability(
                key="stock_scanner",
                label="Operational technical scanner with presets and skipped-symbol reasons",
                status="ready",
            ),
            Capability(
                key="data_quality_report",
                label="Universe cache coverage and indicator readiness report",
                status="ready",
            ),
            Capability(
                key="multi_asset_backtest",
                label="Scanner-driven multi-asset backtest ranking",
                status="ready",
            ),
            Capability(
                key="portfolio_rebalance",
                label="Equal-weight portfolio rebalance simulation",
                status="ready",
            ),
            Capability(
                key="performance_analyzer",
                label="CAGR, volatility, Sharpe, Sortino, Calmar, drawdown, and monthly returns",
                status="ready",
            ),
            Capability(
                key="portfolio_presets",
                label="Scanner preset to portfolio strategy workflow",
                status="ready",
            ),
            Capability(
                key="job_queue",
                label="SQLite-backed long-running job queue with progress events",
                status="ready",
            ),
            Capability(
                key="quality_gates",
                label="Reusable data-quality thresholds for scanner and portfolio workflows",
                status="ready",
            ),
            Capability(
                key="research_demo_automation",
                label="In-app automated sample research workflow with Demo Studio playback",
                status="ready",
            ),
            Capability(
                key="demo_studio",
                label="Visual research playback with heatmap, ranking, and comparison charts",
                status="ready",
            ),
            Capability(
                key="research_pipeline",
                label="Configurable sync, quality, scanner, portfolio, and strategy workflow",
                status="ready",
            ),
            Capability(
                key="research_presets",
                label="Persisted Research Lab pipeline presets",
                status="ready",
            ),
            Capability(
                key="research_report_exports",
                label="Markdown, JSON, and CSV research run artifacts",
                status="ready",
            ),
            Capability(
                key="site_guide",
                label="Animated whole-site guide with spotlight targets",
                status="ready",
            ),
        ],
    )
