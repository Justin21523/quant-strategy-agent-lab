from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.core.container import AppContainer
from app.services.backtest_service import BacktestService
from app.services.data_quality_service import DataQualityService
from app.services.demo_research_service import DemoResearchService
from app.services.job_service import JobService
from app.services.market_data_service import MarketDataService
from app.services.multi_backtest_service import MultiBacktestService
from app.services.portfolio_service import PortfolioService
from app.services.research_pipeline_service import ResearchPipelineService
from app.services.scanner_service import ScannerService
from app.services.strategy_template_service import StrategyTemplateService
from app.services.universe_service import UniverseService


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_market_data_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> MarketDataService:
    return container.market_data_service


def get_strategy_template_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> StrategyTemplateService:
    return container.strategy_template_service


def get_backtest_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> BacktestService:
    return container.backtest_service


def get_universe_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> UniverseService:
    return container.universe_service


def get_scanner_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> ScannerService:
    return container.scanner_service


def get_data_quality_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> DataQualityService:
    return container.data_quality_service


def get_multi_backtest_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> MultiBacktestService:
    return container.multi_backtest_service


def get_portfolio_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> PortfolioService:
    return container.portfolio_service


def get_job_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> JobService:
    return container.job_service


def get_demo_research_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> DemoResearchService:
    return container.demo_research_service


def get_research_pipeline_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> ResearchPipelineService:
    return container.research_pipeline_service


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings
