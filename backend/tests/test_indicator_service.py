from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta

import pytest
from app.domain.indicator import IndicatorSpec, IndicatorType
from app.domain.market import CachedSymbolSummary, MarketBar, MarketSeries, MarketSymbol
from app.services.indicator_service import IndicatorService


class DummyMarketDataService:
    max_response_bars = 10_000


def make_series(length: int = 80) -> MarketSeries:
    symbol = MarketSymbol(
        symbol="TEST",
        name="Test Fixture",
        market="US",
        asset_type="equity",
        exchange="XNAS",
        currency="USD",
        timezone="America/New_York",
    )
    start = date(2024, 1, 2)
    retrieved_at = datetime(2024, 1, 2, tzinfo=UTC)
    bars = tuple(
        MarketBar(
            symbol="TEST",
            interval="1d",
            trade_date=start + timedelta(days=index),
            open=float(index + 1),
            high=float(index + 2),
            low=float(index),
            close=float(index + 1),
            adjusted_close=float(index + 1),
            volume=1_000 + index,
            provider="fixture",
            dataset="unit-test",
            source_timezone="UTC",
            currency="USD",
            is_adjusted=False,
            is_fixture_data=True,
            retrieved_at=retrieved_at,
        )
        for index in range(length)
    )
    summary = CachedSymbolSummary(
        symbol=symbol,
        cached_bar_count=length,
        first_cached_date=bars[0].trade_date,
        last_cached_date=bars[-1].trade_date,
        cached_providers=("fixture",),
    )
    return MarketSeries(
        symbol=symbol,
        cache_summary=summary,
        bars=bars,
        requested_start=bars[0].trade_date,
        requested_end=bars[-1].trade_date,
        effective_start=bars[0].trade_date,
        effective_end=bars[-1].trade_date,
        providers=("fixture",),
        datasets=("unit-test",),
        latest_retrieved_at=retrieved_at,
        contains_fixture_data=True,
        warnings=(),
    )


@pytest.fixture
def service() -> IndicatorService:
    return IndicatorService(DummyMarketDataService())


def last_value(bundle, key: str) -> float:
    for item in bundle.series:
        if key in item.output_keys:
            value = item.points[-1].values[key]
            assert value is not None
            return value
    raise AssertionError(f"Missing indicator key: {key}")


def test_sma_uses_window_mean(service: IndicatorService) -> None:
    bundle = service.compute(make_series(10), specs=(IndicatorSpec(IndicatorType.SMA, window=3),))
    assert last_value(bundle, "sma_3") == pytest.approx((8 + 9 + 10) / 3)
    assert bundle.series[0].points[0].values["sma_3"] is None
    assert bundle.series[0].valid_points == 8


def test_ema_is_warmed_up_and_tracks_trend(service: IndicatorService) -> None:
    bundle = service.compute(make_series(20), specs=(IndicatorSpec(IndicatorType.EMA, window=5),))
    ema = last_value(bundle, "ema_5")
    assert 15 < ema < 20
    assert bundle.series[0].warmup_period == 5


def test_rsi_reaches_overbought_on_monotonic_gain(service: IndicatorService) -> None:
    bundle = service.compute(make_series(30), specs=(IndicatorSpec(IndicatorType.RSI, window=14),))
    assert last_value(bundle, "rsi_14") == pytest.approx(100.0)


def test_macd_outputs_line_signal_and_histogram(service: IndicatorService) -> None:
    spec = IndicatorSpec(IndicatorType.MACD, fast_window=12, slow_window=26, signal_window=9)
    bundle = service.compute(make_series(80), specs=(spec,))
    keys = bundle.series[0].output_keys
    assert keys == ("macd_12_26_9_line", "macd_12_26_9_signal", "macd_12_26_9_histogram")
    assert all(math.isfinite(last_value(bundle, key)) for key in keys)


def test_bollinger_bands_wrap_middle_band(service: IndicatorService) -> None:
    spec = IndicatorSpec(IndicatorType.BOLLINGER_BANDS, window=20, standard_deviations=2)
    bundle = service.compute(make_series(40), specs=(spec,))
    upper = last_value(bundle, "bbands_20_2_upper")
    middle = last_value(bundle, "bbands_20_2_middle")
    lower = last_value(bundle, "bbands_20_2_lower")
    assert upper > middle > lower


def test_atr_uses_true_range(service: IndicatorService) -> None:
    bundle = service.compute(make_series(20), specs=(IndicatorSpec(IndicatorType.ATR, window=14),))
    assert last_value(bundle, "atr_14") == pytest.approx(2.0)


def test_resolve_specs_parses_custom_contract(service: IndicatorService) -> None:
    specs = service.resolve_specs(requested="sma:10,rsi:7,macd:6:13:5,bbands:20:2.5,atr:14")
    assert [spec.key for spec in specs] == [
        "sma_10",
        "rsi_7",
        "macd_6_13_5",
        "bbands_20_2.5",
        "atr_14",
    ]
