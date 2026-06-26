# Phase 3 Acceptance — Strategy Template System

## Scope completed

- deterministic strategy-template service;
- five MVP templates: Buy and Hold, MA Crossover, MA Crossover + RSI Filter, RSI Mean Reversion, MACD Trend Following;
- Strategy JSON DSL rendering;
- backend validation for template parameters and DSL structure;
- Strategy Builder frontend route;
- live backend-rendered JSON preview;
- validation messages and template metadata panels;
- dynamic dev-server URL output includes Strategy Builder.

## Backend endpoints

```text
GET  /api/v1/strategies/templates
GET  /api/v1/strategies/templates/{template_id}
POST /api/v1/strategies/templates/{template_id}/render
POST /api/v1/strategies/render
POST /api/v1/strategies/validate
```

## Frontend route

Use the URL printed by `./scripts/dev.sh` or `make dev`:

```text
Strategy Builder: http://127.0.0.1:<frontend-port>/#/strategy-builder
```

## Acceptance checks

- user can select one of five templates;
- user can modify typed parameters;
- JSON preview updates from the backend render endpoint;
- backend returns structured errors for invalid parameters;
- validation panel shows DSL validation results;
- API proxy tests must use the printed frontend port.

## Quality result

```text
Backend tests: 31 passed
Backend coverage: 89.09%
Frontend tests: 4 passed
Ruff: pass
ESLint: pass
Prettier: pass
Vite production build: pass
```

## Out of scope

- natural-language strategy parsing;
- signal generation;
- backtest execution;
- parameter scanning;
- LLM explanation.

Those start in later phases after this controlled Strategy JSON DSL path is stable.

## Runtime smoke test

A smoke test was run using URLs printed by `./scripts/dev.sh` with dynamic ports:

```text
FastAPI: http://127.0.0.1:38025
Swagger: http://127.0.0.1:38025/docs
ReDoc: http://127.0.0.1:38025/redoc
Frontend: http://127.0.0.1:52373
Market Data Lab: http://127.0.0.1:52373/#/market-data
Strategy Builder: http://127.0.0.1:52373/#/strategy-builder
```

Validated:

```text
GET backend /api/v1/health                              OK phase-3 0.4.0
GET backend /api/v1/strategies/templates                OK total=5
POST backend /api/v1/strategies/templates/.../render    OK valid=true
GET backend /docs                                       OK
GET backend /redoc                                      OK
GET frontend /                                          OK
GET frontend /api/v1/strategies/templates               OK via Vite proxy, total=5
Shutdown cleanup                                        OK; dynamic ports stopped responding
```
