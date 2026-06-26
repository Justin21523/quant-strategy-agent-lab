# Quant Strategy Agent Lab

A local-first quantitative strategy research workbench built with **Python, FastAPI, SQLite, pandas, HTML, CSS, and modular Vanilla JavaScript**.

> Educational and research use only. This application does not provide investment advice. Historical data, indicators, strategy templates, and backtest results cannot guarantee future performance.

## Current status

**Phase 4 — Backtest Engine MVP is implemented.**

The application now provides:

- a normalized OHLCV market-data layer from Phase 1;
- deterministic offline CSV fixtures for `AAPL`, `SPY`, and `QQQ`;
- SQLite market-data cache and provider lineage;
- on-demand technical indicators from cached bars from Phase 2:
  - SMA;
  - EMA;
  - RSI;
  - MACD;
  - Bollinger Bands;
  - ATR;
- five deterministic strategy templates from Phase 3:
  - Buy and Hold;
  - MA Crossover;
  - MA Crossover + RSI Filter;
  - RSI Mean Reversion;
  - MACD Trend Following;
- Strategy JSON DSL `1.0` rendering and validation;
- a deterministic long-only backtest engine that consumes validated Strategy JSON DSL;
- signal generation for entry and exit rule groups;
- next-open fills for normal signals, explicit fees and slippage, forced final-bar liquidation, and a closed trade ledger;
- total return, annualized return, Sharpe ratio, max drawdown, win rate, profit factor, exposure time, average trade return, and final equity;
- equity curve, drawdown curve, signal timeline, warnings, and Agent-style execution steps;
- a minimal Vanilla JS Backtest Lab route for running one strategy against one cached asset;
- dynamic dev-server ports through `./scripts/dev.sh` / `make dev`.

Phase 4 intentionally uses a small in-house deterministic MVP engine instead of depending on `backtesting.py` or `vectorbt` immediately. This keeps the execution assumptions visible, testable, and easy to inspect before a later adapter layer is added.

## Tech stack

### Backend

- Python 3.11+
- FastAPI
- Pydantic
- pandas
- SQLite via Python `sqlite3`
- deterministic CSV provider
- yfinance adapter boundary
- reserved FinMind adapter boundary

### Frontend

- HTML
- CSS
- Vanilla JavaScript
- ES Modules
- Fetch API
- Native DOM API
- Native SVG charts
- Vite as development/build tooling only

No React, Vue, Angular, Svelte, or frontend framework is used.

## Start on Linux

```bash
cp .env.example .env 2>/dev/null || true
./scripts/bootstrap.sh
./scripts/dev.sh
```

or:

```bash
make bootstrap
make dev
```

The dev servers use **dynamic ports**. Do not assume Backend is `8000` or Frontend is `5173`. Use the URLs printed by `./scripts/dev.sh` / `make dev`, for example:

```text
FastAPI: http://127.0.0.1:<backend-port>
Swagger: http://127.0.0.1:<backend-port>/docs
ReDoc: http://127.0.0.1:<backend-port>/redoc
Frontend: http://127.0.0.1:<frontend-port>
Market Data Lab: http://127.0.0.1:<frontend-port>/#/market-data
Strategy Builder: http://127.0.0.1:<frontend-port>/#/strategy-builder
Backtest Lab: http://127.0.0.1:<frontend-port>/#/backtest-lab
```

When testing the Vite API proxy, use the printed **Frontend** port:

```bash
curl 'http://127.0.0.1:<frontend-port>/api/v1/backtests/run'
```

## Phase 4 API examples

### Health

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/health'
```

### Strategy template catalog

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/strategies/templates'
```

### Render a strategy template

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/strategies/templates/ma_crossover_rsi/render' \
  -H 'Content-Type: application/json' \
  -d '{
    "symbol": "AAPL",
    "market": "US",
    "timeframe": "1d",
    "start": "2023-01-03",
    "end": "2025-12-31",
    "parameters": {
      "fast_window": 20,
      "slow_window": 60,
      "rsi_window": 14,
      "rsi_entry_max": 70,
      "rsi_exit_min": 80,
      "source": "close",
      "stop_loss_pct": 0.08,
      "take_profit_pct": 0.2,
      "max_position_pct": 1.0
    }
  }'
```

### Run a backtest

Render a strategy first, then send the returned `strategy_json` to:

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/backtests/run' \
  -H 'Content-Type: application/json' \
  -d '{
    "strategy_json": {
      "dsl_version": "1.0",
      "strategy_id": "buy_and_hold",
      "strategy_name": "Buy and Hold",
      "template_id": "buy_and_hold",
      "market": "US",
      "symbol": "AAPL",
      "timeframe": "1d",
      "date_range": {"start": "2023-01-03", "end": "2025-12-31"},
      "capital": {"initial_cash": 100000, "commission": 0.001, "slippage": 0.0005},
      "indicators": [],
      "entry_rules": {"operator": "AND", "conditions": [{"type": "ENTER_ON_FIRST_BAR"}]},
      "exit_rules": {"operator": "OR", "conditions": [{"type": "EXIT_ON_LAST_BAR"}]},
      "risk_rules": {"stop_loss_pct": 0, "take_profit_pct": 0, "max_position_pct": 1.0}
    }
  }'
```

The response includes:

```text
run_id
assumptions
data_source
metrics
equity_curve
drawdown_curve
trades
signals
warnings
agent_steps
```

### OHLCV with indicators still works

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/market/ohlcv?symbol=AAPL&start=2023-01-03&end=2023-04-10&include_indicators=true'
```

## Quality checks

```bash
make check
```

This runs:

- Ruff lint and format check;
- backend Pytest suite with coverage;
- frontend ESLint;
- frontend Prettier check;
- frontend Node tests;
- Vite production build.

Current Phase 4 validation result:

```text
Backend tests: 35 passed
Backend coverage: 89.01%
Frontend tests: 5 passed
Vite production build: passed
Runtime smoke test: passed through dynamic backend/frontend ports
```

## Project structure

```text
backend/app/
├── api/                  FastAPI routes and error handling
├── core/                 settings, logging, dependency container
├── database/             SQLite schema
├── domain/               provider-neutral market, indicator, strategy, and backtest models
├── providers/            CSV, yfinance, and FinMind adapter boundaries
├── repositories/         SQLite persistence
├── schemas/              Pydantic response/request contracts
└── services/             market data, normalization, indicators, strategy templates, backtesting

frontend/src/
├── charts/               native SVG price, indicator, equity, and drawdown previews
├── components/           reusable Vanilla JS UI functions
├── core/                 router, API client, store, event bus, DOM helper
├── layouts/              shell, sidebar, topbar, status bar
├── pages/                dashboard, Market Data Lab, Strategy Builder, Backtest Lab
├── services/             API service wrappers
├── styles/               modular CSS
└── utils/                formatting helpers
```

## Data boundary

Bundled CSV rows are deterministic synthetic fixtures for engineering tests and offline demos. They are not live, current, or observed market data. API responses explicitly mark fixture rows through warnings such as `synthetic_fixture_data`.

## Backtest execution boundary

Phase 4 does not generate trading advice. The MVP engine uses deterministic assumptions:

- daily bars only;
- long-only, one position at a time;
- strategy rules are evaluated on completed bars;
- normal entries and exits fill at the next bar open;
- Buy and Hold may enter at the first bar open;
- open positions are liquidated at the final close;
- commission and slippage are explicit inputs;
- historical backtests cannot guarantee future performance.

## Roadmap

Completed:

- Phase 0: project foundation;
- Phase 1: market data layer;
- Phase 2: indicator engine;
- Phase 3: strategy template system;
- Phase 4: backtest engine MVP.

Next:

- Phase 5: Backtest Lab frontend polish;
- Phase 6: Agent Timeline MVP;
- Phase 7: performance analyzer expansion.

## Key docs

- [Phase 4 acceptance record](docs/PHASE_4_ACCEPTANCE.md)
- [Backtest Engine design](docs/BACKTEST_ENGINE.md)
- [API specification](docs/API_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Strategy Template System design](docs/STRATEGY_TEMPLATE_SYSTEM.md)
- [Strategy DSL](docs/STRATEGY_DSL.md)
- [Indicator Engine design](docs/INDICATOR_ENGINE.md)
- [Data pipeline](docs/DATA_PIPELINE.md)
- [Frontend architecture](docs/FRONTEND_ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
