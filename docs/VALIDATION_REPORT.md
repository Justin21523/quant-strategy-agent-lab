# Validation Report — Phase 4

## Static and unit checks

```text
Ruff lint and format              PASS
Backend Pytest                    35 passed
Backend coverage                  89.01%
Frontend ESLint                   PASS
Frontend Prettier                 PASS
Frontend Node tests               5 passed
Vite production build             PASS
```

## Backend coverage focus

Phase 4 adds coverage for:

- Backtest API route;
- Strategy JSON DSL validation failure path;
- Buy and Hold execution;
- MA Crossover execution;
- MACD template execution;
- trade ledger and response shape;
- equity/drawdown curve length alignment;
- synthetic fixture warnings.

## Runtime smoke test focus

The runtime smoke test must use dynamic ports printed by `./scripts/dev.sh`:

```text
GET backend /api/v1/health
GET backend /api/v1/ready
GET backend /api/v1/strategies/templates
POST backend /api/v1/strategies/templates/buy_and_hold/render
POST backend /api/v1/backtests/run
GET backend /docs
GET backend /redoc
GET frontend /
POST frontend /api/v1/backtests/run through Vite proxy
```
