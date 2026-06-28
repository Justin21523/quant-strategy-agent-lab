from fastapi.testclient import TestClient


def test_indicator_catalog_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/indicators/catalog")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6
    kinds = {item["kind"] for item in body["indicators"]}
    assert {"sma", "ema", "rsi", "macd", "bollinger_bands", "atr"} == kinds


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
    assert [item["key"] for item in body["indicators"]["series"]] == [
        "sma_20",
        "sma_60",
        "ema_20",
        "rsi_14",
        "macd_12_26_9",
        "bbands_20_2",
        "atr_14",
    ]
    sma_20 = body["indicators"]["series"][0]
    assert sma_20["values"][0]["values"]["sma_20"] is None
    assert sma_20["values"][-1]["values"]["sma_20"] is not None


def test_ohlcv_returns_multi_output_indicator_series(client: TestClient) -> None:
    response = client.get(
        "/api/v1/market/ohlcv",
        params={
            "symbol": "SPY",
            "start": "2023-01-03",
            "end": "2023-03-31",
            "include_indicators": "true",
        },
    )
    assert response.status_code == 200
    body = response.json()
    series_by_key = {item["key"]: item for item in body["indicators"]["series"]}
    assert set(series_by_key["macd_12_26_9"]["values"][-1]["values"]) == {
        "macd",
        "signal",
        "histogram",
    }
    assert set(series_by_key["bbands_20_2"]["values"][-1]["values"]) == {
        "middle",
        "upper",
        "lower",
    }


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
    codes = {warning["code"] for warning in response.json()["indicators"]["warnings"]}
    assert "insufficient_warmup_rows" in codes
