import time

from fastapi.testclient import TestClient


def _wait_for_job(client: TestClient, job_id: str) -> dict:
    deadline = time.time() + 20
    while time.time() < deadline:
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        body = response.json()
        if body["status"] in {"success", "failed", "cancelled"}:
            return body
        time.sleep(0.15)
    raise AssertionError(f"job did not finish: {job_id}")


def test_configurable_research_pipeline_job_and_read_endpoints(client: TestClient) -> None:
    response = client.post(
        "/api/v1/jobs/research/pipeline/run",
        json={
            "run_label": "Test Pipeline",
            "universe_id": "demo_research_sample",
            "start": "2023-01-03",
            "end": "2025-12-31",
            "provider": "csv",
            "sync_mode": "all",
            "sync_chunk_size": 25,
            "benchmark_symbol": "SPY",
            "quality_gate": {
                "min_bars": 120,
                "allow_fixture_data": True,
                "max_missing_weekdays": 1000,
            },
            "scanner_config": {
                "preset_id": "trend_momentum",
                "sort_key": "return_60d_pct",
                "sort_direction": "desc",
                "result_limit": 12,
            },
            "portfolio_matrix_configs": [
                {
                    "label": "Trend Momentum Monthly Top 3",
                    "scanner_preset_id": "trend_momentum",
                    "frequency": "monthly",
                    "top_n": 3,
                    "lookback_days": 365,
                    "start": "2023-01-03",
                    "end": "2023-06-30",
                }
            ],
            "strategy_matrix_configs": [
                {
                    "template_id": "buy_and_hold",
                    "top_n": 3,
                    "start": "2023-01-03",
                    "end": "2023-06-30",
                }
            ],
        },
    )
    assert response.status_code == 200
    job = _wait_for_job(client, response.json()["job_id"])

    assert job["status"] == "success"
    assert job["kind"] == "research_pipeline"
    assert job["result_type"] == "research_pipeline"
    assert job["result_id"].startswith("rp_")

    latest = client.get("/api/v1/research/runs/latest")
    assert latest.status_code == 200
    summary = latest.json()["summary"]
    assert summary["run_id"] == job["result_id"]
    assert summary["run_label"] == "Test Pipeline"
    assert summary["sync"]["successful"] == 20
    assert summary["quality"]["symbols"]
    assert summary["scanner"]["results"]
    assert summary["portfolio_matrix"][0]["equity_curve"]
    assert summary["strategy_comparison"][0]["template_id"] == "buy_and_hold"
    assert summary["events"]

    listed = client.get("/api/v1/research/runs?limit=5")
    assert listed.status_code == 200
    assert listed.json()["runs"][0]["run_id"] == job["result_id"]

    read = client.get(f"/api/v1/research/runs/{job['result_id']}")
    assert read.status_code == 200
    assert read.json()["summary"]["run_id"] == job["result_id"]

    report = client.get(f"/api/v1/research/runs/{job['result_id']}/report")
    assert report.status_code == 200
    assert "# Test Pipeline" in report.text
    assert "## Portfolio Matrix" in report.text

    summary_export = client.get(
        f"/api/v1/research/runs/{job['result_id']}/export?artifact=summary&format=json"
    )
    assert summary_export.status_code == 200
    assert summary_export.json()["run_id"] == job["result_id"]

    scanner_csv = client.get(
        f"/api/v1/research/runs/{job['result_id']}/export?artifact=scanner&format=csv"
    )
    assert scanner_csv.status_code == 200
    assert "symbol" in scanner_csv.text


def test_research_presets_can_be_saved_listed_and_read(client: TestClient) -> None:
    listed = client.get("/api/v1/research/presets")
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    payload = {
        "preset_id": "test_research_preset",
        "name": "Test Research Preset",
        "description": "Saved by tests.",
        "config": {
            "run_label": "Preset Pipeline",
            "universe_id": "demo_research_sample",
            "start": "2023-01-03",
            "end": "2025-12-31",
            "provider": "csv",
            "quality_gate": {
                "min_bars": 120,
                "allow_fixture_data": True,
                "max_missing_weekdays": 1000,
            },
            "scanner_config": {
                "preset_id": "trend_momentum",
                "sort_key": "return_60d_pct",
                "sort_direction": "desc",
                "result_limit": 8,
            },
            "portfolio_matrix_configs": [],
            "strategy_matrix_configs": [],
        },
    }
    saved = client.post("/api/v1/research/presets", json=payload)
    assert saved.status_code == 200
    assert saved.json()["preset_id"] == "test_research_preset"
    assert saved.json()["config"]["run_label"] == "Preset Pipeline"

    read = client.get("/api/v1/research/presets/test_research_preset")
    assert read.status_code == 200
    assert read.json()["name"] == "Test Research Preset"
