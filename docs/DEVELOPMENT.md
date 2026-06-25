# Linux Development Workflow

## Supported runtime baseline

- Python 3.11+
- Node.js 20.19+, 22.12+, or newer compatible releases
- npm

The repository includes `.python-version` and `.nvmrc` as convenience hints, while runtime checks in `scripts/bootstrap.sh` enforce minimum versions.

## First setup

```bash
cp .env.example .env
./scripts/bootstrap.sh
```

The script:

1. checks Python and Node versions;
2. creates `.venv`;
3. installs backend runtime and development dependencies;
4. installs frontend dependencies using `npm ci`;
5. creates `.env` when missing.

## Run both applications

```bash
./scripts/dev.sh
```

The script starts Uvicorn and Vite, keeps both attached to the terminal, and cleans up child processes on exit.

## Run applications separately

Terminal 1:

```bash
make backend-dev
```

Terminal 2:

```bash
make frontend-dev
```

## Quality gate

```bash
make check
```

A change is not considered complete unless:

- Python lint passes;
- JavaScript lint passes;
- backend API tests pass;
- frontend unit tests pass;
- the frontend production build succeeds.

## Git workflow

Recommended branch names:

```text
phase/01-market-data
feature/market-symbol-endpoint
fix/frontend-health-timeout
chore/dependency-update
```

Recommended commit style:

```text
feat(market): add validated symbol catalog endpoint
test(indicators): cover RSI flat-series behavior
docs(strategy): define crossover DSL semantics
fix(frontend): cancel stale health requests on route change
```

Each phase should end with:

1. passing quality checks;
2. updated API and architecture documentation;
3. a clear manual demo path;
4. a tagged milestone or release note.

## Environment variables

Copy `.env.example` to `.env`. Do not commit `.env`.

| Variable | Purpose |
|---|---|
| `QSA_ENVIRONMENT` | Backend runtime label |
| `QSA_LOG_LEVEL` | Planned logging level |
| `QSA_API_PREFIX` | Versioned API root |
| `QSA_CORS_ORIGINS` | Comma-separated browser origins |
| `VITE_API_BASE_URL` | Browser API base path |

## Troubleshooting

### Port already in use

```bash
ss -ltnp | grep -E ':(5173|8000)\b'
```

### Recreate dependencies

```bash
rm -rf .venv frontend/node_modules
./scripts/bootstrap.sh
```

### Verify backend only

```bash
curl -fsS http://127.0.0.1:8000/api/v1/health | python3 -m json.tool
```
