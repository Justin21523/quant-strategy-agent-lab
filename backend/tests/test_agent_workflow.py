from fastapi.testclient import TestClient


def test_backtest_agent_workflow_metadata_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/agent/backtest-workflow")

    assert response.status_code == 200
    body = response.json()
    assert body["workflow_key"] == "backtest_workflow"
    assert body["phase"] == "phase-6"
    assert body["total_steps"] == 8
    assert [step["sequence"] for step in body["steps"]] == list(range(1, 9))
    assert body["steps"][0]["key"] == "strategy_received"
    assert body["steps"][-1]["key"] == "risk_review"
    assert all(step["status"] == "pending" for step in body["steps"])
