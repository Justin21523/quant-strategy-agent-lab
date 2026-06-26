from fastapi.testclient import TestClient


def test_root_metadata(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["phase"] == "phase-3"
    assert body["version"] == "0.4.0"
    assert body["docs"] == "/docs"
    assert body["market"] == "/api/v1/market/symbols"
    assert body["indicators"] == "/api/v1/indicators/catalog"
    assert body["strategies"] == "/api/v1/strategies/templates"
    assert body["strategies"] == "/api/v1/strategies/templates"
    assert "not investment advice" in body["disclaimer"].lower()


def test_health_and_readiness(client: TestClient) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["phase"] == "phase-3"
    assert health.json()["version"] == "0.4.0"

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

    info = client.get("/api/v1/system/info")
    assert info.status_code == 200
    assert info.json()["phase_name"] == "Strategy Template System"
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
        item["key"] == "strategy_template_system" and item["status"] == "ready"
        for item in body["capabilities"]
    )
    assert body["strategy_templates"] == 5
    assert body["cache"] == {"symbols": 3, "bars": 2346, "sync_records": 0}
