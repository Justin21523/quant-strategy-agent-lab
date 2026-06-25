"""Phase 0 API contract tests."""

from fastapi.testclient import TestClient


def test_root_exposes_metadata(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] == "0-foundation"
    assert payload["docs"] == "/docs"
    assert payload["health"] == "/api/v1/health"


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Quant Strategy Agent Lab API"
    assert payload["version"] == "0.1.0"
    assert "timestamp" in payload


def test_system_info_reports_ready_and_planned_capabilities(client: TestClient) -> None:
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    payload = response.json()
    statuses = {item["key"]: item["status"] for item in payload["capabilities"]}
    assert payload["phase"] == "0"
    assert statuses["frontend_shell"] == "ready"
    assert statuses["market_data"] == "planned"


def test_openapi_schema_is_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Quant Strategy Agent Lab API"
    assert "/api/v1/health" in schema["paths"]
