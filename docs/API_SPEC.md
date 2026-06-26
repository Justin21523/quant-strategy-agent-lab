# API Specification — Phase 4

All application endpoints are served under `/api/v1`.

The development server uses dynamic ports. Use the URLs printed by `./scripts/dev.sh` or `make dev` rather than assuming backend `8000` or frontend `5173`.

```text
FastAPI: http://127.0.0.1:<backend-port>
Swagger: http://127.0.0.1:<backend-port>/docs
ReDoc: http://127.0.0.1:<backend-port>/redoc
Frontend: http://127.0.0.1:<frontend-port>
Market Data Lab: http://127.0.0.1:<frontend-port>/#/market-data
Strategy Builder: http://127.0.0.1:<frontend-port>/#/strategy-builder
Backtest Lab: http://127.0.0.1:<frontend-port>/#/backtest-lab
```

## System endpoints

### `GET /api/v1/health`

Returns service health, environment, version, and timestamp.

### `GET /api/v1/ready`

Checks runtime readiness, including SQLite connectivity.

### `GET /api/v1/system/info`

Returns current phase metadata, cache stats, template count, and capability states.

Current phase metadata:

```json
{
  "phase": "4",
  "phase_name": "Backtest Engine MVP"
}
```

## Market data endpoints

### `GET /api/v1/market/providers`

Returns configured provider status for CSV, yfinance, and the reserved FinMind boundary.

### `GET /api/v1/market/symbols`

Returns cached symbol metadata. Optional filters:

```text
market
asset_type
```

### `GET /api/v1/market/ohlcv`

Query parameters:

```text
symbol              required
start               optional YYYY-MM-DD
end                 optional YYYY-MM-DD
interval            optional, currently 1d
include_indicators  optional boolean
indicators          optional custom indicator contract
```

Example:

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/market/ohlcv?symbol=AAPL&start=2023-01-03&end=2023-04-10&include_indicators=true'
```

### `POST /api/v1/market/sync`

Synchronizes market data from the selected provider into SQLite cache.

## Indicator endpoints

### `GET /api/v1/market/indicators/catalog`

Returns supported technical-indicator specs and output keys.

Supported indicator families:

```text
SMA
EMA
RSI
MACD
Bollinger Bands
ATR
```

## Strategy endpoints

### `GET /api/v1/strategies/templates`

Returns the five MVP strategy templates:

```text
buy_and_hold
ma_crossover
ma_crossover_rsi
rsi_mean_reversion
macd_trend_following
```

### `GET /api/v1/strategies/templates/{template_id}`

Returns one template with parameter metadata, defaults, notes, and risk notes.

### `POST /api/v1/strategies/templates/{template_id}/render`

Renders typed template parameters into validated Strategy JSON DSL.

### `POST /api/v1/strategies/render`

Alternative render endpoint that accepts `template_id` in the JSON body.

### `POST /api/v1/strategies/validate`

Validates a Strategy JSON DSL document without running it.

## Backtest endpoints

### `POST /api/v1/backtests/run`

Runs one validated Strategy JSON DSL document through the deterministic Phase 4 MVP engine.

Request body:

```json
{
  "strategy_json": {
    "dsl_version": "1.0",
    "strategy_id": "ma_crossover",
    "strategy_name": "SMA 20/60 Crossover",
    "template_id": "ma_crossover",
    "market": "US",
    "symbol": "AAPL",
    "timeframe": "1d",
    "date_range": {"start": "2023-01-03", "end": "2025-12-31"},
    "capital": {"initial_cash": 100000, "commission": 0.001, "slippage": 0.0005},
    "indicators": [
      {"id": "sma_fast", "type": "SMA", "source": "close", "window": 20},
      {"id": "sma_slow", "type": "SMA", "source": "close", "window": 60}
    ],
    "entry_rules": {
      "operator": "AND",
      "conditions": [{"type": "CROSSOVER", "left": "sma_fast", "right": "sma_slow"}]
    },
    "exit_rules": {
      "operator": "OR",
      "conditions": [{"type": "CROSSUNDER", "left": "sma_fast", "right": "sma_slow"}]
    },
    "risk_rules": {"stop_loss_pct": 0.08, "take_profit_pct": 0.2, "max_position_pct": 1.0}
  }
}
```

Response sections:

```text
run_id
created_at
status
strategy_id
strategy_name
symbol
timeframe
assumptions
data
data_source
metrics
equity_curve
drawdown_curve
trades
signals
warnings
agent_steps
```

Important assumptions returned in the response:

```text
signals use completed daily bars only
market entries/exits fill at next bar open
final liquidation uses final close
long_only
max_positions = 1
commission and slippage are explicit inputs
```

Representative metrics:

```text
total_return_pct
annual_return_pct
sharpe_ratio
max_drawdown_pct
win_rate_pct
profit_factor
trade_count
exposure_time_pct
average_trade_return_pct
final_equity
```

## Error format

Domain errors use a structured response:

```json
{
  "error": {
    "code": "strategy_dsl_validation_error",
    "message": "Strategy JSON DSL failed validation and cannot be backtested.",
    "details": {"issues": []}
  }
}
```

Backtest validation errors return HTTP `422`.
