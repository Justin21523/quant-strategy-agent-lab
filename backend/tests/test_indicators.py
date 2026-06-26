from datetime import UTC, date, datetime, timedelta

import numpy as np
from app.domain.market import MarketBar
from app.services.indicator_service import IndicatorService
from fastapi.testclient import TestClient


def bars_from_closes(closes: list[float]) -> tuple[MarketBar, ...]:
    start = date(2024, 1, 1)
    return tuple(
        MarketBar(
            symbol="TEST",
            interval="1d",
            trade_date=start + timedelta(days=index),
            open=close,
            high=close + 1,
            low=close - 1,
            close=close,
            adjusted_close=close,
            volume=1_000 + index,
            provider="csv",
            dataset="unit-test",
            source_timezone="UTC",
            currency="USD",
            is_adjusted=False,
            is_fixture_data=True,
            retrieved_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        for index, close in enumerate(closes)
    )


def by_key(bundle, key: str):
    return next(item for item in bundle.series if item.key == key)


def test_indicator_service_computes_default_bundle_with_aligned_dates() -> None:
    bars = bars_from_closes([float(value) for value in range(1, 81)])
    bundle = IndicatorService().compute_default_bundle(bars)
    assert bundle.profile == "default"
    assert bundle.count == 7
    assert len(bundle.warnings) == 0
    assert {series.key for series in bundle.series} == {
        "sma_20",
        "sma_60",
        "ema_20",
        "rsi_14",
        "macd_12_26_9",
        "bbands_20_2",
        "atr_14",
    }
    assert all(series.values[0].date == bars[0].trade_date for series in bundle.series)
    assert all(series.values[-1].date == bars[-1].trade_date for series in bundle.series)


def test_sma_rsi_bollinger_and_atr_values_are_deterministic() -> None:
    bars = bars_from_closes([float(value) for value in range(1, 81)])
    bundle = IndicatorService().compute_default_bundle(bars)

    sma20 = by_key(bundle, "sma_20")
    assert sma20.values[18].values["sma_20"] is None
    assert sma20.values[19].values["sma_20"] == 10.5

    rsi14 = by_key(bundle, "rsi_14")
    assert rsi14.values[13].values["rsi_14"] is None
    assert rsi14.values[14].values["rsi_14"] == 100.0

    bands = by_key(bundle, "bbands_20_2")
    middle = bands.values[19].values["middle"]
    upper = bands.values[19].values["upper"]
    lower = bands.values[19].values["lower"]
    expected_std = float(np.std(np.arange(1, 21), ddof=0))
    assert middle == 10.5
    assert round(upper, 6) == round(10.5 + 2 * expected_std, 6)
    assert round(lower, 6) == round(10.5 - 2 * expected_std, 6)

    atr14 = by_key(bundle, "atr_14")
    assert atr14.values[13].values["atr_14"] == 2.0


def test_macd_exposes_three_series_values_after_warmup() -> None:
    bars = bars_from_closes([float(value) for value in range(1, 100)])
    bundle = IndicatorService().compute_default_bundle(bars)
    macd = by_key(bundle, "macd_12_26_9")
    assert macd.warmup_period == 34
    assert set(macd.values[-1].values) == {"macd", "signal", "histogram"}
    assert macd.values[-1].values["macd"] is not None
    assert macd.values[-1].values["signal"] is not None
    assert macd.values[-1].values["histogram"] is not None


def test_indicator_warning_when_range_is_short() -> None:
    bars = bars_from_closes([float(value) for value in range(1, 10)])
    bundle = IndicatorService().compute_default_bundle(bars)
    assert bundle.warnings[0].code == "insufficient_warmup_rows"
    assert bundle.warnings[0].context["required_warmup"] == 60


def test_indicator_catalog_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/indicators/catalog")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6
    assert {item["kind"] for item in body["indicators"]} == {
        "sma",
        "ema",
        "rsi",
        "macd",
        "bollinger_bands",
        "atr",
    }


def test_ohlcv_can_include_indicator_bundle(client: TestClient) -> None:
    response = client.get(
        "/api/v1/market/ohlcv",
        params={
            "symbol": "AAPL",
            "start": "2023-01-03",
            "end": "2023-04-30",
            "include_indicators": "true",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["indicators"]["count"] == 7
    assert body["indicators"]["series"][0]["key"] == "sma_20"
    assert len(body["indicators"]["series"][0]["values"]) == body["count"]
    assert body["indicators"]["series"][0]["values"][0]["values"] == {"sma_20": None}
    assert body["indicators"]["series"][0]["values"][-1]["values"]["sma_20"] is not None
