from fastapi.testclient import TestClient


def test_strategy_template_catalog_contains_phase_3_mvp_templates(client: TestClient) -> None:
    response = client.get("/api/v1/strategies/templates")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    template_ids = {item["id"] for item in body["templates"]}
    assert template_ids == {
        "buy_and_hold",
        "ma_crossover",
        "ma_crossover_rsi",
        "rsi_mean_reversion",
        "macd_trend_following",
    }
    ma_rsi = next(item for item in body["templates"] if item["id"] == "ma_crossover_rsi")
    assert ma_rsi["indicator_kinds"] == ["SMA", "RSI"]
    assert any(parameter["key"] == "fast_window" for parameter in ma_rsi["parameters"])


def test_render_ma_crossover_rsi_template_to_strategy_dsl(client: TestClient) -> None:
    response = client.post(
        "/api/v1/strategies/templates/ma_crossover_rsi/render",
        json={
            "symbol": "AAPL",
            "market": "US",
            "timeframe": "1d",
            "start": "2023-01-03",
            "end": "2025-12-31",
            "initial_cash": 100000,
            "commission": 0.001,
            "slippage": 0.0005,
            "parameters": {
                "fast_window": 10,
                "slow_window": 40,
                "rsi_window": 14,
                "rsi_entry_max": 65,
                "rsi_exit_min": 78,
                "source": "close",
                "stop_loss_pct": 0.05,
                "take_profit_pct": 0.2,
                "max_position_pct": 1.0,
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["validation"]["valid"] is True
    strategy = body["strategy_json"]
    assert strategy["dsl_version"] == "1.0"
    assert strategy["strategy_id"] == "ma_crossover_rsi"
    assert strategy["symbol"] == "AAPL"
    assert [item["id"] for item in strategy["indicators"]] == ["sma_fast", "sma_slow", "rsi"]
    assert strategy["entry_rules"]["operator"] == "AND"
    assert strategy["risk_rules"]["stop_loss_pct"] == 0.05
    assert body["required_indicators"] == ["sma_fast", "sma_slow", "rsi"]


def test_template_parameter_validation_is_structured(client: TestClient) -> None:
    response = client.post(
        "/api/v1/strategies/templates/ma_crossover/render",
        json={"parameters": {"fast_window": 80, "slow_window": 20}},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "strategy_template_validation_error"
    assert "Fast window" in body["error"]["message"]


def test_strategy_document_validation_catches_unknown_references(client: TestClient) -> None:
    render_response = client.post("/api/v1/strategies/templates/ma_crossover/render", json={})
    strategy = render_response.json()["strategy_json"]
    strategy["entry_rules"]["conditions"][0]["left"] = "does_not_exist"

    response = client.post("/api/v1/strategies/validate", json={"strategy_json": strategy})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert any(issue["code"] == "unknown_rule_reference" for issue in body["issues"])


def test_unknown_strategy_template_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/strategies/templates/not_real")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "strategy_template_not_found"
