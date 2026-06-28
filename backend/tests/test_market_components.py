from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest
from app.core.config import BACKEND_DIRECTORY
from app.domain.errors import ProviderDataError, ProviderUnavailableError
from app.domain.market import MarketSymbol, ProviderName, SourceBar
from app.providers.csv_provider import CsvMarketDataProvider
from app.providers.yfinance_provider import YFinanceMarketDataProvider
from app.repositories.market_data_repository import MarketDataRepository
from app.services.market_data_normalizer import MarketDataNormalizer
from app.services.market_data_service import MarketDataService


def demo_symbol() -> MarketSymbol:
    return MarketSymbol(
        symbol="AAPL",
        name="Apple Inc.",
        market="US",
        asset_type="equity",
        exchange="NASDAQ",
        currency="USD",
        timezone="America/New_York",
    )


def test_normalizer_sorts_deduplicates_and_removes_invalid_rows() -> None:
    provider = CsvMarketDataProvider(BACKEND_DIRECTORY / "data" / "seed")
    fetched = provider.fetch_ohlcv(demo_symbol(), date(2023, 1, 3), date(2023, 1, 4))
    invalid = SourceBar(
        trade_date=date(2023, 1, 5),
        open=-1,
        high=1,
        low=1,
        close=1,
        adjusted_close=1,
        volume=1,
    )
    duplicate = fetched.bars[0]
    expanded = fetched.__class__(
        symbol=fetched.symbol,
        provider=fetched.provider,
        dataset=fetched.dataset,
        bars=(fetched.bars[1], invalid, fetched.bars[0], duplicate),
        is_adjusted=fetched.is_adjusted,
        is_fixture_data=fetched.is_fixture_data,
        warnings=fetched.warnings,
        metadata=fetched.metadata,
    )
    result = MarketDataNormalizer().normalize(expanded)
    assert [bar.trade_date for bar in result.bars] == [date(2023, 1, 3), date(2023, 1, 4)]
    assert {warning.code for warning in result.warnings} >= {
        "duplicate_dates_removed",
        "invalid_rows_removed",
        "provider_notice",
    }


def test_normalizer_rejects_an_empty_valid_result() -> None:
    provider = CsvMarketDataProvider(BACKEND_DIRECTORY / "data" / "seed")
    fetched = provider.fetch_ohlcv(demo_symbol(), date(2023, 1, 3), date(2023, 1, 3))
    empty = fetched.__class__(
        symbol=fetched.symbol,
        provider=fetched.provider,
        dataset=fetched.dataset,
        bars=(),
        is_adjusted=fetched.is_adjusted,
        is_fixture_data=fetched.is_fixture_data,
    )
    with pytest.raises(ProviderDataError):
        MarketDataNormalizer().normalize(empty)


def test_yfinance_adapter_normalizes_injected_dataframe() -> None:
    frame = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Adj Close": [100.5, 101.5],
            "Volume": [1_000_000, 1_100_000],
        },
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
    )

    def download(**_kwargs):
        return frame

    result = YFinanceMarketDataProvider(download_function=download).fetch_ohlcv(
        demo_symbol(), date(2020, 1, 2), date(2020, 1, 3)
    )
    assert result.provider is ProviderName.YFINANCE
    assert result.is_adjusted is False
    assert len(result.bars) == 2
    assert result.bars[0].adjusted_close == 100.5


def test_yfinance_adapter_wraps_network_errors() -> None:
    def download(**_kwargs):
        raise OSError("network down")

    provider = YFinanceMarketDataProvider(download_function=download)
    with pytest.raises(ProviderUnavailableError):
        provider.fetch_ohlcv(demo_symbol(), date(2020, 1, 2), date(2020, 1, 3))


def test_service_enforces_response_limit(tmp_path: Path) -> None:
    csv_provider = CsvMarketDataProvider(BACKEND_DIRECTORY / "data" / "seed")
    repository = MarketDataRepository(
        tmp_path / "market.sqlite3",
        BACKEND_DIRECTORY / "app" / "database" / "schema.sql",
    )
    service = MarketDataService(
        repository=repository,
        providers={
            ProviderName.CSV: csv_provider,
            ProviderName.YFINANCE: YFinanceMarketDataProvider(enabled=False),
            ProviderName.FINMIND: type(
                "ReservedProvider",
                (),
                {
                    "name": ProviderName.FINMIND,
                    "configured": False,
                    "list_symbols": lambda self: (),
                    "fetch_ohlcv": lambda self, *_args, **_kwargs: None,
                },
            )(),
        },
        normalizer=MarketDataNormalizer(),
        seed_demo_data=True,
        max_response_bars=100,
    )
    service.initialize()
    with pytest.raises(Exception) as error:
        service.get_series("AAPL")
    assert error.value.__class__.__name__ == "MarketDataLimitError"


def test_csv_provider_metadata_and_dates() -> None:
    provider = CsvMarketDataProvider(BACKEND_DIRECTORY / "data" / "seed")
    symbols = provider.list_symbols()
    assert len(symbols) == 22
    assert [item.symbol for item in symbols[:3]] == ["AAPL", "ALFA", "BRAV"]
    aapl = next(item for item in symbols if item.symbol == "AAPL")
    result = provider.fetch_ohlcv(aapl, date(2023, 1, 3), date(2023, 1, 4))
    assert result.is_fixture_data is True
    assert result.is_adjusted is False
    assert len(result.bars) == 2
    assert result.bars[0].trade_date == date(2023, 1, 3)


def test_repository_records_retrieval_timestamp(tmp_path: Path) -> None:
    provider = CsvMarketDataProvider(BACKEND_DIRECTORY / "data" / "seed")
    repository = MarketDataRepository(
        tmp_path / "market.sqlite3",
        BACKEND_DIRECTORY / "app" / "database" / "schema.sql",
    )
    repository.initialize()
    repository.upsert_symbols(provider.list_symbols())
    fetched = provider.fetch_ohlcv(provider.list_symbols()[0], date(2023, 1, 3), date(2023, 1, 3))
    result = MarketDataNormalizer().normalize(
        fetched, retrieved_at=datetime(2024, 1, 1, tzinfo=UTC)
    )
    assert repository.upsert_bars(result.bars) == 1
    stored = repository.get_bars("AAPL")
    assert stored[0].retrieved_at == datetime(2024, 1, 1, tzinfo=UTC)
    assert repository.ping() is True
