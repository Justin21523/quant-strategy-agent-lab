# Changelog

## 0.11.0 — Phase 9B In-App Research Demo Automation

- Added a deterministic 20-stock synthetic sample universe for automated workflow demos.
- Added research demo job/API endpoints that run sample sync, quality report, scanner, portfolio preset matrix, and multi-strategy comparison.
- Added a Dashboard demo mode with an Activate Demo browser-guided app tour.
- Expanded Playwright E2E coverage to verify the in-app demo automation.
- Advanced project version to `0.11.0` and status to Phase 9B.

## 0.10.0 — Phase 9A Portfolio Rebalance and Job Queue

- Added equal-weight portfolio rebalance runs with weekly/monthly cadence, turnover, skipped periods, holdings, and equity curves.
- Added richer performance analysis with CAGR, annual volatility, Sharpe, Sortino, Calmar, rolling drawdown, monthly returns, and benchmark comparison.
- Added scanner-to-portfolio presets for Trend Momentum, Low Volatility Trend, and Oversold Watchlist workflows.
- Added a SQLite-backed job queue for batch sync, scanner runs, and portfolio rebalance jobs with progress events.
- Integrated reusable data-quality gates into scanner and portfolio workflows.
- Added Portfolio Rebalance, Jobs, and strengthened Performance frontend pages.
- Advanced project version to `0.10.0` and status to Phase 9A.

## 0.9.0 — Phase 8A Scanner Operations and Multi-Asset Backtest

- Added scanner presets, toggleable scanner filters, saved scan-run listing, skipped-symbol persistence, and richer sortable metrics.
- Added batch-sync history APIs plus missing/stale sync and failed-symbol retry modes.
- Added universe data-quality reports for coverage, missing weekdays, fixture flags, and SMA200/252D readiness.
- Added scanner-driven multi-asset backtest runs with aggregate and per-symbol performance ranking.
- Added Data Quality and Multi-Asset Comparison frontend pages.
- Advanced project version to `0.9.0` and status to Phase 8A.

## 0.8.0 — Phase 7A Market Universe and Scanner Foundation

- Added US common-stock universe refresh from Nasdaq Trader symbol directory files.
- Added cursor-based `/api/v1/market/batch-sync` for chunked universe synchronization.
- Added saved technical scanner runs at `/api/v1/scans/run` and `/api/v1/scans/{run_id}`.
- Replaced the placeholder Parameter Scanner route with an interactive Stock Scanner UI.
- Advanced project version to `0.8.0` and status to Phase 7A.

## 0.7.0 — Phase 6 Agent Timeline MVP

- Added canonical Agent workflow metadata at `/api/v1/agent/backtest-workflow`.
- Added Agent Workflow frontend route and reusable timeline state handling.
- Integrated runtime backtest `agent_steps` into the Backtest Lab timeline.
- Advanced project version to `0.7.0` and status to Phase 6.

## 0.6.0 — Phase 5 Backtest Lab Frontend

- Added candlestick chart support with buy/sell markers.
- Expanded Backtest Lab result panels, metric presentation, and trade inspection UI.
- Added frontend tests for backtest chart normalization and marker generation.
- Advanced project version to `0.6.0` and status to Phase 5.

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
