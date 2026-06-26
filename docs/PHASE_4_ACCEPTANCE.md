# Phase 4 Acceptance — Backtest Engine MVP

## Scope

Phase 4 implements the first executable backtest layer for Strategy JSON DSL.

Included:

- `POST /api/v1/backtests/run`;
- Strategy JSON DSL validation before execution;
- cached OHLCV loading through `MarketDataService`;
- indicator computation from Strategy JSON requirements;
- entry and exit signal generation;
- deterministic long-only execution;
- commission and slippage support;
- next-open fills for normal signals;
- final close liquidation for open positions;
- metrics, trades, equity, drawdown, warnings, and Agent-style steps;
- minimal Vanilla JS Backtest Lab route;
- dynamic dev-server URL output includes Backtest Lab.

Out of scope:

- polished K-line Backtest Lab UI;
- parameter scanning;
- multi-asset backtests;
- short selling;
- external engine adapters;
- LLM explanation.

## Acceptance checklist

```text
✅ Backtest endpoint exists
✅ Strategy JSON is validated before execution
✅ Buy and Hold can be backtested
✅ MA Crossover can be backtested
✅ MACD template can be backtested
✅ Response includes metrics
✅ Response includes trades
✅ Response includes equity curve
✅ Response includes drawdown curve
✅ Response includes warnings
✅ Response includes Agent-style steps
✅ Frontend Backtest Lab can run a backtest
✅ dev.sh prints Backtest Lab URL with the selected dynamic frontend port
✅ Vite API proxy works through the printed frontend port
✅ Quality gate passes
```

## Quality gate

```text
Python Ruff lint and format       PASS
Backend tests                     35 passed
Backend coverage                  89.01%
Frontend ESLint                   PASS
Frontend Prettier                 PASS
Frontend tests                    5 passed
Vite production build             PASS
```

## Runtime smoke test

The runtime smoke test used the URLs printed by `./scripts/dev.sh` rather than fixed ports.

Validated endpoints:

```text
GET backend /api/v1/health
GET backend /api/v1/ready
GET backend /api/v1/strategies/templates
POST backend /api/v1/strategies/templates/buy_and_hold/render
POST backend /api/v1/backtests/run
GET backend /docs
GET backend /redoc
GET frontend /
POST frontend /api/v1/backtests/run via Vite proxy
```

## Backtest assumptions

```text
Daily bars only
Long-only
One position at a time
Completed bars generate normal signals
Normal entries/exits fill at next open
Buy and Hold first entry fills at first open
Open positions liquidate at final close
Commission and slippage are explicit inputs
```

## Disclaimer

Backtest output is educational research output only. Historical performance cannot guarantee future performance, and this project does not provide investment advice.
