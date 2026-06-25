# API Specification

## Conventions

- Base path: `/api/v1`
- Format: JSON
- Dates: ISO 8601
- Timestamps: UTC ISO 8601 with offset
- Public contracts: Pydantic response models

## Phase 0 endpoints

### `GET /`

Returns backend metadata and links.

```json
{
  "name": "Quant Strategy Agent Lab API",
  "version": "0.1.0",
  "phase": "0-foundation",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```

### `GET /api/v1/health`

Liveness and identity response.

```json
{
  "status": "ok",
  "service": "Quant Strategy Agent Lab API",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-06-25T12:00:00Z"
}
```

### `GET /api/v1/system/info`

Returns the current project phase and honest capability states used by the frontend overview.

## Reserved future endpoint groups

```text
/api/v1/market/*
/api/v1/indicators/*
/api/v1/strategies/*
/api/v1/backtests/*
/api/v1/scans/*
/api/v1/agents/*
/api/v1/reports/*
```

These paths are documented but not implemented in Phase 0. Returning fake market or backtest output would create a misleading contract.
