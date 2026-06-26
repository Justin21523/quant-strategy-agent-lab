# Architecture — Phase 4

Phase 4 keeps the system layered: market data is normalized first, indicators are computed from normalized bars, strategy templates render declarative Strategy JSON DSL, and the backtest engine consumes only validated DSL.

## Runtime architecture

```text
Browser
  ↓
Vanilla JS frontend
  ├── Market Data Lab
  ├── Strategy Builder
  └── Backtest Lab
  ↓ fetch / Vite proxy
FastAPI backend
  ├── MarketDataService
  ├── IndicatorService
  ├── StrategyTemplateService
  └── BacktestService
  ↓
SQLite cache + deterministic CSV fixtures
```

## Backtest path

```text
Template metadata
  ↓
Strategy Builder form
  ↓
POST /api/v1/strategies/templates/{id}/render
  ↓
Strategy JSON DSL v1.0
  ↓
POST /api/v1/backtests/run
  ↓
Strategy validation
  ↓
Cached OHLCV load
  ↓
Feature frame + indicators
  ↓
Signal generation
  ↓
Long-only execution
  ↓
Metrics, equity, drawdown, trades, warnings, agent steps
```

## Backend dependency direction

```text
api routes
  → schemas
  → services
  → repositories / providers
  → domain models
```

Services do not depend on FastAPI request objects. The `BacktestService` receives plain Strategy JSON dictionaries and returns domain objects.

## Frontend dependency direction

```text
pages
  → services
  → api-client
  → Fetch API

pages
  → components / charts / utils
```

The frontend never fabricates Strategy JSON rule logic. It asks the backend to render templates, then sends the returned JSON to the backtest endpoint.

## State ownership

```text
Market data cache       backend SQLite
Strategy templates      backend service
Rendered Strategy JSON   backend authoritative, frontend preview only
Backtest result          backend response, frontend display only
UI transient state       frontend page module
```

## Dynamic ports

Development ports are selected at runtime. All documentation, dev output, and smoke tests use the printed dynamic URLs:

```text
FastAPI: http://127.0.0.1:<backend-port>
Frontend: http://127.0.0.1:<frontend-port>
Backtest Lab: http://127.0.0.1:<frontend-port>/#/backtest-lab
```

## Safety boundaries

- Strategy templates generate declarative JSON, not code.
- The backtest engine validates DSL before execution.
- The engine is deterministic and long-only in Phase 4.
- Fixture data is explicitly marked.
- Backtest output is educational research output only, not investment advice.
