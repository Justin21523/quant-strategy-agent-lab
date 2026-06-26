from __future__ import annotations

from dataclasses import dataclass

from app.core.config import BACKEND_DIRECTORY, Settings
from app.domain.market import ProviderName
from app.providers.csv_provider import CsvMarketDataProvider
from app.providers.finmind_provider import FinMindMarketDataProvider
from app.providers.yfinance_provider import YFinanceMarketDataProvider
from app.repositories.market_data_repository import MarketDataRepository
from app.services.market_data_normalizer import MarketDataNormalizer
from app.services.market_data_service import MarketDataService
from app.services.strategy_template_service import StrategyTemplateService


@dataclass(slots=True)
class AppContainer:
    market_data_service: MarketDataService
    strategy_template_service: StrategyTemplateService

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
        return cls(
            market_data_service=MarketDataService(
                repository=repository,
                providers=providers,
                normalizer=MarketDataNormalizer(),
                seed_demo_data=settings.market_seed_demo_data,
                max_response_bars=settings.market_max_response_bars,
            ),
            strategy_template_service=StrategyTemplateService(),
        )

    def initialize(self) -> None:
        self.market_data_service.initialize()
