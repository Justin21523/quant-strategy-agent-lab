# Quant Strategy Agent Lab

A local-first quantitative strategy research workbench built with **Python, FastAPI, SQLite, pandas, HTML, CSS, and modular Vanilla JavaScript**.

> Educational and research use only. This application does not provide investment advice. Historical data, indicators, strategy templates, and future backtest results cannot guarantee future performance.

## Current status

**Phase 3 — Strategy Template System is implemented.**

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
- five deterministic strategy templates:
  - Buy and Hold;
  - MA Crossover;
  - MA Crossover + RSI Filter;
  - RSI Mean Reversion;
  - MACD Trend Following;
- Strategy JSON DSL `1.0` rendering from typed template parameters;
- backend Strategy DSL validation for references, rule groups, capital assumptions, and risk limits;
- a Vanilla JS Strategy Builder with template cards, parameter controls, validation messages, and JSON preview;
- dynamic dev-server ports through `./scripts/dev.sh` / `make dev`.

The implementation follows the project roadmap: Phase 1 made data inspectable, Phase 2 made features computable, and Phase 3 turns those features into controlled strategy definitions that Phase 4 can execute.

## Tech stack

### Backend

- Python 3.11+
- FastAPI
- Pydantic
- pandas
- SQLite via Python `sqlite3`
- yfinance adapter boundary
- deterministic CSV provider

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
```

When testing the Vite API proxy, use the printed **Frontend** port:

```bash
curl 'http://127.0.0.1:<frontend-port>/api/v1/strategies/templates'
```

## Phase 3 API examples

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

### Validate a Strategy JSON document

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/strategies/validate' \
  -H 'Content-Type: application/json' \
  -d '{"strategy_json": {"dsl_version": "1.0"}}'
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

Current Phase 3 validation result:

```text
Backend tests: 31 passed
Backend coverage: 89.09%
Frontend tests: 4 passed
Vite production build: passed
Runtime smoke test: passed through dynamic backend/frontend ports
```

## Project structure

```text
backend/app/
├── api/                  FastAPI routes and error handling
├── core/                 settings, logging, dependency container
├── database/             SQLite schema
├── domain/               provider-neutral market, indicator, and strategy models
├── providers/            CSV, yfinance, and FinMind adapter boundaries
├── repositories/         SQLite persistence
├── schemas/              Pydantic response/request contracts
└── services/             market data, normalization, indicators, strategy templates

frontend/src/
├── charts/               native SVG price and indicator previews
├── components/           reusable Vanilla JS UI functions
├── core/                 router, API client, store, event bus, DOM helper
├── layouts/              shell, sidebar, topbar, status bar
├── pages/                dashboard, Market Data Lab, Strategy Builder
├── services/             API service wrappers
├── styles/               modular CSS
└── utils/                formatting helpers
```

## Data boundary

Bundled CSV rows are deterministic synthetic fixtures for engineering tests and offline demos. They are not live, current, or observed market data. API responses explicitly mark fixture rows through:

```json
{
  "source": {
    "contains_fixture_data": true
  },
  "warnings": [
    {
      "code": "synthetic_fixture_data"
    }
  ]
}
```

## Strategy safety boundary

Phase 3 templates produce declarative JSON only. They do not execute code, generate Python, or make trading recommendations. The Strategy JSON DSL is a controlled contract for later signal generation and backtesting.

## Roadmap

Completed:

- Phase 0: project foundation;
- Phase 1: market data layer;
- Phase 2: indicator engine;
- Phase 3: strategy template system.

Next:

- Phase 4: backtest engine MVP;
- Phase 5: Backtest Lab frontend;
- Phase 6: Agent Timeline MVP.

## Key docs

- [Phase 3 acceptance record](docs/PHASE_3_ACCEPTANCE.md)
- [Strategy Template System design](docs/STRATEGY_TEMPLATE_SYSTEM.md)
- [Phase 2 acceptance record](docs/PHASE_2_ACCEPTANCE.md)
- [Indicator Engine design](docs/INDICATOR_ENGINE.md)
- [API specification](docs/API_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data pipeline](docs/DATA_PIPELINE.md)
- [Frontend architecture](docs/FRONTEND_ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Strategy DSL](docs/STRATEGY_DSL.md)
