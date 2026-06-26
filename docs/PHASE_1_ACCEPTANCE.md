# Phase 1 Acceptance Record

**Validation date:** 2026-06-25  
**Phase:** Market Data Layer  
**Application version:** `0.2.0`

## Delivered scope

| Deliverable | Result |
|---|:---:|
| Provider protocol and domain models | Pass |
| Deterministic CSV fixture provider | Pass |
| Optional yfinance adapter | Pass |
| Reserved FinMind boundary | Pass |
| OHLCV normalizer and warnings | Pass |
| SQLite schema and repository | Pass |
| Startup seed without overwrite | Pass |
| Symbol/provider/OHLCV/sync APIs | Pass |
| Sync audit records | Pass |
| Vanilla JS Market Data Lab | Pass |
| Symbol dropdown and date controls | Pass |
| Provider/fallback controls | Pass |
| Provenance and quality display | Pass |
| SVG price preview and OHLCV table | Pass |
| Linux scripts and docs | Pass |

## Automated quality gate

Command:

```bash
make check
```

Result: **passed**.

| Check | Result |
|---|---|
| Ruff lint | Pass |
| Ruff format check | Pass |
| Backend tests | 20 passed |
| Backend branch coverage | 92.31% |
| Configured coverage floor | 80% |
| ESLint | Pass |
| Prettier check | Pass |
| Frontend tests | 3 passed |
| Vite production build | Pass |

Production build recorded during validation:

```text
dist/index.html                  0.74 kB
dist/assets/index-*.css         15.07 kB
dist/assets/index-*.js          27.02 kB
```

Hashed asset names and compressed sizes can change after formatting or source edits.

## Runtime smoke test

FastAPI and Vite were started together against an isolated temporary SQLite database.

| Runtime check | Result |
|---|---|
| `GET /api/v1/health` | HTTP 200, version `0.2.0`, `phase-1` |
| `GET /api/v1/ready` | HTTP 200, API/database ready |
| startup fixture import | 3 symbols, 2,346 bars |
| `GET /api/v1/market/symbols` | AAPL, QQQ, SPY |
| `GET /api/v1/market/ohlcv` | requested 5 rows returned in order |
| source metadata | CSV provider and synthetic-fixture flag present |
| warning contract | `synthetic_fixture_data` present |
| `POST /api/v1/market/sync` | auto fallback completed successfully |
| fallback disabled contract | yfinance-only attempt failed explicitly; CSV was not attempted |
| Vite `/api` proxy | symbol catalog returned through the Vite development server |
| Swagger `/docs` | HTTP 200 |
| frontend root | expected application title present |
| shutdown cleanup | no Vite/Uvicorn process or port left behind |

## Reproducibility and container-definition checks

| Check | Result |
|---|---|
| fixture regeneration | byte-identical SHA-256 hashes before and after regeneration |
| bundled fixture size | 782 rows per symbol, 2,346 total |
| local Markdown links | all referenced project files exist |
| Compose YAML structure | parsed successfully; backend/frontend services and health dependency present |
| Docker runtime | not executed because this validation environment has no Docker or Podman binary |

## External provider verification boundary

The yfinance adapter is covered with injected DataFrame and provider-error tests. The deterministic runtime smoke test intentionally set `QSA_MARKET_YFINANCE_ENABLED=false`, then verified both request branches:

- `allow_fallback=false`: only yfinance was attempted and the result failed explicitly;
- `allow_fallback=true`: the yfinance failure was recorded and CSV completed the synchronization.

A successful live Yahoo retrieval was not required for deterministic Phase 1 acceptance.

Therefore:

- adapter parsing and error translation: verified;
- fallback disclosure and the no-fallback guarantee: verified;
- successful live Yahoo retrieval in this validation run: **not claimed**.

## Fixture integrity

- Symbols: AAPL, SPY, QQQ
- Date range: 2023-01-03 through 2025-12-31
- Rows: 782 per symbol
- Total startup rows: 2,346
- Dataset: `qsal-synthetic-offline-v1`
- Classification: deterministic synthetic engineering fixtures

The UI, manifest, repository, API, and documentation all identify these rows as synthetic and unsuitable for investment conclusions.

## Exit conclusion

Phase 1 satisfies its exit condition: a user can select a supported symbol, inspect validated cached OHLCV and source metadata, synchronize through a provider contract with explicit fallback, and receive meaningful warnings without requiring network access.

The next implementation boundary is Phase 2: indicators derived exclusively from normalized cached bars.
