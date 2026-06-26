# Backend

FastAPI modular monolith for the Quant Strategy Agent Lab.

```bash
make bootstrap
make backend
```

## Phase 1 boundaries

```text
HTTP route
→ MarketDataService
→ provider + normalizer + repository
→ SQLite
```

- `api/`: transport and response translation;
- `domain/`: provider-neutral models and errors;
- `providers/`: CSV, yfinance, and reserved FinMind adapters;
- `services/`: use-case orchestration and normalization;
- `repositories/`: SQLite access;
- `schemas/`: Pydantic API contracts.

Run tests:

```bash
cd backend
../.venv/bin/python -m pytest
```
