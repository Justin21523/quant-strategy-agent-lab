# Project Specification

## 1. Product name

**Quant Strategy Agent Lab — 量化策略回測與 AI Agent 實驗室**

## 2. Product statement

A local-first research workbench that converts a strategy template or natural-language description into a validated Strategy JSON DSL, then calculates indicators, generates signals, executes historical backtests, measures performance, explains risk, scans parameters, and exports a reproducible report.

## 3. Product boundary

This project is a research and engineering system, not an investment-advice product. It must never present a historical result as a promise, forecast certainty, or personalized recommendation.

### Explicit non-goals

- live order execution during the portfolio-project roadmap;
- guaranteed price or return prediction;
- arbitrary LLM-generated Python execution;
- silently changing data, costs, or strategy assumptions;
- optimizing only on one historical period and calling the result robust.

## 4. Target users

### Primary

- a learner practicing HTML, CSS, modular Vanilla JavaScript, Python, APIs, and financial engineering;
- a reviewer evaluating full-stack, quantitative, and AI-agent engineering skills.

### Secondary

- a researcher comparing transparent rule-based strategies on historical datasets.

## 5. Core user journey

```text
Choose symbol and date range
        ↓
Choose a template or enter natural language
        ↓
Inspect and validate Strategy JSON DSL
        ↓
Run a cost-aware historical backtest
        ↓
Inspect trades, equity, drawdown, and metrics
        ↓
Review the agent timeline and risk explanation
        ↓
Scan parameters or compare assets
        ↓
Export a reproducible research report
```

## 6. Functional modules

| Module | Responsibility | First phase |
|---|---|---:|
| Application shell | Routing, state, navigation, status | 0 |
| Market data | Ingestion, validation, cache, provenance | 1 |
| Indicator engine | Tested indicator calculations | 2 |
| Strategy templates | Safe strategy configuration | 3 |
| Strategy DSL | Structure and validation | 3 |
| Backtest engine | Signals, positions, costs, trades, equity | 4 |
| Backtest UI | Interactive execution and charts | 5 |
| Agent timeline | Observable workflow state | 6 |
| Performance analyzer | Return and risk metrics | 7 |
| Explanation engine | Rule-based, then local-LLM explanation | 8 |
| Natural-language parser | Text to constrained DSL | 9 |
| Parameter scanner | Sensitivity analysis, not magic optimization | 10 |
| Multi-asset comparison | Generalization tests and ranking | 11 |
| Report center | Reproducible exports | 12 |
| Portfolio polish | Tests, screenshots, docs, deployment | 13 |

## 7. Phase 0 requirements

### Goals

- establish clean frontend and backend module boundaries;
- create a reproducible Linux development workflow;
- expose a versioned health API and automatic API documentation;
- provide real navigation and backend connectivity without pretending later features exist;
- document decisions and quality gates.

### Deliverables

- `README.md`;
- `docs/PROJECT_SPEC.md`;
- `docs/ROADMAP.md`;
- modular Vanilla JavaScript frontend skeleton;
- FastAPI backend skeleton;
- `.gitignore`, `.env.example`, `Makefile`, and scripts;
- Python and JavaScript lint/test configuration;
- Docker and Compose definitions.

### Acceptance criteria

- `./scripts/bootstrap.sh` installs dependencies on a compatible Linux environment;
- `./scripts/dev.sh` starts frontend and backend processes;
- the frontend route shell works without a framework;
- the frontend reports backend health through `/api/v1/health`;
- Swagger UI is available at `/docs`;
- `make check` runs lint, tests, and a frontend production build;
- the README contains the educational-use and no-investment-advice disclaimer.

## 8. Architectural constraints

### Frontend

- no React, Vue, Angular, Svelte, or similar application framework;
- ES modules are mandatory;
- pages may compose components and call services;
- services may call the API client but may not import page modules;
- chart libraries will be wrapped behind chart modules when introduced;
- global state must be small and explicit.

### Backend

- API route handlers orchestrate input/output only;
- domain calculations belong in services;
- data access belongs in repositories;
- Pydantic schemas define all public request and response contracts;
- every quantitative formula receives deterministic tests;
- source data and derived data remain distinguishable.

### Agent safety

- natural language is converted only into an allow-listed DSL;
- DSL validation happens before any indicator or backtest work;
- an LLM cannot import packages, access the file system, or execute generated code;
- agent steps must expose status and useful failure detail.

## 9. Data and backtest integrity requirements

Later phases must record:

- symbol, market, timeframe, and source;
- requested and effective date ranges;
- missing-value and corporate-action handling;
- initial cash, commission, slippage, and position sizing;
- strategy definition and parameter values;
- execution assumptions and engine version;
- benchmark definition;
- full trade list and equity series;
- warnings for insufficient observations or trades.

## 10. Success criteria for the finished portfolio project

- a reviewer can clone, bootstrap, and run the system from documented Linux commands;
- one strategy can be traced from human input to validated DSL to every resulting trade;
- performance output is reproducible and includes assumptions;
- parameter results show sensitivity rather than only the best cell;
- the frontend clearly separates facts, computed metrics, and generated explanations;
- automated tests protect financial calculations and API contracts;
- the project can be explained in a technical interview without hand-waving.
