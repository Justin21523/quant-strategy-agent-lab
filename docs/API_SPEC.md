# API Specification — Phase 1

Base prefix: `/api/v1`

OpenAPI document: `/api/v1/openapi.json`

All dates use ISO 8601 calendar-date format (`YYYY-MM-DD`). Daily bars are returned in ascending date order. Unknown request fields are rejected where Pydantic models use `extra="forbid"`.

## Common error envelope

Domain errors use a stable envelope:

```json
{
  "error": {
    "code": "symbol_not_found",
    "message": "Unsupported symbol: NOPE",
    "details": {
      "symbol": "NOPE"
    }
  }
}
```

Representative status mapping:

| Status | Meaning |
|---:|---|
| `404` | symbol or cached range not found |
| `413` | response exceeds configured row limit |
| `422` | invalid date range/provider/request shape |
| `501` | reserved provider is not implemented |
| `502` | provider returned unusable data |
| `503` | provider or required dependency unavailable |

FastAPI's request-validation errors retain the standard FastAPI `detail` shape. Domain errors use the envelope above.

## System endpoints

### `GET /api/v1/health`

Liveness only. It does not prove database readiness.

```json
{
  "status": "ok",
  "service": "Quant Strategy Agent Lab API",
  "version": "0.2.0",
  "environment": "development",
  "phase": "phase-1",
  "timestamp": "2026-06-25T23:02:26.927764Z"
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
  "phase": "1",
  "phase_name": "Market Data Layer",
  "cache": {
    "symbols": 3,
    "bars": 2346,
    "sync_records": 0
  },
  "capabilities": [
    {
      "key": "market_catalog",
      "label": "AAPL / SPY / QQQ symbol catalog",
      "status": "ready"
    }
  ]
}
```

## Market provider endpoints

### `GET /api/v1/market/providers`

Returns capabilities, not a promise that an external network endpoint is currently reachable.

```json
{
  "total": 3,
  "providers": [
    {
      "provider": "csv",
      "status": "ready",
      "configured": true,
      "supports_sync": true,
      "notes": "Deterministic offline CSV fixtures for AAPL, SPY, and QQQ."
    },
    {
      "provider": "yfinance",
      "status": "ready",
      "configured": true,
      "supports_sync": true,
      "notes": "Optional network provider. Raw OHLC plus adjusted close are cached locally."
    },
    {
      "provider": "finmind",
      "status": "reserved",
      "configured": false,
      "supports_sync": false,
      "notes": "Adapter boundary reserved for TaiwanStockPrice in a later phase."
    }
  ]
}
```

## Symbol catalog

### `GET /api/v1/market/symbols`

Optional query parameters:

| Parameter | Type | Example |
|---|---|---|
| `market` | string | `US` |
| `asset_type` | string | `etf` |

Response excerpt:

```json
{
  "total": 3,
  "symbols": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "market": "US",
      "asset_type": "equity",
      "exchange": "NASDAQ",
      "currency": "USD",
      "timezone": "America/New_York",
      "default_provider": "yfinance",
      "supported_providers": ["yfinance", "csv"],
      "is_demo": true,
      "cached_bar_count": 782,
      "first_cached_date": "2023-01-03",
      "last_cached_date": "2025-12-31",
      "cached_providers": ["csv"]
    }
  ],
  "providers": []
}
```

## Cached OHLCV

### `GET /api/v1/market/ohlcv`

Query parameters:

| Parameter | Required | Notes |
|---|:---:|---|
| `symbol` | yes | case-insensitive catalog symbol |
| `start` | no | inclusive date |
| `end` | no | inclusive date |
| `interval` | no | Phase 1 accepts only `1d` |

Example:

```http
GET /api/v1/market/ohlcv?symbol=AAPL&start=2023-01-03&end=2023-01-09
```

Response excerpt:

```json
{
  "symbol": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "currency": "USD",
    "timezone": "America/New_York",
    "cached_bar_count": 782,
    "first_cached_date": "2023-01-03",
    "last_cached_date": "2025-12-31",
    "cached_providers": ["csv"]
  },
  "interval": "1d",
  "requested_range": {
    "start": "2023-01-03",
    "end": "2023-01-09"
  },
  "effective_range": {
    "start": "2023-01-03",
    "end": "2023-01-09"
  },
  "source": {
    "providers": ["csv"],
    "datasets": ["qsal-synthetic-offline-v1"],
    "served_from_cache": true,
    "retrieved_at": "2026-06-25T00:00:00Z",
    "source_timezone": "America/New_York",
    "currency": "USD",
    "adjustment": "raw_ohlc_with_adjusted_close",
    "contains_fixture_data": true
  },
  "count": 5,
  "warnings": [
    {
      "code": "synthetic_fixture_data",
      "severity": "info",
      "message": "This response includes deterministic offline fixture rows. They are not observed, live, or current market data.",
      "affected_rows": 0,
      "context": {}
    }
  ],
  "bars": [
    {
      "date": "2023-01-03",
      "open": 132.5807,
      "high": 136.7002,
      "low": 131.6131,
      "close": 135.6244,
      "adjusted_close": 132.2338,
      "volume": 91052081,
      "provider": "csv",
      "is_fixture_data": true
    }
  ]
}
```

Possible warning codes:

| Code | Meaning |
|---|---|
| `synthetic_fixture_data` | response contains synthetic offline rows |
| `requested_start_not_available` | cache begins after requested start |
| `requested_end_not_available` | cache ends before requested end |
| `mixed_sources` | range combines more than one provider |
| `duplicate_dates_removed` | normalizer kept the last duplicate date |
| `invalid_rows_removed` | invalid OHLCV rows were discarded |
| `provider_notice` | provider-specific research/fixture notice |
| `provider_fallback_used` | requested provider failed and fallback succeeded |

## Synchronization

### `POST /api/v1/market/sync`

Request:

```json
{
  "symbols": ["AAPL", "SPY"],
  "provider": "auto",
  "start": "2023-01-03",
  "end": "2023-01-31",
  "allow_fallback": true
}
```

Accepted provider values:

```text
auto | csv | yfinance | finmind
```

With `allow_fallback: true`, `auto` uses the sequence `yfinance → csv`. With fallback disabled, `auto` attempts only yfinance and reports an explicit failure if it is unavailable. A specifically requested non-CSV provider can also fall back to CSV only when `allow_fallback` is true. FinMind is intentionally reserved, so a request with fallback disabled produces a failed result without crashing a multi-symbol batch.

Response:

```json
{
  "run_id": "sync_c245aab2f697",
  "status": "success",
  "requested_range": {
    "start": "2023-01-03",
    "end": "2023-01-31"
  },
  "results": [
    {
      "symbol": "AAPL",
      "status": "success",
      "requested_provider": "auto",
      "provider_used": "csv",
      "fallback_used": true,
      "bars_received": 21,
      "bars_stored": 21,
      "effective_range": {
        "start": "2023-01-03",
        "end": "2023-01-31"
      },
      "is_fixture_data": true,
      "warnings": [
        {
          "code": "provider_notice",
          "severity": "info",
          "message": "Bundled CSV rows are deterministic synthetic fixtures for offline engineering tests; they are not observed market data.",
          "affected_rows": 0,
          "context": {}
        },
        {
          "code": "provider_fallback_used",
          "severity": "warning",
          "message": "The requested provider failed; csv was used as a fallback.",
          "affected_rows": 0,
          "context": {
            "attempts": ["yfinance: yfinance could not retrieve market data."]
          }
        }
      ],
      "attempts": [
        "yfinance: yfinance could not retrieve market data.",
        "csv: success"
      ],
      "error": null
    }
  ],
  "successful": 1,
  "failed": 0
}
```

Synchronization is synchronous in Phase 1. Long-running task queues and progress streaming are deferred until a later Agent/backtest phase.
