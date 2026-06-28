from fastapi.testclient import TestClient

from tests.test_universes import NASDAQ_SAMPLE, OTHER_HEADER, OTHER_SAMPLE

EMPTY_OTHER_SAMPLE = f"{OTHER_HEADER}\n"


def seed_universe(client: TestClient) -> None:
    client.app.state.container.universe_service.refresh_us_common_stocks(
        nasdaq_text=NASDAQ_SAMPLE,
        other_text=EMPTY_OTHER_SAMPLE,
    )


def test_batch_sync_processes_one_universe_chunk(client: TestClient) -> None:
    seed_universe(client)

    response = client.post(
        "/api/v1/market/batch-sync",
        json={
            "universe_id": "us_common_stocks",
            "provider": "csv",
            "start": "2023-01-03",
            "end": "2023-01-31",
            "chunk_size": 1,
            "cursor": 0,
            "allow_fallback": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 1
    assert body["successful"] == 1
    assert body["complete"] is True
    assert body["next_cursor"] is None


def test_scanner_run_persists_and_can_be_read(client: TestClient) -> None:
    seed_universe(client)

    response = client.post(
        "/api/v1/scans/run",
        json={
            "universe_id": "us_common_stocks",
            "start": "2023-01-03",
            "end": "2025-12-31",
            "rules": {
                "close_above_sma_200": False,
                "sma_20_above_sma_60": False,
                "rsi_min": 0,
                "rsi_max": 100,
                "volume_ratio_20d_min": 0,
                "return_60d_min_pct": -100,
            },
            "result_limit": 10,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_symbols"] == 1
    assert body["analyzed_symbols"] == 1
    assert body["matched_symbols"] == 1
    assert body["results"][0]["symbol"] == "AAPL"
    assert body["results"][0]["metrics"]["sma_200"] is not None

    read_response = client.get(f"/api/v1/scans/{body['run_id']}")
    assert read_response.status_code == 200
    assert read_response.json()["run_id"] == body["run_id"]

    list_response = client.get("/api/v1/scans?limit=5")
    assert list_response.status_code == 200
    assert list_response.json()["runs"][0]["run_id"] == body["run_id"]


def test_scanner_presets_and_skipped_reasons(client: TestClient) -> None:
    client.app.state.container.universe_service.refresh_us_common_stocks(
        nasdaq_text=NASDAQ_SAMPLE,
        other_text=OTHER_SAMPLE,
    )

    presets = client.get("/api/v1/scans/presets")
    assert presets.status_code == 200
    assert {item["preset_id"] for item in presets.json()["presets"]} >= {
        "trend_momentum",
        "oversold_watchlist",
    }

    response = client.post(
        "/api/v1/scans/run",
        json={
            "universe_id": "us_common_stocks",
            "start": "2023-01-03",
            "end": "2025-12-31",
            "rules": {
                "enable_close_above_sma_200": False,
                "enable_sma_20_above_sma_60": False,
                "enable_rsi_range": False,
                "enable_volume_ratio_20d": False,
                "enable_return_60d": False,
            },
            "result_limit": 10,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_symbols"] == 2
    assert body["matched_symbols"] == 1
    assert body["skipped_symbols"] == 1
    assert body["skipped"][0]["symbol"] == "IBM"
    assert body["skipped"][0]["reason"] == "no_cached_bars"


def test_batch_sync_history_modes_and_data_quality_report(client: TestClient) -> None:
    client.app.state.container.universe_service.refresh_us_common_stocks(
        nasdaq_text=NASDAQ_SAMPLE,
        other_text=OTHER_SAMPLE,
    )

    stale_response = client.post(
        "/api/v1/market/batch-sync",
        json={
            "universe_id": "us_common_stocks",
            "provider": "csv",
            "start": "2023-01-03",
            "end": "2023-01-31",
            "chunk_size": 10,
            "cursor": 0,
            "allow_fallback": False,
            "mode": "missing_or_stale",
            "stale_after": "2026-01-01",
        },
    )
    assert stale_response.status_code == 200
    stale_body = stale_response.json()
    assert stale_body["processed"] == 2
    assert stale_body["failed"] == 1

    retry_response = client.post(
        "/api/v1/market/batch-sync",
        json={
            "universe_id": "us_common_stocks",
            "provider": "csv",
            "start": "2023-01-03",
            "end": "2023-01-31",
            "chunk_size": 10,
            "cursor": 0,
            "allow_fallback": False,
            "mode": "retry_failed",
            "failed_run_id": stale_body["child_sync_run_id"],
        },
    )
    assert retry_response.status_code == 200
    retry_body = retry_response.json()
    assert retry_body["processed"] == 1
    assert retry_body["failed"] == 1
    assert retry_body["results"][0]["symbol"] == "IBM"

    history = client.get("/api/v1/market/batch-sync/runs?universe_id=us_common_stocks")
    assert history.status_code == 200
    assert history.json()["total"] >= 2

    records = client.get(f"/api/v1/market/sync-runs?run_id={stale_body['child_sync_run_id']}")
    assert records.status_code == 200
    assert records.json()["total"] == 2

    report = client.get(
        "/api/v1/data-quality/universes/us_common_stocks?start=2023-01-03&end=2025-12-31&limit=10"
    )
    assert report.status_code == 200
    report_body = report.json()
    assert report_body["member_count"] == 2
    assert report_body["covered_symbols"] == 1
    assert report_body["symbols"][0]["symbol"] == "AAPL"
    assert report_body["symbols"][1]["symbol"] == "IBM"
    assert "no_cached_bars" in report_body["symbols"][1]["warnings"]


def test_multi_asset_backtest_runs_top_scanner_results(client: TestClient) -> None:
    seed_universe(client)
    scan_response = client.post(
        "/api/v1/scans/run",
        json={
            "universe_id": "us_common_stocks",
            "start": "2023-01-03",
            "end": "2025-12-31",
            "rules": {
                "enable_close_above_sma_200": False,
                "enable_sma_20_above_sma_60": False,
                "enable_rsi_range": False,
                "enable_volume_ratio_20d": False,
                "enable_return_60d": False,
            },
            "result_limit": 10,
        },
    )
    assert scan_response.status_code == 200

    response = client.post(
        "/api/v1/multi-backtests/run",
        json={
            "scan_run_id": scan_response.json()["run_id"],
            "template_id": "buy_and_hold",
            "parameters": {},
            "top_n": 1,
            "start": "2023-01-03",
            "end": "2025-12-31",
            "initial_cash": 100000,
            "commission": 0.001,
            "slippage": 0.0005,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"].startswith("mbt_")
    assert body["status"] == "success"
    assert body["successful_symbols"] == 1
    assert body["aggregate"]["best_symbol"] == "AAPL"
    assert body["results"][0]["symbol"] == "AAPL"

    read_response = client.get(f"/api/v1/multi-backtests/{body['run_id']}")
    assert read_response.status_code == 200
    assert read_response.json()["run_id"] == body["run_id"]

    list_response = client.get("/api/v1/multi-backtests?limit=5")
    assert list_response.status_code == 200
    assert list_response.json()["runs"][0]["run_id"] == body["run_id"]
