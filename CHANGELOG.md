# Changelog

## 0.5.0 — Phase 4 Backtest Engine MVP

- Added deterministic long-only Backtest Engine MVP.
- Added `/api/v1/backtests/run` for executing validated Strategy JSON DSL.
- Added entry/exit signal generation from rule groups.
- Added next-open fills, first-bar Buy and Hold entry, explicit commission/slippage, and forced final-bar liquidation.
- Added trade ledger, equity curve, drawdown curve, core performance metrics, warnings, and Agent-style execution steps.
- Added minimal Vanilla JavaScript Backtest Lab route.
- Updated `scripts/dev.sh` to print the dynamic Backtest Lab URL.
- Advanced project version to `0.5.0` and status to Phase 4.

## 0.4.0 — Phase 3 Strategy Template System

- Added deterministic Strategy Template System and Strategy JSON DSL rendering.
- Added five MVP templates: Buy and Hold, MA Crossover, MA Crossover + RSI Filter, RSI Mean Reversion, and MACD Trend Following.
- Added `/api/v1/strategies/templates`, `/api/v1/strategies/templates/{template_id}/render`, and `/api/v1/strategies/validate`.
- Added Vanilla JavaScript Strategy Builder with template selector, typed parameter editor, JSON preview, validation panel, and template metadata.
- Updated `scripts/dev.sh` to print the dynamic Strategy Builder URL.
- Advanced project version to `0.4.0` and status to Phase 3.

## 0.3.0 — Phase 2 Indicator Engine

- Added provider-neutral indicator domain models and `IndicatorService`.
- Implemented SMA, EMA, RSI, MACD, Bollinger Bands, and ATR.
- Added `/api/v1/indicators/catalog`.
- Added `include_indicators=true` support to `/api/v1/market/ohlcv`.
- Added Vanilla SVG SMA/RSI indicator previews in the Market Data Lab.
- Updated `scripts/dev.sh` to select dynamic ports and print FastAPI, Swagger, ReDoc, Frontend, and Market Data Lab URLs.

## 0.2.0 — Phase 1 Market Data Layer

- Provider-neutral market-data domain and adapter protocol.
- Deterministic synthetic CSV fixtures for AAPL, SPY, and QQQ.
- Optional yfinance daily-history adapter and reserved FinMind boundary.
- OHLCV normalization, data-quality warnings, and source metadata.
- SQLite symbol, bar, and synchronization-audit persistence.
- Market providers, symbols, OHLCV, synchronization, readiness, and cache-stat APIs.
- Vanilla JavaScript Market Data Lab with provider controls, provenance, warnings, SVG preview, and OHLCV table.
- Phase 1 API, architecture, pipeline, development, roadmap, and acceptance documentation.
- Docker Compose deployment for Nginx frontend, FastAPI backend, and persistent SQLite volume.

## 0.1.0 — Phase 0 Foundation

- FastAPI application factory, CORS, health/readiness endpoints, Swagger UI, and OpenAPI schema.
- Modular Vanilla JavaScript shell with router, store, event bus, API client, pages, and components.
- Linux bootstrap, development, verification, and Git initialization scripts.
- Product, architecture, API, Strategy DSL, development, ADR, and roadmap documents.
- Ruff, pytest/coverage, ESLint, Prettier, and Vite production build quality gates.
