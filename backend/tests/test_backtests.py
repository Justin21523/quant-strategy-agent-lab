from fastapi.testclient import TestClient


def _render_strategy(client: TestClient, template_id: str, parameters: dict | None = None) -> dict:
    response = client.post(
        f"/api/v1/strategies/templates/{template_id}/render",
        json={
            "symbol": "AAPL",
            "market": "US",
            "timeframe": "1d",
            "start": "2023-01-03",
            "end": "2025-12-31",
            "initial_cash": 100000,
            "commission": 0.001,
            "slippage": 0.0005,
            "parameters": parameters or {},
        },
    )
    assert response.status_code == 200
    return response.json()["strategy_json"]


def test_backtest_engine_runs_ma_crossover_strategy(client: TestClient) -> None:
    strategy = _render_strategy(client, "ma_crossover")

    response = client.post("/api/v1/backtests/run", json={"strategy_json": strategy})

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"].startswith("bt_")
    assert body["strategy_id"] == "ma_crossover"
    assert body["symbol"] == "AAPL"
    assert body["data_source"]["bar_count"] == 782
    assert body["data_source"]["provider"] == ["csv"]
    assert body["metrics"]["trade_count"] >= 1
    assert body["metrics"]["total_return_pct"] != 0
    assert body["metrics"]["max_drawdown_pct"] <= 0
    assert len(body["equity_curve"]) == body["data_source"]["bar_count"]
    assert len(body["drawdown_curve"]) == body["data_source"]["bar_count"]
    trade_id = body["trades"][0]["trade_id"]
    assert (isinstance(trade_id, str) and trade_id.startswith("trade_")) or trade_id >= 1
    assert body["trades"][0].get("legacy_trade_id", body["trades"][0]["trade_id"])
    assert body["trades"][0]["side"] == "long"
    assert body["signals"][0]["date"]
    assert body["agent_steps"][0]["key"] == "validate_strategy"
    assert any(step["key"] == "run_backtest" for step in body["agent_steps"])
    assert any(warning["code"] == "synthetic_fixture_data" for warning in body["warnings"])


def test_backtest_engine_runs_buy_and_hold_and_forces_final_liquidation(
    client: TestClient,
) -> None:
    strategy = _render_strategy(client, "buy_and_hold")

    response = client.post("/api/v1/backtests/run", json={"strategy_json": strategy})

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_id"] == "buy_and_hold"
    assert body["metrics"]["trade_count"] == 1
    assert body["trades"][0]["exit_reason"] in {"EXIT_ON_LAST_BAR", "final_bar_liquidation"}
    assert body["assumptions"]["forced_final_liquidation"]


def test_backtest_engine_supports_macd_template(client: TestClient) -> None:
    strategy = _render_strategy(client, "macd_trend_following")

    response = client.post("/api/v1/backtests/run", json={"strategy_json": strategy})

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_id"] == "macd_trend_following"
    assert body["metrics"]["trade_count"] >= 0
    assert len(body["equity_curve"]) == body["data_source"]["bar_count"]


def test_backtest_engine_rejects_invalid_strategy_dsl(client: TestClient) -> None:
    strategy = _render_strategy(client, "ma_crossover")
    strategy["entry_rules"]["conditions"][0]["left"] = "does_not_exist"

    response = client.post("/api/v1/backtests/run", json={"strategy_json": strategy})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "strategy_dsl_validation_error"
    assert body["error"]["details"]["issues"]
