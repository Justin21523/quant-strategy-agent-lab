# Development Guide

## Bootstrap

```bash
./scripts/bootstrap.sh
```

## Start dev servers

```bash
./scripts/dev.sh
```

or:

```bash
make dev
```

The script selects free ports at runtime. Use the printed URLs:

```text
FastAPI: http://127.0.0.1:<backend-port>
Swagger: http://127.0.0.1:<backend-port>/docs
ReDoc: http://127.0.0.1:<backend-port>/redoc
Frontend: http://127.0.0.1:<frontend-port>
Market Data Lab: http://127.0.0.1:<frontend-port>/#/market-data
Strategy Builder: http://127.0.0.1:<frontend-port>/#/strategy-builder
Backtest Lab: http://127.0.0.1:<frontend-port>/#/backtest-lab
```

Do not assume backend `8000` or frontend `5173`.

## Quality checks

```bash
./scripts/check.sh
```

This runs backend lint/format/tests and frontend lint/format/tests/build.

## Git commit convention

Use one focused commit per completed phase:

```bash
git add .
git commit -m "feat: implement backtesting engine and trade execution pipeline"
```

## Backtest smoke test flow

1. Start `./scripts/dev.sh`.
2. Copy the printed backend and frontend URLs.
3. Render a template through `/api/v1/strategies/templates/{template_id}/render`.
4. Send the returned `strategy_json` to `/api/v1/backtests/run`.
5. Repeat through the printed frontend port to verify the Vite proxy.
