# Phase 2 Acceptance Record

**Phase:** 2 — Indicator Engine  
**Application version:** `0.3.0`  
**Date:** 2026-06-26

## Scope

Phase 2 implements the technical indicator engine planned for Quant Strategy Agent Lab:

- SMA;
- EMA;
- RSI;
- MACD;
- Bollinger Bands;
- ATR;
- indicator metadata API;
- `include_indicators=true` support on the OHLCV endpoint;
- Vanilla JS SMA overlays and RSI chart preview;
- unit tests for each indicator family.

## Acceptance criteria

| Requirement | Result |
|---|---|
| `GET /api/market/ohlcv?include_indicators=true` can return indicators | Passed via versioned endpoint `/api/v1/market/ohlcv` |
| Frontend can draw SMA | Passed: close-price SVG now overlays `sma_20` and `sma_60` |
| Frontend can draw RSI | Passed: Market Data Lab includes native SVG RSI preview |
| Each indicator has unit tests | Passed: SMA, EMA, RSI, MACD, Bollinger Bands, ATR |
| Indicators are computed from normalized OHLCV, not provider raw data | Passed: `IndicatorService` consumes `MarketSeries` / `MarketBar` |
| Dynamic dev ports are respected | Passed: runtime smoke tests used URLs printed by `./scripts/dev.sh` |

## Quality gate

`make check` / `./scripts/check.sh` result:

```text
Python Ruff lint and format: passed
Backend tests: 31 passed
Backend coverage: 90.99%
Frontend ESLint: passed
Frontend Prettier: passed
Frontend tests: 4 passed
Vite production build: passed
```

## Runtime smoke test

The dev server was started through `./scripts/dev.sh`, and the printed dynamic URLs were used. The verified run printed:

```text
FastAPI: http://127.0.0.1:59757
Swagger: http://127.0.0.1:59757/docs
ReDoc: http://127.0.0.1:59757/redoc
Frontend: http://127.0.0.1:47529
Market Data Lab: http://127.0.0.1:47529/#/market-data
```

The following were tested against those actual ports:

```text
GET backend /api/v1/health                                           HTTP 200
GET backend /api/v1/ready                                            HTTP 200
GET backend /api/v1/market/indicators/catalog                        HTTP 200
GET backend /api/v1/market/ohlcv?include_indicators=true             HTTP 200
GET backend /docs                                                    HTTP 200
GET backend /redoc                                                   HTTP 200
GET frontend /                                                       HTTP 200
GET frontend /api/v1/market/ohlcv?include_indicators=true            HTTP 200
GET frontend /docs                                                   HTTP 200
```

The API proxy test intentionally used the printed **Frontend** port, not a hard-coded Vite port.

## Sample indicator payload

Runtime validation confirmed that the default indicator bundle returns:

```text
indicator_count = 3
keys = sma_20, sma_60, rsi_14
```

The latest tested bar had non-null values for all three default indicators.

## Server cleanup

After `SIGTERM`, Uvicorn, its reload child, npm, and Vite were all stopped. No listeners remained on the dynamic backend/frontend ports used in the smoke test.

## Notes

- Phase 2 does not implement strategy templates yet.
- Phase 2 does not execute backtests yet.
- The bundled CSV market rows remain deterministic synthetic fixtures and are not investment data.
- Indicator values are educational/research features and are not trading advice.
