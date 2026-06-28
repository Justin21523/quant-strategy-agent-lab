from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta

import pytest
from app.domain.indicators import IndicatorKind, IndicatorPane, IndicatorSpec
from app.domain.market import CachedSymbolSummary, MarketBar, MarketSeries, MarketSymbol
from app.services.indicator_service import IndicatorService


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
    return IndicatorService()


def last_value(bundle, key: str) -> float:
    for item in bundle.series:
        if key in item.values[-1].values:
            value = item.values[-1].values[key]
            assert value is not None
            return value
    raise AssertionError(f"Missing indicator key: {key}")


def test_sma_uses_window_mean(service: IndicatorService) -> None:
    spec = IndicatorSpec(
        key="sma_3",
        kind=IndicatorKind.SMA,
        label="SMA 3",
        pane=IndicatorPane.PRICE,
        parameters={"window": 3, "source": "close"},
    )
    bundle = service.compute_bundle(make_series(10).bars, specs=(spec,), profile="unit-test")
    assert last_value(bundle, "sma_3") == pytest.approx((8 + 9 + 10) / 3)
    assert bundle.series[0].values[0].values["sma_3"] is None
    assert sum(point.values["sma_3"] is not None for point in bundle.series[0].values) == 8


def test_ema_is_warmed_up_and_tracks_trend(service: IndicatorService) -> None:
    spec = IndicatorSpec(
        key="ema_5",
        kind=IndicatorKind.EMA,
        label="EMA 5",
        pane=IndicatorPane.PRICE,
        parameters={"window": 5, "source": "close"},
    )
    bundle = service.compute_bundle(make_series(20).bars, specs=(spec,), profile="unit-test")
    ema = last_value(bundle, "ema_5")
    assert 15 < ema < 20
    assert bundle.series[0].warmup_period == 5


def test_rsi_reaches_overbought_on_monotonic_gain(service: IndicatorService) -> None:
    spec = IndicatorSpec(
        key="rsi_14",
        kind=IndicatorKind.RSI,
        label="RSI 14",
        pane=IndicatorPane.OSCILLATOR,
        parameters={"window": 14, "source": "close"},
    )
    bundle = service.compute_bundle(make_series(30).bars, specs=(spec,), profile="unit-test")
    assert last_value(bundle, "rsi_14") == pytest.approx(100.0)


def test_macd_outputs_line_signal_and_histogram(service: IndicatorService) -> None:
    spec = IndicatorSpec(
        key="macd_12_26_9",
        kind=IndicatorKind.MACD,
        label="MACD 12/26/9",
        pane=IndicatorPane.OSCILLATOR,
        parameters={"fast": 12, "slow": 26, "signal": 9, "source": "close"},
    )
    bundle = service.compute_bundle(make_series(80).bars, specs=(spec,), profile="unit-test")
    keys = tuple(bundle.series[0].values[-1].values)
    assert keys == ("macd", "signal", "histogram")
    assert all(math.isfinite(last_value(bundle, key)) for key in keys)


def test_bollinger_bands_wrap_middle_band(service: IndicatorService) -> None:
    spec = IndicatorSpec(
        key="bbands_20_2",
        kind=IndicatorKind.BOLLINGER_BANDS,
        label="Bollinger Bands 20/2",
        pane=IndicatorPane.PRICE,
        parameters={"window": 20, "stddev": 2, "source": "close"},
    )
    bundle = service.compute_bundle(make_series(40).bars, specs=(spec,), profile="unit-test")
    upper = last_value(bundle, "upper")
    middle = last_value(bundle, "middle")
    lower = last_value(bundle, "lower")
    assert upper > middle > lower


def test_atr_uses_true_range(service: IndicatorService) -> None:
    spec = IndicatorSpec(
        key="atr_14",
        kind=IndicatorKind.ATR,
        label="ATR 14",
        pane=IndicatorPane.VOLATILITY,
        parameters={"window": 14},
    )
    bundle = service.compute_bundle(make_series(20).bars, specs=(spec,), profile="unit-test")
    assert last_value(bundle, "atr_14") == pytest.approx(2.0)


def test_default_specs_include_current_indicator_bundle(service: IndicatorService) -> None:
    specs = service.default_specs()
    assert [spec.key for spec in specs] == [
        "sma_20",
        "sma_60",
        "ema_20",
        "rsi_14",
        "macd_12_26_9",
        "bbands_20_2",
        "atr_14",
    ]
