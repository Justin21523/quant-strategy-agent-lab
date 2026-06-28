from fastapi.testclient import TestClient


def test_root_metadata(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["phase"] == "phase-9f"
    assert body["version"] == "0.15.0"
    assert body["docs"] == "/docs"
    assert body["market"] == "/api/v1/market/symbols"
    assert body["indicators"] == "/api/v1/indicators/catalog"
    assert body["strategies"] == "/api/v1/strategies/templates"
    assert body["backtests"] == "/api/v1/backtests/run"
    assert body["universes"] == "/api/v1/universes"
    assert body["scans"] == "/api/v1/scans/run"
    assert body["data_quality"] == "/api/v1/data-quality/universes/us_common_stocks"
    assert body["multi_backtests"] == "/api/v1/multi-backtests/run"
    assert body["portfolio_rebalance"] == "/api/v1/portfolios/rebalance"
    assert body["jobs"] == "/api/v1/jobs"
    assert body["demo"] == "/api/v1/demo/research/latest"
    assert body["research"] == "/api/v1/research/runs/latest"
    assert "not investment advice" in body["disclaimer"].lower()


def test_health_and_readiness(client: TestClient) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["phase"] == "phase-9f"
    assert health.json()["version"] == "0.15.0"

    readiness = client.get("/api/v1/ready")
    assert readiness.status_code == 200
    assert readiness.json() == {
        "status": "ready",
        "checks": {"api": "ok", "database": "ok"},
    }


def test_openapi_and_system_info(client: TestClient) -> None:
    openapi = client.get("/api/v1/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    assert "/api/v1/market/symbols" in paths
    assert "/api/v1/market/ohlcv" in paths
    assert "/api/v1/market/sync" in paths
    assert "/api/v1/indicators/catalog" in paths
    assert "/api/v1/strategies/templates" in paths
    assert "/api/v1/strategies/templates" in paths
    assert "/api/v1/strategies/render" in paths
    assert "/api/v1/backtests/run" in paths
    assert "/api/v1/agent/backtest-workflow" in paths
    assert "/api/v1/universes" in paths
    assert "/api/v1/market/batch-sync" in paths
    assert "/api/v1/market/batch-sync/runs" in paths
    assert "/api/v1/scans/run" in paths
    assert "/api/v1/scans/presets" in paths
    assert "/api/v1/data-quality/universes/{universe_id}" in paths
    assert "/api/v1/multi-backtests/run" in paths
    assert "/api/v1/portfolios/rebalance" in paths
    assert "/api/v1/portfolios/rebalance/{run_id}" in paths
    assert "/api/v1/portfolios/presets" in paths
    assert "/api/v1/jobs" in paths
    assert "/api/v1/jobs/{job_id}" in paths
    assert "/api/v1/jobs/{job_id}/events" in paths
    assert "/api/v1/jobs/portfolios/rebalance/run" in paths
    assert "/api/v1/jobs/demo/research/run" in paths
    assert "/api/v1/jobs/research/pipeline/run" in paths
    assert "/api/v1/demo/research/latest" in paths
    assert "/api/v1/demo/research/{run_id}" in paths
    assert "/api/v1/research/runs/latest" in paths
    assert "/api/v1/research/runs" in paths
    assert "/api/v1/research/runs/{run_id}" in paths
    assert "/api/v1/research/presets" in paths
    assert "/api/v1/research/presets/{preset_id}" in paths
    assert "/api/v1/research/runs/{run_id}/report" in paths
    assert "/api/v1/research/runs/{run_id}/export" in paths

    info = client.get("/api/v1/system/info")
    assert info.status_code == 200
    assert info.json()["phase_name"] == "Guided Site Onboarding"
    body = info.json()
    assert any(item["key"] == "sqlite_cache" for item in body["capabilities"])
    assert any(
        item["key"] == "indicator_engine" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "strategy_template_system" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "backtest_engine" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "agent_timeline" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "market_universes" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "stock_scanner" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "data_quality_report" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "multi_asset_backtest" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "portfolio_rebalance" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "performance_analyzer" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "portfolio_presets" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "job_queue" and item["status"] == "ready" for item in body["capabilities"]
    )
    assert any(
        item["key"] == "quality_gates" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "research_demo_automation" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "demo_studio" and item["status"] == "ready" for item in body["capabilities"]
    )
    assert any(
        item["key"] == "research_pipeline" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "research_presets" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "research_report_exports" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert any(
        item["key"] == "site_guide" and item["status"] == "ready" for item in body["capabilities"]
    )
    assert body["strategy_templates"] == 5
    assert body["cache"] == {"symbols": 22, "bars": 16408, "sync_records": 0}
