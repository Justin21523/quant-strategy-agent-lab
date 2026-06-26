# API Specification — Phase 3

Base prefix: `/api/v1`

OpenAPI document: `/api/v1/openapi.json`

All dates use ISO 8601 calendar-date format (`YYYY-MM-DD`). Daily bars are returned in ascending date order. Unknown request fields are rejected where Pydantic models use `extra="forbid"`.

## Dynamic development URLs

When running locally, use the URLs printed by `./scripts/dev.sh` or `make dev`. Development ports are dynamic and must not be assumed.

```text
FastAPI: http://127.0.0.1:<backend-port>
Swagger: http://127.0.0.1:<backend-port>/docs
ReDoc: http://127.0.0.1:<backend-port>/redoc
Frontend: http://127.0.0.1:<frontend-port>
Market Data Lab: http://127.0.0.1:<frontend-port>/#/market-data
Strategy Builder: http://127.0.0.1:<frontend-port>/#/strategy-builder
```

## Common error envelope

Domain errors use a stable envelope:

```json
{
  "error": {
    "code": "strategy_template_validation_error",
    "message": "Fast window must be smaller than slow window.",
    "details": {
      "fast_window": 80,
      "slow_window": 20
    }
  }
}
```

Representative status mapping:

| Status | Meaning |
|---:|---|
| `404` | symbol, cached range, or strategy template not found |
| `413` | response exceeds configured row limit |
| `422` | invalid date range/provider/template parameter/request shape |
| `501` | reserved provider is not implemented |
| `502` | provider returned unusable data |
| `503` | provider or required dependency unavailable |

## System endpoints

### `GET /api/v1/health`

```json
{
  "status": "ok",
  "service": "Quant Strategy Agent Lab API",
  "version": "0.4.0",
  "environment": "development",
  "phase": "phase-3",
  "timestamp": "2026-06-26T00:00:00Z"
}
```

### `GET /api/v1/ready`

```json
{
  "status": "ready",
  "checks": {
    "api": "ok",
    "database": "ok"
  }
}
```

### `GET /api/v1/system/info`

```json
{
  "phase": "3",
  "phase_name": "Strategy Template System",
  "cache": {
    "symbols": 3,
    "bars": 2346,
    "sync_records": 0
  },
  "strategy_templates": 5,
  "capabilities": [
    {
      "key": "strategy_templates",
      "label": "Strategy template catalog",
      "status": "ready"
    },
    {
      "key": "strategy_json_dsl",
      "label": "Template to Strategy JSON DSL",
      "status": "ready"
    },
    {
      "key": "strategy_validation",
      "label": "Strategy JSON validation",
      "status": "ready"
    }
  ]
}
```

## Strategy template endpoints

### `GET /api/v1/strategies/templates`

Returns deterministic template metadata and typed parameter definitions.

```json
{
  "total": 5,
  "templates": [
    {
      "id": "ma_crossover_rsi",
      "name": "MA Crossover + RSI Filter",
      "category": "trend_following",
      "indicator_kinds": ["SMA", "RSI"],
      "parameters": []
    }
  ]
}
```

### `GET /api/v1/strategies/templates/{template_id}`

Reads one template. Template IDs are normalized case-insensitively and hyphens are treated as underscores.

### `POST /api/v1/strategies/templates/{template_id}/render`

Renders a template into Strategy JSON DSL. The endpoint is authoritative; the frontend does not construct strategy rules locally.

```json
{
  "symbol": "AAPL",
  "market": "US",
  "timeframe": "1d",
  "start": "2023-01-03",
  "end": "2025-12-31",
  "initial_cash": 100000,
  "commission": 0.001,
  "slippage": 0.0005,
  "parameters": {
    "fast_window": 20,
    "slow_window": 60,
    "rsi_window": 14,
    "rsi_entry_max": 70,
    "rsi_exit_min": 80,
    "source": "close",
    "stop_loss_pct": 0.08,
    "take_profit_pct": 0.2,
    "max_position_pct": 1.0
  }
}
```

Response excerpt:

```json
{
  "dsl_version": "1.0",
  "template": {
    "id": "ma_crossover_rsi",
    "name": "MA Crossover + RSI Filter"
  },
  "required_indicators": ["sma_fast", "sma_slow", "rsi"],
  "validation": {
    "valid": true,
    "issue_count": 0,
    "issues": []
  },
  "strategy_json": {
    "dsl_version": "1.0",
    "strategy_id": "ma_crossover_rsi",
    "strategy_name": "SMA 20/60 Crossover + RSI Filter",
    "symbol": "AAPL",
    "indicators": [],
    "entry_rules": {},
    "exit_rules": {},
    "risk_rules": {}
  }
}
```

### `POST /api/v1/strategies/render`

Alternative body-selected render endpoint. The request must include `template_id`.

### `POST /api/v1/strategies/validate`

Validates a Strategy JSON DSL document without rendering it from a template.

```json
{
  "strategy_json": {
    "dsl_version": "1.0"
  }
}
```

Response:

```json
{
  "valid": false,
  "issue_count": 7,
  "issues": [
    {
      "code": "missing_top_level_field",
      "severity": "error",
      "message": "Strategy DSL is missing top-level field 'symbol'.",
      "path": "$.symbol",
      "context": {}
    }
  ]
}
```

## Market and indicator endpoints

The Phase 1 and Phase 2 endpoints remain available:

```text
GET  /api/v1/market/providers
GET  /api/v1/market/symbols
GET  /api/v1/market/ohlcv?symbol=AAPL&include_indicators=true
POST /api/v1/market/sync
GET  /api/v1/indicators/catalog
```
