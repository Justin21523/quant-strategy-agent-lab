# API Specification — Phase 9B

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
Agent Workflow: http://127.0.0.1:<frontend-port>/#/agent-workflow
Stock Scanner: http://127.0.0.1:<frontend-port>/#/parameter-scanner
Data Quality: http://127.0.0.1:<frontend-port>/#/data-quality
Multi-Asset Comparison: http://127.0.0.1:<frontend-port>/#/comparison
Performance Report: http://127.0.0.1:<frontend-port>/#/performance-report
Portfolio Rebalance: http://127.0.0.1:<frontend-port>/#/portfolio-rebalance
Jobs: http://127.0.0.1:<frontend-port>/#/jobs
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
  "phase": "9B",
  "phase_name": "In-App Research Demo Automation"
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
```

Example:

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/market/ohlcv?symbol=AAPL&start=2023-01-03&end=2023-04-10&include_indicators=true'
```

### `POST /api/v1/market/sync`

Synchronizes market data from the selected provider into SQLite cache.

### `POST /api/v1/market/batch-sync`

Synchronizes one cursor-based chunk from a universe into the SQLite cache. The default
provider is `yfinance`, the default chunk size is `50`, and CSV fallback is disabled by
default so real-market syncs do not silently mix with synthetic fixture data.

```json
{
  "universe_id": "us_common_stocks",
  "provider": "yfinance",
  "start": "2023-01-03",
  "end": "2025-12-31",
  "chunk_size": 50,
  "cursor": 0,
  "allow_fallback": false,
  "mode": "all"
}
```

The response includes `next_cursor` and `complete` so the client can continue chunking.

Supported `mode` values:

```text
all
missing_or_stale
retry_failed
```

`missing_or_stale` requires `stale_after`. `retry_failed` requires `failed_run_id`, using
a symbol-level sync run id from batch-sync history.

### `GET /api/v1/market/batch-sync/runs`

Lists recent batch-sync runs. Optional query parameters:

```text
universe_id
limit
```

### `GET /api/v1/market/sync-runs`

Lists symbol-level sync records. Optional query parameters:

```text
run_id
limit
```

## Universe endpoints

### `GET /api/v1/universes`

Lists configured market universes.

### `GET /api/v1/universes/{universe_id}`

Returns universe metadata and active members.

### `POST /api/v1/universes/us-common-stocks/refresh`

Refreshes the `us_common_stocks` universe from Nasdaq Trader symbol directory files and
upserts matching symbols into the local catalog.

## Indicator endpoints

### `GET /api/v1/indicators/catalog`

Returns supported technical-indicator families and default parameters.

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

Runs one validated Strategy JSON DSL document through the deterministic backtest engine.

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

## Agent workflow endpoints

### `GET /api/v1/agent/backtest-workflow`

Returns the canonical Phase 6 backtest workflow steps used by the Backtest Lab timeline.

## Scanner endpoints

### `GET /api/v1/scans/capabilities`

Returns default scanner rules and sortable metric keys.

### `GET /api/v1/scans/presets`

Returns built-in scanner presets:

```text
trend_momentum
pullback_in_uptrend
volume_breakout
low_volatility_trend
oversold_watchlist
```

### `GET /api/v1/scans`

Lists recent saved scanner runs.

### `POST /api/v1/scans/run`

Runs the technical scanner against cached OHLCV bars for a universe. The scanner does not
fetch missing bars during scan execution; symbols without enough cached history are skipped.

Default rules:

```text
close > SMA200
SMA20 > SMA60
40 <= RSI14 <= 70
volume / volume_sma20 >= 1.0
60-day return > 0%
```

### `GET /api/v1/scans/{run_id}`

Reads a saved scanner run, ranked result snapshot, and skipped-symbol reasons.

## Data quality endpoints

### `GET /api/v1/data-quality/universes/{universe_id}`

Reports cache quality for universe members in a date range.

Query parameters:

```text
start   required YYYY-MM-DD
end     required YYYY-MM-DD
limit   optional, default 500
```

The response includes member count, covered symbols, coverage percent, fixture-symbol
count, SMA200 readiness, 252D return readiness, and per-symbol warnings.

## Multi-asset backtest endpoints

### `POST /api/v1/multi-backtests/run`

Runs one strategy template across the top N symbols from a saved scanner run.

```json
{
  "scan_run_id": "scan_xxxxxxxxxxxx",
  "template_id": "buy_and_hold",
  "parameters": {},
  "top_n": 10,
  "start": "2023-01-03",
  "end": "2025-12-31",
  "initial_cash": 100000,
  "commission": 0.001,
  "slippage": 0.0005
}
```

### `GET /api/v1/multi-backtests`

Lists recent multi-asset backtest runs.

### `GET /api/v1/multi-backtests/{run_id}`

Reads one saved multi-asset backtest run.

## Portfolio rebalance endpoints

### `GET /api/v1/portfolios/presets`

Lists scanner-to-portfolio presets, including monthly Trend Momentum top 20, monthly Low Volatility Trend top 30, and weekly Oversold Watchlist top 10.

### `POST /api/v1/portfolios/presets`

Saves a portfolio preset with scanner preset/rules plus rebalance configuration.

### `GET /api/v1/portfolios/rebalance`

Lists saved portfolio rebalance runs.

### `GET /api/v1/portfolios/rebalance/{run_id}`

Reads one portfolio rebalance run with performance, benchmark report, equity curve, holdings, rebalance events, and skipped periods.

## Job endpoints

### `POST /api/v1/jobs/market/batch-sync`

Queues a long-running market batch sync job.

### `POST /api/v1/jobs/scans/run`

Queues a scanner run job.

### `POST /api/v1/jobs/portfolios/rebalance/run`

Queues a portfolio rebalance job.

### `POST /api/v1/jobs/demo/research/run`

Queues the deterministic in-app research demo workflow.

### `GET /api/v1/jobs`

Lists recent jobs with status, progress, result IDs, and errors.

### `GET /api/v1/jobs/{job_id}`

Reads one job.

### `GET /api/v1/jobs/{job_id}/events`

Lists progress events for one job.

### `POST /api/v1/jobs/{job_id}/cancel`

Marks a pending or running job as cancelled.

## Research demo endpoints

### `GET /api/v1/demo/research/latest`

Reads the latest completed demo workflow summary, or a built-in sample snapshot if none has run.

### `GET /api/v1/demo/research/{run_id}`

Reads one completed demo workflow summary.

Reads one saved multi-asset run with aggregate metrics and per-symbol ranking.

Backtest assumptions used by single and multi-asset runs:

```text
signals use completed daily bars only
market entries/exits fill at next bar open
final liquidation uses final close
long_only
max_positions = 1
commission and slippage are explicit inputs
```

Representative performance metrics:

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
