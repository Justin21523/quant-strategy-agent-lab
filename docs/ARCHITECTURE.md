# Architecture — Phase 1

## 1. Runtime topology

```mermaid
flowchart LR
    Browser[Browser] -->|ES modules| Vite[Vite :5173]
    Browser -->|/api/v1 via proxy| FastAPI[FastAPI :8000]
    FastAPI --> Service[MarketDataService]
    Service --> Normalizer[MarketDataNormalizer]
    Service --> CSV[CsvMarketDataProvider]
    Service --> YF[YFinanceMarketDataProvider]
    Service --> FM[FinMindMarketDataProvider reserved]
    Normalizer --> Repo[MarketDataRepository]
    Repo --> SQLite[(SQLite)]
    FastAPI --> OpenAPI[Swagger / ReDoc]
```

In production containers, Nginx serves the frontend and proxies `/api` to the backend service.

## 2. Backend dependency direction

```text
main / lifespan
  → API routes and dependencies
    → Pydantic schemas
    → application service
      → provider protocol + provider adapters
      → normalizer
      → repository
        → SQLite
```

Rules:

- API routes may translate HTTP parameters and domain objects, but do not fetch or normalize data themselves.
- Provider adapters may understand provider payloads, but do not write to SQLite.
- Only the normalizer creates persistent `MarketBar` values.
- The service owns fallback order, use-case validation, audit outcomes, and response-level warnings.
- The repository owns SQL and row mapping; it does not call external providers.

## 3. Market-data domain

```mermaid
classDiagram
    class MarketSymbol {
      symbol
      market
      exchange
      currency
      timezone
      supported_providers
    }
    class SourceBar {
      trade_date
      open
      high
      low
      close
      adjusted_close
      volume
    }
    class ProviderFetchResult {
      provider
      dataset
      is_adjusted
      is_fixture_data
      warnings
    }
    class MarketBar {
      symbol
      interval
      trade_date
      OHLCV
      provider
      dataset
      retrieved_at
    }
    class DataQualityWarning {
      code
      severity
      affected_rows
      context
    }

    MarketSymbol --> ProviderFetchResult
    SourceBar --> ProviderFetchResult
    ProviderFetchResult --> MarketBar : normalized into
    ProviderFetchResult --> DataQualityWarning
```

`SourceBar` is deliberately permissive because external data may be missing or malformed. `MarketBar` is strict and can only exist after validation.

## 4. Provider abstraction

All adapters implement the same conceptual contract:

```python
class MarketDataProvider(Protocol):
    name: ProviderName

    def list_symbols(self) -> tuple[MarketSymbol, ...]: ...

    def fetch_ohlcv(
        self,
        symbol: MarketSymbol,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderFetchResult: ...
```

Phase 1 adapters:

| Adapter | State | Role |
|---|---|---|
| CSV | implemented | deterministic offline fixture and fallback |
| yfinance | implemented | optional daily public-history synchronization |
| FinMind | reserved | preserves a clean future Taiwan-market boundary |

## 5. Normalization invariants

A row is persisted only when:

- date is within the requested range;
- open, high, low, close, and adjusted close are finite and positive;
- `high >= max(open, low, close)`;
- `low <= min(open, high, close)`;
- volume is finite and non-negative;
- duplicate dates have been reduced to one row;
- rows are sorted in ascending trading-date order.

Invalid and duplicate counts become typed `DataQualityWarning` values. If no valid rows remain, normalization fails instead of returning a deceptive empty success.

## 6. SQLite model

```mermaid
erDiagram
    SYMBOLS ||--o{ OHLCV_BARS : has
    SYMBOLS ||--o{ MARKET_SYNC_RUNS : audited_by

    SYMBOLS {
      text symbol PK
      text name
      text market
      text asset_type
      text exchange
      text currency
      text timezone
      text default_provider
      text supported_providers_json
      integer is_demo
      text updated_at
    }

    OHLCV_BARS {
      text symbol PK,FK
      text interval PK
      text trade_date PK
      real open
      real high
      real low
      real close
      real adjusted_close
      integer volume
      text provider
      text dataset
      text source_timezone
      text currency
      integer is_adjusted
      integer is_fixture_data
      text retrieved_at
    }

    MARKET_SYNC_RUNS {
      text run_id PK
      text symbol PK,FK
      text requested_provider
      text provider_used
      text status
      integer bars_received
      integer bars_stored
      integer fallback_used
      text warnings_json
      text attempts_json
      text error
      text created_at
    }
```

The bar primary key is `(symbol, interval, trade_date)`. External synchronization uses upsert semantics, so a newer provider row replaces the prior row for that date. Startup fixture import uses insert-if-missing semantics, so restarting the application does not overwrite synchronized rows with synthetic data.

## 7. Read and synchronization flows

### Cached read

```mermaid
sequenceDiagram
    Browser->>FastAPI: GET /market/ohlcv
    FastAPI->>Service: get_series(symbol, range)
    Service->>Repository: get_symbol + get_symbol_summary + get_bars
    Repository-->>Service: full-cache metadata + ordered MarketBar values
    Service->>Service: compute provenance and warnings
    Service-->>FastAPI: MarketSeries
    FastAPI-->>Browser: typed OHLCVResponse
```

### Provider synchronization

```mermaid
sequenceDiagram
    Browser->>FastAPI: POST /market/sync
    FastAPI->>Service: sync(symbols, provider, range)
    Service->>Provider: fetch_ohlcv
    alt provider succeeds
      Provider-->>Service: ProviderFetchResult
    else provider fails and fallback allowed
      Service->>CSV: fetch_ohlcv
      CSV-->>Service: fixture ProviderFetchResult
    end
    Service->>Normalizer: normalize
    Normalizer-->>Service: strict MarketBar values + warnings
    Service->>Repository: upsert bars + record audit
    Repository-->>Service: stored count
    Service-->>Browser: attempts, provider used, fallback, warnings
```

## 8. Frontend dependency direction

```text
main → app → router/layout/store
             ↓
           pages
        ↙         ↘
 components      services
     ↓              ↓
 chart adapter   API client
```

The Market Data page owns transient controls and loaded series. The global store remains limited to application-shell state such as route and backend availability. The chart is an adapter with `element` and `update()` rather than inline SVG logic scattered through the page.

## 9. Failure behavior

- Network provider failure does not corrupt the existing cache.
- Fallback occurs only when the request enables it, and is explicit in the sync response and audit table.
- A failed symbol does not abort the remaining symbols in a batch.
- Unsupported symbols and invalid ranges produce typed errors.
- Cached read endpoints never silently call the network.
- Fixture data is always labeled in both storage and API output.

## 10. Phase boundaries

Phase 1 provides validated daily OHLCV only. Phase 2 consumes `MarketBar` values to calculate indicators. Provider-specific DataFrames must not leak into the indicator engine.
