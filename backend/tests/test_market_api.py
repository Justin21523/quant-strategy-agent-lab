from fastapi.testclient import TestClient


def test_symbol_catalog_is_bootstrapped(client: TestClient) -> None:
    response = client.get("/api/v1/market/symbols")
    assert response.status_code == 200
    body = response.json()
    symbols = [item["symbol"] for item in body["symbols"]]
    assert body["total"] == 22
    assert {"AAPL", "QQQ", "SPY", "ALFA", "SIER"} <= set(symbols)
    assert (
        next(item for item in body["symbols"] if item["symbol"] == "AAPL")["cached_bar_count"]
        == 782
    )
    assert all(item["cached_providers"] == ["csv"] for item in body["symbols"])
    assert {item["provider"] for item in body["providers"]} == {
        "csv",
        "yfinance",
        "finmind",
    }


def test_provider_capabilities_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/market/providers")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    providers = {item["provider"]: item for item in body["providers"]}
    assert providers["csv"]["status"] == "ready"
    assert providers["yfinance"]["status"] == "unavailable"
    assert providers["finmind"]["status"] == "reserved"


def test_symbol_filters(client: TestClient) -> None:
    equity = client.get("/api/v1/market/symbols?asset_type=equity")
    assert equity.status_code == 200
    assert equity.json()["total"] == 20
    assert [item["symbol"] for item in equity.json()["symbols"]][:3] == ["AAPL", "ALFA", "BRAV"]

    us = client.get("/api/v1/market/symbols?market=us")
    assert us.status_code == 200
    assert us.json()["total"] == 22


def test_ohlcv_response_includes_source_and_warning(client: TestClient) -> None:
    response = client.get(
        "/api/v1/market/ohlcv",
        params={"symbol": "AAPL", "start": "2023-01-03", "end": "2023-01-09"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"]["symbol"] == "AAPL"
    assert body["symbol"]["cached_bar_count"] == 782
    assert body["symbol"]["first_cached_date"] == "2023-01-03"
    assert body["symbol"]["last_cached_date"] == "2025-12-31"
    assert body["symbol"]["cached_providers"] == ["csv"]
    assert body["count"] == 5
    assert body["effective_range"] == {"start": "2023-01-03", "end": "2023-01-09"}
    assert body["source"]["providers"] == ["csv"]
    assert body["source"]["served_from_cache"] is True
    assert body["source"]["contains_fixture_data"] is True
    assert body["source"]["adjustment"] == "raw_ohlc_with_adjusted_close"
    assert body["bars"][0]["date"] == "2023-01-03"
    assert body["bars"][-1]["date"] == "2023-01-09"
    assert body["warnings"][0]["code"] == "synthetic_fixture_data"


def test_partial_range_produces_quality_warnings(client: TestClient) -> None:
    response = client.get(
        "/api/v1/market/ohlcv",
        params={"symbol": "SPY", "start": "2022-01-01", "end": "2026-12-31"},
    )
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()["warnings"]}
    assert {"requested_start_not_available", "requested_end_not_available"} <= codes


def test_market_errors_are_structured(client: TestClient) -> None:
    unknown = client.get("/api/v1/market/ohlcv?symbol=NOPE")
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "symbol_not_found"

    invalid_range = client.get("/api/v1/market/ohlcv?symbol=AAPL&start=2023-01-04&end=2023-01-03")
    assert invalid_range.status_code == 422
    assert invalid_range.json()["error"]["code"] == "invalid_date_range"

    no_rows = client.get("/api/v1/market/ohlcv?symbol=AAPL&start=2030-01-01&end=2030-01-05")
    assert no_rows.status_code == 404
    assert no_rows.json()["error"]["code"] == "market_data_not_found"


def test_csv_sync_is_auditable(client: TestClient) -> None:
    response = client.post(
        "/api/v1/market/sync",
        json={
            "symbols": ["AAPL", "SPY"],
            "provider": "csv",
            "start": "2023-01-03",
            "end": "2023-01-09",
            "allow_fallback": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["successful"] == 2
    assert body["failed"] == 0
    assert body["run_id"].startswith("sync_")
    assert all(item["provider_used"] == "csv" for item in body["results"])
    assert all(item["bars_received"] == 5 for item in body["results"])
    assert all(item["is_fixture_data"] is True for item in body["results"])


def test_auto_sync_falls_back_when_network_provider_is_disabled(client: TestClient) -> None:
    response = client.post(
        "/api/v1/market/sync",
        json={
            "symbols": ["QQQ"],
            "provider": "auto",
            "start": "2023-01-03",
            "end": "2023-01-05",
            "allow_fallback": True,
        },
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["status"] == "success"
    assert result["provider_used"] == "csv"
    assert result["fallback_used"] is True
    assert result["attempts"][0].startswith("yfinance:")
    assert any(item["code"] == "provider_fallback_used" for item in result["warnings"])


def test_auto_sync_respects_disabled_fallback(client: TestClient) -> None:
    response = client.post(
        "/api/v1/market/sync",
        json={
            "symbols": ["QQQ"],
            "provider": "auto",
            "start": "2023-01-03",
            "end": "2023-01-05",
            "allow_fallback": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    result = body["results"][0]
    assert result["provider_used"] is None
    assert result["fallback_used"] is False
    assert len(result["attempts"]) == 1
    assert result["attempts"][0].startswith("yfinance:")


def test_reserved_provider_can_fail_without_breaking_batch_contract(client: TestClient) -> None:
    response = client.post(
        "/api/v1/market/sync",
        json={
            "symbols": ["AAPL", "UNKNOWN"],
            "provider": "finmind",
            "start": "2023-01-03",
            "end": "2023-01-05",
            "allow_fallback": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["failed"] == 2
    assert body["results"][0]["attempts"][0].startswith("finmind:")
    assert body["results"][1]["error"].startswith("Unsupported symbol")
