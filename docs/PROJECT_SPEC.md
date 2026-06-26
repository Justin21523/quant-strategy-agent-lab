# Project Specification

## Product statement

Quant Strategy Agent Lab is a local-first research workbench where a user defines a quantitative trading strategy through a template or natural language, the system converts it into a controlled Strategy JSON DSL, Python tools run historical simulations, and an explicit Agent workflow produces performance and risk reports.

## Goals

1. Demonstrate full-stack engineering without a frontend framework.
2. Keep quantitative logic reproducible, testable, and server-authoritative.
3. Make data lineage and Agent/tool execution inspectable rather than magical.
4. Report return and risk together with assumptions and limitations.
5. Grow incrementally from deterministic data/templates to natural-language strategy parsing.

## Non-goals

- live brokerage integration or order execution;
- personalized investment advice;
- guaranteed predictive performance;
- arbitrary LLM-generated Python execution;
- high-frequency or tick-level simulation in the initial roadmap;
- presenting synthetic fixtures as observed market prices.

## Core user journey

```text
Inspect symbol, provider, date range, adjustment, and data warnings
→ choose a strategy template or enter natural language
→ review validated Strategy JSON DSL
→ configure capital, fee, slippage, and position rules
→ run backtest
→ inspect Agent timeline, signals, equity, drawdown, trades, and metrics
→ read risk explanation
→ export a reproducible report
```

## Cross-cutting research requirements

Every future run must record:

- provider, dataset, retrieval timestamp, fixture status, and adjusted-price policy;
- market, exchange, symbol, currency, timezone, timeframe, and effective date range;
- initial capital, commission, slippage, and fill timing;
- position sizing, cash, warm-up, and benchmark rules;
- Strategy DSL, indicator, and engine versions;
- generated warnings and report timestamp.

## Phase 0 acceptance

- Linux bootstrap works;
- FastAPI and Vite run together;
- versioned health/readiness/API docs work;
- modular Vanilla JavaScript shell works;
- lint, tests, formatting, and build pass;
- explicit non-advisory disclaimer exists.

## Phase 1 acceptance

- provider-neutral source and persistent market-bar models exist;
- AAPL, SPY, and QQQ work offline;
- yfinance can be selected behind the same provider contract;
- FinMind has an explicit reserved boundary rather than fake behavior;
- dates, numbers, OHLC envelopes, duplicate rows, and ordering are validated;
- normalized daily bars persist in SQLite with source metadata;
- synchronization attempts and fallback are auditable;
- Market Data APIs expose symbols, providers, cached OHLCV, sync, and warnings;
- the Vanilla JS UI can select a symbol/range, sync, and inspect data/provenance;
- API, unit, quality-gate, build, and runtime smoke tests pass.

## Security and integrity boundaries

- External text is never inserted as raw HTML.
- External provider data is never trusted before normalization.
- SQLite paths and CSV manifest paths are constrained by configuration/provider checks.
- Provider errors do not erase prior cached data.
- The future LLM layer may emit only a constrained DSL and prose; it may not execute generated Python.
- Research disclaimers do not replace engineering controls: assumptions and provenance must remain machine-readable.
