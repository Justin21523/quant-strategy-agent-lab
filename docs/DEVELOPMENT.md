# Linux Development Guide

## Bootstrap

```bash
make bootstrap
```

Equivalent command:

```bash
./scripts/bootstrap.sh
```

The script verifies Python and Node versions, creates `.venv`, installs `backend/requirements-dev.txt`, copies `backend/.env.example` when necessary, and installs frontend packages using `npm ci`.

## Run both services

```bash
make dev
```

Endpoints:

```text
Frontend     http://127.0.0.1:5173
FastAPI      http://127.0.0.1:8000
Swagger      http://127.0.0.1:8000/docs
Market Lab   http://127.0.0.1:5173/#/market-data
```

`Ctrl+C` terminates the Uvicorn and npm/Vite process groups, including reload children.

## Run independently

```bash
make backend
make frontend
```

## Configuration

Backend variables use the `QSA_` prefix and are loaded from `backend/.env` or the process environment.

```bash
cp backend/.env.example backend/.env
```

Useful offline configuration:

```text
QSA_MARKET_YFINANCE_ENABLED=false
QSA_MARKET_SEED_DEMO_DATA=true
```

Use a temporary database for isolated manual tests:

```bash
QSA_MARKET_DATABASE_PATH=/tmp/qsal.sqlite3 make backend
```

## Database inspection

```bash
sqlite3 backend/data/cache/market_data.sqlite3
```

Useful SQL:

```sql
.tables
SELECT symbol, COUNT(*) FROM ohlcv_bars GROUP BY symbol;
SELECT symbol, provider, MIN(trade_date), MAX(trade_date)
FROM ohlcv_bars
GROUP BY symbol, provider;
SELECT run_id, symbol, status, requested_provider, provider_used, fallback_used
FROM market_sync_runs
ORDER BY created_at DESC;
```

The cache directory is gitignored. Removing the database is safe during development; the next backend startup recreates the schema and imports missing fixture rows.

## Fixture regeneration

```bash
.venv/bin/python scripts/generate_demo_market_data.py
```

After regeneration, run all tests. The fixtures are synthetic and must stay labeled as such in `symbols.csv`, API responses, documentation, and UI.

## API examples

```bash
curl http://127.0.0.1:8000/api/v1/market/symbols

curl 'http://127.0.0.1:8000/api/v1/market/ohlcv?symbol=SPY&start=2023-01-03&end=2023-02-01'

curl -X POST http://127.0.0.1:8000/api/v1/market/sync \
  -H 'Content-Type: application/json' \
  -d '{"symbols":["QQQ"],"provider":"auto","start":"2023-01-03","end":"2023-01-31","allow_fallback":true}'
```

## Quality gate

```bash
make check
```

Individual commands:

```bash
cd backend && ../.venv/bin/ruff check .
cd backend && ../.venv/bin/ruff format --check .
cd backend && ../.venv/bin/python -m pytest
npm --prefix frontend run lint
npm --prefix frontend run format:check
npm --prefix frontend run test
npm --prefix frontend run build
```

## Code rules

### Python

- type public boundaries;
- keep route handlers thin;
- use domain errors instead of transport-specific exceptions in services;
- never persist unnormalized provider rows;
- keep SQL inside repositories;
- test fallback and failure behavior, not only happy paths.

### JavaScript

- use ES modules and named exports;
- keep HTTP construction in services;
- keep DOM composition in pages/components;
- use `textContent`/safe DOM creation rather than injecting external HTML;
- destroy page-owned listeners, timers, streams, observers, and charts during route changes;
- represent loading, empty, error, warning, and success states explicitly.

### CSS

- use existing design tokens;
- keep route-specific styles modular;
- preserve visible keyboard focus;
- test desktop and narrow layouts;
- do not encode financial meaning through color alone.

## Docker

```bash
docker compose up --build
```

Inspect:

```text
Frontend  http://localhost:8080
Backend   http://localhost:8000
Swagger   http://localhost:8000/docs
```

## Troubleshooting

### API appears offline

```bash
curl -v http://127.0.0.1:8000/api/v1/health
ss -ltnp | grep -E ':8000|:5173'
```

### External synchronization fails

The network provider is optional. Check DNS/network access and provider terms, or use `provider: "csv"`. With fallback enabled, the sync audit records both the failed external attempt and CSV success.

### Cache contains fixture rows after external sync

Fixture import never overwrites an existing date, but an external sync only replaces dates inside its requested range. Query `provider` by date to see which portions remain synthetic.
