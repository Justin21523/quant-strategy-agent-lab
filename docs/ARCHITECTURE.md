# Architecture — Phase 3

Phase 3 keeps the system intentionally layered: market data is normalized first, indicators are computed from normalized bars, and strategy templates render declarative Strategy JSON DSL documents for the future backtest engine.

## 1. Runtime topology

Development servers use dynamic ports selected by `./scripts/dev.sh` / `make dev`. Use the printed URLs instead of assuming fixed ports.

```mermaid
flowchart LR
    Browser[Browser] -->|ES modules| Vite[Vite dev server<br/>dynamic frontend port]
    Browser -->|/api via Vite proxy| FastAPI[FastAPI<br/>dynamic backend port]
    FastAPI --> Market[MarketDataService]
    FastAPI --> Indicators[IndicatorService]
    FastAPI --> Strategies[StrategyTemplateService]
    Market --> Normalizer[MarketDataNormalizer]
    Market --> CSV[CsvMarketDataProvider]
    Market --> YF[YFinanceMarketDataProvider]
    Market --> FM[FinMindMarketDataProvider reserved]
    Normalizer --> Repo[MarketDataRepository]
    Repo --> SQLite[(SQLite cache)]
    Market --> Indicators
    Strategies --> DSL[Strategy JSON DSL]
    FastAPI --> OpenAPI[Swagger / ReDoc]
```

In production containers, Nginx serves the built frontend and proxies `/api`, `/docs`, and `/redoc` to the backend service.

## 2. Backend dependency direction

```text
main / lifespan
  → API routes and dependencies
    → Pydantic schemas
    → application services
      ├── market data service
      │   ├── provider adapters
      │   ├── normalizer
      │   └── repository → SQLite
      ├── indicator service
      │   └── provider-neutral MarketBar values
      └── strategy template service
          └── deterministic Strategy JSON DSL renderer
```

Rules:

- API routes translate HTTP input/output only; business rules live in services.
- Provider adapters may understand provider payloads, but they do not write to SQLite.
- Only the normalizer creates persistent `MarketBar` rows.
- `IndicatorService` consumes normalized `MarketBar` values only.
- `StrategyTemplateService` does not fetch market data, compute indicators, or execute trades.
- Strategy templates output declarative JSON only; no Python, JavaScript, shell, SQL, or file paths are accepted.

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

## 4. Indicator layer

```mermaid
flowchart LR
    Cache[(SQLite OHLCV cache)] --> MarketService[MarketDataService]
    MarketService --> Bars[MarketBar objects]
    Bars --> IndicatorService[IndicatorService]
    IndicatorService --> Bundle[IndicatorBundle]
    Bundle --> API[OHLCV response with indicators]
    API --> Frontend[Vanilla JS Market + Indicator Lab]
```

Rules:

- indicator points are aligned with the same bars returned by the OHLCV request;
- warm-up values are serialized as `null` instead of fabricated;
- indicator requests are optional so raw market inspection stays lightweight;
- provider-specific DataFrames never leak into the indicator engine.

## 5. Strategy template layer

```mermaid
flowchart LR
    UI[Vanilla JS Strategy Builder] --> ServiceJS[strategy-service.js]
    ServiceJS --> API[FastAPI /api/v1/strategies]
    API --> TemplateService[StrategyTemplateService]
    TemplateService --> Params[Typed parameter normalization]
    TemplateService --> Rules[Template rule renderer]
    TemplateService --> Validator[DSL validator]
    Validator --> DSL[Validated Strategy JSON DSL]
```

Implemented templates:

| Template ID | Category | Role |
|---|---|---|
| `buy_and_hold` | baseline | passive benchmark contract |
| `ma_crossover` | trend following | SMA cross entry/exit |
| `ma_crossover_rsi` | trend following | SMA cross plus RSI filter |
| `rsi_mean_reversion` | mean reversion | oversold/recovery RSI rules |
| `macd_trend_following` | trend following | MACD signal crossover rules |

The strategy layer is the controlled boundary for Phase 4. A backtest runner will consume the DSL; it will not parse random prose or execute arbitrary generated code.

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

The bar primary key is `(symbol, interval, trade_date)`. External synchronization uses upsert semantics. Startup fixture import uses insert-if-missing semantics, so restarting the application does not overwrite synchronized rows with synthetic data.

## 7. Frontend dependency direction

```text
main → app → router/layout/store
             ↓
           pages
        ↙         ↘
 components      services
     ↓              ↓
 chart/preview    API client
```

The global store stays small: route and backend availability. Market series, indicator previews, selected strategy template, typed parameters, validation reports, and rendered JSON are route-local state.

## 8. Failure behavior

- network provider failure does not corrupt the existing cache;
- fallback occurs only when the request enables it;
- unsupported symbols and invalid ranges produce typed domain errors;
- fixture data is always labeled in storage and API output;
- invalid template parameters return structured validation errors;
- DSL validation reports path-specific issues;
- cached read endpoints never silently call the network;
- the Strategy Builder never fabricates a strategy locally when backend rendering fails.

## 9. Phase boundaries

- Phase 1: validated daily OHLCV and provider lineage.
- Phase 2: tested technical indicators from normalized bars.
- Phase 3: deterministic templates render validated Strategy JSON DSL.
- Phase 4: signal generation and backtest execution from the DSL.
