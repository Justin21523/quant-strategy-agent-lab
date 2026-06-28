import time

from fastapi.testclient import TestClient

from tests.test_scanner import seed_universe


def _wait_for_job(client: TestClient, job_id: str) -> dict:
    deadline = time.time() + 5
    while time.time() < deadline:
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        body = response.json()
        if body["status"] in {"success", "failed", "cancelled"}:
            return body
        time.sleep(0.1)
    raise AssertionError(f"job did not finish: {job_id}")


def _scan_payload() -> dict:
    return {
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
        "quality_gate": {
            "min_bars": 200,
            "allow_fixture_data": True,
            "max_missing_weekdays": 1000,
        },
        "result_limit": 10,
    }


def test_scanner_quality_gate_and_scan_job(client: TestClient) -> None:
    seed_universe(client)

    response = client.post("/api/v1/jobs/scans/run", json=_scan_payload())
    assert response.status_code == 200
    job = _wait_for_job(client, response.json()["job_id"])

    assert job["status"] == "success"
    assert job["result_type"] == "scan"
    scan = client.get(f"/api/v1/scans/{job['result_id']}")
    assert scan.status_code == 200
    assert scan.json()["results"][0]["symbol"] == "AAPL"


def test_portfolio_presets_and_fixed_scan_run_job(client: TestClient) -> None:
    seed_universe(client)
    scan = client.post("/api/v1/scans/run", json=_scan_payload())
    assert scan.status_code == 200
    scan_id = scan.json()["run_id"]

    presets = client.get("/api/v1/portfolios/presets")
    assert presets.status_code == 200
    assert {
        "trend_momentum_monthly_top20",
        "oversold_watchlist_weekly_top10",
    } <= {item["preset_id"] for item in presets.json()["presets"]}

    response = client.post(
        "/api/v1/jobs/portfolios/rebalance/run",
        json={
            "selection_mode": "fixed_scan_run",
            "universe_id": "us_common_stocks",
            "fixed_scan_run_id": scan_id,
            "top_n": 1,
            "frequency": "monthly",
            "start": "2023-01-03",
            "end": "2023-06-30",
            "lookback_days": 365,
            "initial_cash": 100000,
            "commission": 0.001,
            "slippage": 0.0005,
            "benchmark_symbol": "SPY",
            "quality_gate": {
                "min_bars": 0,
                "allow_fixture_data": True,
                "max_missing_weekdays": 1000,
            },
        },
    )
    assert response.status_code == 200
    job = _wait_for_job(client, response.json()["job_id"])

    assert job["status"] == "success"
    assert job["result_type"] == "portfolio_rebalance"
    run = client.get(f"/api/v1/portfolios/rebalance/{job['result_id']}")
    assert run.status_code == 200
    body = run.json()
    assert body["selection_mode"] == "fixed_scan_run"
    assert body["aggregate"]["rebalance_count"] >= 1
    assert (
        body["performance"]["sortino_ratio"] is not None
        or body["performance"]["sharpe_ratio"] is not None
    )
    assert body["benchmark"]["total_return_pct"] is not None
    assert body["rebalance_events"][0]["selected_symbols"] == ["AAPL"]

    listed = client.get("/api/v1/portfolios/rebalance?limit=5")
    assert listed.status_code == 200
    assert listed.json()["runs"][0]["run_id"] == body["run_id"]

    events = client.get(f"/api/v1/jobs/{job['job_id']}/events")
    assert events.status_code == 200
    assert events.json()["total"] >= 2
