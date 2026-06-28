import time

from fastapi.testclient import TestClient


def _wait_for_job(client: TestClient, job_id: str) -> dict:
    deadline = time.time() + 15
    while time.time() < deadline:
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        body = response.json()
        if body["status"] in {"success", "failed", "cancelled"}:
            return body
        time.sleep(0.15)
    raise AssertionError(f"job did not finish: {job_id}")


def test_demo_research_latest_snapshot_and_job(client: TestClient) -> None:
    snapshot = client.get("/api/v1/demo/research/latest")
    assert snapshot.status_code == 200
    snapshot_summary = snapshot.json()["summary"]
    assert snapshot_summary["status"] == "snapshot"
    assert snapshot_summary["events"]
    assert snapshot_summary["quality"]["symbols"]
    assert snapshot_summary["scanner"]["results"]
    assert snapshot_summary["portfolio_matrix"][0]["equity_curve"]
    assert snapshot_summary["portfolio_matrix"][0]["drawdown_curve"]

    queued = client.post("/api/v1/jobs/demo/research/run")
    assert queued.status_code == 200
    job = _wait_for_job(client, queued.json()["job_id"])

    assert job["status"] == "success"
    assert job["kind"] == "research_demo"
    assert job["result_type"] == "research_demo"
    assert job["result_id"].startswith("demo_")

    latest = client.get("/api/v1/demo/research/latest")
    assert latest.status_code == 200
    summary = latest.json()["summary"]
    assert summary["run_id"] == job["result_id"]
    assert summary["universe"]["member_count"] == 20
    assert summary["sync"]["successful"] == 20
    assert summary["quality"]["failed_examples"]
    assert len(summary["quality"]["symbols"]) == 20
    assert summary["scanner"]["matched_symbols"] > 0
    assert summary["scanner"]["results"]
    assert len(summary["portfolio_matrix"]) == 3
    assert summary["portfolio_matrix"][0]["equity_curve"]
    assert summary["portfolio_matrix"][0]["drawdown_curve"]
    assert len(summary["strategy_comparison"]) == 3
    assert summary["events"]
    assert summary["best_portfolio_run_id"]
    assert summary["best_multi_backtest_run_id"]

    read = client.get(f"/api/v1/demo/research/{job['result_id']}")
    assert read.status_code == 200
    assert read.json()["summary"]["run_id"] == job["result_id"]
