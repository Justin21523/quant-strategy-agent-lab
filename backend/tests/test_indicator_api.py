from fastapi.testclient import TestClient


def test_indicator_catalog_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/market/indicators/catalog")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 7
    keys = {item["key"] for item in body["indicators"]}
    assert {"sma_20", "sma_60", "rsi_14", "macd_12_26_9", "bbands_20_2", "atr_14"} <= keys


def test_ohlcv_can_include_default_indicators(client: TestClient) -> None:
    response = client.get(
        "/api/v1/market/ohlcv",
        params={
            "symbol": "AAPL",
            "start": "2023-01-03",
            "end": "2023-04-10",
            "include_indicators": "true",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert [item["key"] for item in body["indicators"]] == ["sma_20", "sma_60", "rsi_14"]
    assert body["bars"][0]["indicators"] == {"sma_20": None, "sma_60": None, "rsi_14": None}
    latest = body["bars"][-1]["indicators"]
    assert latest["sma_20"] is not None
    assert latest["sma_60"] is not None
    assert latest["rsi_14"] is not None


def test_ohlcv_accepts_custom_indicator_specs(client: TestClient) -> None:
    response = client.get(
        "/api/v1/market/ohlcv",
        params={
            "symbol": "SPY",
            "start": "2023-01-03",
            "end": "2023-03-31",
            "include_indicators": "true",
            "indicators": "sma:10,ema:10,macd:6:13:5,bbands:20:2,atr:14",
        },
    )
    assert response.status_code == 200
    body = response.json()
    output_keys = {key for item in body["indicators"] for key in item["output_keys"]}
    assert {
        "sma_10",
        "ema_10",
        "macd_6_13_5_line",
        "macd_6_13_5_signal",
        "macd_6_13_5_histogram",
        "bbands_20_2_upper",
        "atr_14",
    } <= output_keys
    assert any(value is not None for value in body["bars"][-1]["indicators"].values())


def test_short_range_produces_indicator_warning(client: TestClient) -> None:
    response = client.get(
        "/api/v1/market/ohlcv",
        params={
            "symbol": "QQQ",
            "start": "2023-01-03",
            "end": "2023-01-06",
            "include_indicators": "true",
        },
    )
    assert response.status_code == 200
    codes = {warning["code"] for warning in response.json()["warnings"]}
    assert "indicator_warmup_exceeds_series" in codes
    assert "indicator_no_valid_points" in codes
