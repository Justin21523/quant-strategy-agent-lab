# Quant Strategy Agent Lab

A local-first quantitative strategy research workbench built with **Python, FastAPI, SQLite, pandas, HTML, CSS, and modular Vanilla JavaScript**.

> Educational and research use only. This application does not provide investment advice. Historical data, indicators, strategy templates, and backtest results cannot guarantee future performance.

## Current status

**Phase 9F — Guided static showcase and research demo automation are implemented.**

The application now provides:

- a normalized OHLCV market-data layer from Phase 1;
- deterministic offline CSV fixtures for `AAPL`, `SPY`, `QQQ`, and a 20-stock synthetic sample universe;
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
- an interactive Vanilla JS Backtest Lab with candlestick markers and Agent timeline state;
- a canonical Agent Workflow route backed by `/api/v1/agent/backtest-workflow`;
- a US common-stock universe sourced from Nasdaq Trader symbol directory files;
- chunked universe synchronization for yfinance-backed OHLCV caching;
- an operational Stock Scanner with presets, toggleable rules, saved-run reload, sortable metrics, and skipped-symbol reasons;
- batch-sync history, failed-symbol retry, and missing/stale-symbol sync modes;
- a universe Data Quality report for cache coverage, missing weekdays, fixture flags, and SMA200/252D readiness;
- a scanner-driven Multi-Asset Backtest workflow that ranks top scanner candidates with one strategy template;
- equal-weight Portfolio Rebalance runs with weekly/monthly cadence, turnover, skipped periods, holdings, and equity curves;
- a richer Performance Analyzer with CAGR, annual volatility, Sharpe, Sortino, Calmar, rolling drawdown, monthly returns, and SPY benchmark comparison;
- Scanner to Portfolio preset workflows for Trend Momentum, Low Volatility Trend, and Oversold Watchlist strategies;
- a SQLite-backed job queue for long-running batch sync, scanner, and portfolio jobs with progress events;
- reusable data-quality gates integrated into Scanner and Portfolio workflows;
- an in-app automated research demo that can queue a full sample workflow and tour the website;
- a 15-step site guide with spotlight masks, particle effects, routed navigation, and a bottom-right guide card;
- a GitHub Pages static demo mode backed by deterministic fixture snapshots;
- Playwright showcase capture for screenshots, guide demo video, poster, trace, and HTML report;
- dynamic dev-server ports through `./scripts/dev.sh` / `make dev`.

The backtest engine intentionally uses a small in-house deterministic MVP instead of depending on `backtesting.py` or `vectorbt` immediately. This keeps the execution assumptions visible, testable, and easy to inspect before a later adapter layer is added.

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

## Public static demo

The public GitHub Pages deployment runs the frontend in static demo mode:

```bash
cd frontend
npm run build:pages
npm run showcase:capture
```

`VITE_STATIC_DEMO=true` routes the frontend API client to deterministic fixture snapshots under `frontend/public/demo-data/`. This keeps the public demo fully static while the local development workflow still uses FastAPI, SQLite, and the normal `/api/v1` contract.

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
Agent Workflow: http://127.0.0.1:<frontend-port>/#/agent-workflow
Stock Scanner: http://127.0.0.1:<frontend-port>/#/parameter-scanner
Data Quality: http://127.0.0.1:<frontend-port>/#/data-quality
Multi-Asset Comparison: http://127.0.0.1:<frontend-port>/#/comparison
Performance Report: http://127.0.0.1:<frontend-port>/#/performance-report
Portfolio Rebalance: http://127.0.0.1:<frontend-port>/#/portfolio-rebalance
Jobs: http://127.0.0.1:<frontend-port>/#/jobs
```

When testing the Vite API proxy, use the printed **Frontend** port:

```bash
curl 'http://127.0.0.1:<frontend-port>/api/v1/backtests/run'
```

## Phase 9B API examples

### Health

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/health'
```

### Strategy template catalog

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/strategies/templates'
```

### Indicator catalog

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/indicators/catalog'
```

### Agent workflow metadata

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/agent/backtest-workflow'
```

### Refresh US common-stock universe

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/universes/us-common-stocks/refresh'
```

### Queue a portfolio rebalance job

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/jobs/portfolios/rebalance/run' \
  -H 'content-type: application/json' \
  -d '{"selection_mode":"rescan_each_period","scanner_preset_id":"trend_momentum","frequency":"monthly","top_n":20,"start":"2024-01-02","end":"2025-12-31","quality_gate":{"min_bars":252,"allow_fixture_data":true}}'
```

### Poll jobs

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/jobs'
```

### Run the in-app research demo workflow

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/jobs/demo/research/run'
curl 'http://127.0.0.1:<backend-port>/api/v1/demo/research/latest'
```

### Read portfolio presets and runs

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/portfolios/presets'
curl 'http://127.0.0.1:<backend-port>/api/v1/portfolios/rebalance'
```

### Sync one universe chunk

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/market/batch-sync' \
  -H 'Content-Type: application/json' \
  -d '{
    "universe_id": "us_common_stocks",
    "provider": "yfinance",
    "start": "2023-01-03",
    "end": "2025-12-31",
    "chunk_size": 50,
    "cursor": 0,
    "allow_fallback": false
  }'
```

Sync only missing or stale symbols:

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/market/batch-sync' \
  -H 'Content-Type: application/json' \
  -d '{
    "universe_id": "us_common_stocks",
    "provider": "yfinance",
    "start": "2023-01-03",
    "end": "2025-12-31",
    "chunk_size": 50,
    "cursor": 0,
    "mode": "missing_or_stale",
    "stale_after": "2025-01-01"
  }'
```

### Run the Stock Scanner

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/scans/run' \
  -H 'Content-Type: application/json' \
  -d '{
    "universe_id": "us_common_stocks",
    "start": "2023-01-03",
    "end": "2025-12-31",
    "result_limit": 100
  }'
```

### Read scanner presets and saved runs

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/scans/presets'
curl 'http://127.0.0.1:<backend-port>/api/v1/scans?limit=20'
```

### Run a data-quality report

```bash
curl 'http://127.0.0.1:<backend-port>/api/v1/data-quality/universes/us_common_stocks?start=2023-01-03&end=2025-12-31&limit=500'
```

### Run a multi-asset backtest from a scan run

```bash
curl -X POST 'http://127.0.0.1:<backend-port>/api/v1/multi-backtests/run' \
  -H 'Content-Type: application/json' \
  -d '{
    "scan_run_id": "scan_xxxxxxxxxxxx",
    "template_id": "buy_and_hold",
    "parameters": {},
    "top_n": 10,
    "start": "2023-01-03",
    "end": "2025-12-31",
    "initial_cash": 100000,
    "commission": 0.001,
    "slippage": 0.0005
  }'
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

For browser-driven end-to-end verification:

```bash
make e2e
```

This starts a dedicated FastAPI + Vite pair, seeds a deterministic E2E universe, opens Chromium through Playwright, queues a scanner job, queues a portfolio rebalance job, watches Jobs, and verifies the Performance Report UI. It uses `backend/data/cache/e2e_market.sqlite3` so the smoke test does not depend on yfinance or the normal development cache.

Current Phase 9B validation result:

```text
Backend tests: 59 passed
Backend coverage: 88.08%
Frontend tests: 21 passed
Frontend lint, Prettier, and Vite production build: passed
Playwright E2E: 2 passed
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
├── pages/                dashboard, Market Data Lab, Strategy Builder, Backtest Lab, Agent Workflow, Stock Scanner, Data Quality, Comparison, Portfolio Rebalance, Jobs, Performance
├── services/             API service wrappers
├── styles/               modular CSS
└── utils/                formatting helpers
```

## Data boundary

Bundled CSV rows are deterministic synthetic fixtures for engineering tests and offline demos. They are not live, current, or observed market data. API responses explicitly mark fixture rows through warnings such as `synthetic_fixture_data`.

## Backtest execution boundary

The backtest engine does not generate trading advice. The MVP engine uses deterministic assumptions:

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
- Phase 4: backtest engine MVP;
- Phase 5: Backtest Lab frontend;
- Phase 6: Agent Timeline MVP;
- Phase 7A: market universe and scanner foundation;
- Phase 8A: scanner operations, data quality, and scanner-driven multi-asset backtest;
- Phase 9A: portfolio rebalance, performance analyzer expansion, scanner-to-portfolio presets, job queue, and quality gates;
- Phase 9B: in-app research demo automation with 20-stock sample workflow and Playwright validation.

Next:

- Portfolio analytics polish, exports, and larger-scale async execution controls.

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

<!-- portfolio-release-notes:start -->
## Portfolio Release Notes

## Overview
A local-first quant research workbench built with FastAPI, SQLite, and pandas. It provides a normalized OHLCV data layer, six technical indicators, five strategy templates with a Strategy JSON DSL, and an in-house deterministic backtest engine that outputs metrics, equity curves, and agent-style execution steps. The frontend is framework-free Vanilla JS with native SVG charts. Educational and research use only; not investment advice.

## Demo
- Live Demo: https://justin21523.github.io/quant-strategy-agent-lab/
- Portfolio Case Study: /projects/quant-strategy-agent-lab
- GitHub Repository: https://github.com/Justin21523/quant-strategy-agent-lab
- Demo Video: /projects/quant-strategy-agent-lab#demo-video
- README: https://github.com/Justin21523/quant-strategy-agent-lab#readme

## Features
- In-house long-only deterministic backtest engine: next-bar-open fills, explicit fees and slippage, forced final-bar liquidation, with fully transparent, auditable assumptions
- Strategy JSON DSL 1.0: declarative JSON for entry/exit and risk rules with structural and indicator-reference validation
- Six technical indicators (SMA/EMA/RSI/MACD/Bollinger Bands/ATR) computed on demand from SQLite-cached bars
- Provider-neutral data layer: synthetic CSV fixtures run fully offline by default, with yfinance and reserved FinMind adapter boundaries
- No frontend framework: Vanilla JS + ES Modules + native SVG rendering of price, indicator, equity, and drawdown charts
- Agent-style execution timeline orchestrating deterministic steps (receive -> validate -> load data -> compute indicators -> generate signals -> backtest -> analyze -> explain -> report) that cite concrete data assumptions

## Tech Stack
- Python
- FastAPI
- Pydantic
- pandas
- SQLite
- Vanilla JavaScript
- Vite
- Docker

## Architecture
This case study is generated from the portfolio catalog pipeline using README, Git metadata, package/build configuration, and media signals. The final architecture narrative still needs source-level review. Current detected technology signals include: Python, FastAPI, Pydantic, pandas, SQLite, Vanilla JavaScript, Vite, Docker.

## Project Structure
```text
quant-strategy-agent-lab/
  README.md              # project documentation, when available
  source files           # implementation reviewed by local audit
  package/build config   # detected capability signals
```

## Getting Started
- Install: No package install command detected.
- Dev/Run: No verified run command detected.
- Build: No verified build command detected.
- Test: No test script detected.
- Lint: No lint script detected.

## Screenshots
Screenshots are packaged in the portfolio under `public/projects/quant-strategy-agent-lab/screenshots/`. They are generated with Playwright from the current app.

## Demo Script
See `docs/demo-scripts/quant-strategy-agent-lab.md` in the portfolio release pack.

## Key Implementation Details
- Detected technical signals: Python, FastAPI, Pydantic, pandas, SQLite, Vanilla JavaScript, Vite, Docker
- README evidence exists and can support a fuller reviewed case study
- Public GitHub, README, live demo, and demo video links are verified in the portfolio entry.

## Challenges & Decisions
- Implementing reproducible fill and liquidation logic with clear assumptions without depending on backtesting.py or vectorbt
- Designing a Strategy JSON DSL that covers multiple strategy templates yet validates strictly
- Honestly labeling synthetic fixtures and backtest boundaries so no result can be mistaken for investment advice

## Future Improvements
- Add more real-market providers and stricter data freshness policies
- Expand portfolio optimization, rebalance cost modeling, and factor exposure analysis
- Package research artifacts as reproducible downloadable study bundles
<!-- portfolio-release-notes:end -->

<!-- portfolio-quality-notes:start -->
## Portfolio Quality Notes

This section records the latest portfolio packaging check. It is intentionally factual: incomplete deployment, video, or build work is listed as follow-up instead of being presented as finished.

### Verification Status
- Build: `npm --prefix frontend run build:pages`
- Run: `make dev` for the full local stack
- Test: `make check` and `make e2e`
- Lint: included in `make check`
- Screenshots: Playwright showcase screenshots present
- Demo Video: Playwright guide video present

### Portfolio Follow-up
- None.
<!-- portfolio-quality-notes:end -->

<!-- portfolio-readme:begin -->

## Portfolio Documentation

### Project Overview

**Quant Strategy Agent Lab** is maintained as part of the Justin21523 GitHub portfolio. Demo: quant-strategy-agent-lab

### Features

- Demo: quant-strategy-agent-lab

### Tech Stack

- HTML
- Docker
- Makefile

### Installation

```bash
./scripts/bootstrap.sh
```

### Usage

```bash
make dev
make check
make e2e
```

### Project Structure

```text
quant-strategy-agent-lab/
  .coverage
  .dockerignore
  .editorconfig
  .env.example
  .gitignore
  .nvmrc
  .python-version
  .ruff_cache/
  .vscode/
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
```

### Environment Variables

- `QSA_ENVIRONMENT`: TODO: Document expected value and whether it is required.
- `QSA_LOG_LEVEL`: TODO: Document expected value and whether it is required.
- `QSA_API_PREFIX`: TODO: Document expected value and whether it is required.
- `QSA_BACKEND_HOST`: TODO: Document expected value and whether it is required.
- `QSA_BACKEND_PORT`: TODO: Document expected value and whether it is required.
- `QSA_CORS_ORIGINS`: TODO: Document expected value and whether it is required.
- `VITE_API_BASE_URL`: TODO: Document expected value and whether it is required.

### Deployment

- Demo / GitHub Pages: https://justin21523.github.io/quant-strategy-agent-lab/
- Static frontend demo build: `npm --prefix frontend run build:pages`
- Full local stack: `make dev`

### Demo

- Live demo: https://justin21523.github.io/quant-strategy-agent-lab/
- Source: https://github.com/Justin21523/quant-strategy-agent-lab

### Screenshots

- Portfolio screenshots and demo video are generated by `npm --prefix frontend run showcase:capture`.

### License

- See `LICENSE`.

### Maintainer

- Justin21523 - https://github.com/Justin21523

<!-- portfolio-readme:end -->
