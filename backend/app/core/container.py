from __future__ import annotations

from dataclasses import dataclass

from app.core.config import BACKEND_DIRECTORY, Settings
from app.domain.market import ProviderName
from app.providers.csv_provider import CsvMarketDataProvider
from app.providers.finmind_provider import FinMindMarketDataProvider
from app.providers.yfinance_provider import YFinanceMarketDataProvider
from app.repositories.market_data_repository import MarketDataRepository
from app.services.backtest_service import BacktestService
from app.services.data_quality_service import DataQualityService
from app.services.demo_research_service import DemoResearchService
from app.services.job_service import JobService
from app.services.market_data_normalizer import MarketDataNormalizer
from app.services.market_data_service import MarketDataService
from app.services.multi_backtest_service import MultiBacktestService
from app.services.performance_service import PerformanceService
from app.services.portfolio_service import PortfolioService
from app.services.research_pipeline_service import ResearchPipelineService
from app.services.scanner_service import ScannerService
from app.services.strategy_template_service import StrategyTemplateService
from app.services.universe_service import UniverseService


@dataclass(slots=True)
class AppContainer:
    market_data_service: MarketDataService
    strategy_template_service: StrategyTemplateService
    backtest_service: BacktestService
    universe_service: UniverseService
    scanner_service: ScannerService
    data_quality_service: DataQualityService
    multi_backtest_service: MultiBacktestService
    performance_service: PerformanceService
    portfolio_service: PortfolioService
    demo_research_service: DemoResearchService
    research_pipeline_service: ResearchPipelineService
    job_service: JobService

    @classmethod
    def build(cls, settings: Settings) -> AppContainer:
        csv_provider = CsvMarketDataProvider(settings.market_csv_seed_dir)
        token = settings.finmind_token.get_secret_value() if settings.finmind_token else None
        providers = {
            ProviderName.CSV: csv_provider,
            ProviderName.YFINANCE: YFinanceMarketDataProvider(
                enabled=settings.market_yfinance_enabled,
                timeout_seconds=settings.market_provider_timeout_seconds,
            ),
            ProviderName.FINMIND: FinMindMarketDataProvider(token=token),
        }
        repository = MarketDataRepository(
            settings.market_database_path,
            BACKEND_DIRECTORY / "app" / "database" / "schema.sql",
        )
        market_data_service = MarketDataService(
            repository=repository,
            providers=providers,
            normalizer=MarketDataNormalizer(),
            seed_demo_data=settings.market_seed_demo_data,
            max_response_bars=settings.market_max_response_bars,
        )
        strategy_template_service = StrategyTemplateService()
        backtest_service = BacktestService(
            market_data_service=market_data_service,
            strategy_template_service=strategy_template_service,
        )
        universe_service = UniverseService(repository)
        scanner_service = ScannerService(repository)
        data_quality_service = DataQualityService(repository)
        performance_service = PerformanceService()
        portfolio_service = PortfolioService(
            repository=repository,
            scanner_service=scanner_service,
            performance_service=performance_service,
        )
        multi_backtest_service = MultiBacktestService(
            repository=repository,
            backtest_service=backtest_service,
            strategy_template_service=strategy_template_service,
        )
        demo_research_service = DemoResearchService(
            repository=repository,
            market_data_service=market_data_service,
            scanner_service=scanner_service,
            data_quality_service=data_quality_service,
            portfolio_service=portfolio_service,
            multi_backtest_service=multi_backtest_service,
        )
        research_pipeline_service = ResearchPipelineService(
            repository=repository,
            market_data_service=market_data_service,
            scanner_service=scanner_service,
            data_quality_service=data_quality_service,
            portfolio_service=portfolio_service,
            multi_backtest_service=multi_backtest_service,
            demo_research_service=demo_research_service,
        )
        job_service = JobService(
            repository=repository,
            market_data_service=market_data_service,
            scanner_service=scanner_service,
            portfolio_service=portfolio_service,
            demo_research_service=demo_research_service,
            research_pipeline_service=research_pipeline_service,
        )
        return cls(
            market_data_service=market_data_service,
            strategy_template_service=strategy_template_service,
            universe_service=universe_service,
            scanner_service=scanner_service,
            data_quality_service=data_quality_service,
            multi_backtest_service=multi_backtest_service,
            performance_service=performance_service,
            portfolio_service=portfolio_service,
            demo_research_service=demo_research_service,
            research_pipeline_service=research_pipeline_service,
            job_service=job_service,
            backtest_service=backtest_service,
        )

    def initialize(self) -> None:
        self.market_data_service.initialize()
        self.portfolio_service.initialize_presets()
        self.research_pipeline_service.initialize_presets()
        self.job_service.start()

    def shutdown(self) -> None:
        self.job_service.stop()
