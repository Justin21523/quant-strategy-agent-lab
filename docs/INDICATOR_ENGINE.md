# Indicator Engine — Phase 2

## Goal

Phase 2 turns normalized OHLCV bars into tested technical features. The indicator engine consumes only provider-neutral `MarketBar` values from the Phase 1 cache. It must not depend on yfinance DataFrames, CSV column names, or future provider-specific formats.

## Implemented indicators

| Indicator | Default key | Method |
|---|---:|---|
| Simple Moving Average | `sma_<window>` | pandas rolling mean |
| Exponential Moving Average | `ema_<window>` | pandas EWM with `adjust=False` |
| Relative Strength Index | `rsi_<window>` | Wilder-style exponential smoothing |
| MACD | `macd_<fast>_<slow>_<signal>_*` | fast EMA minus slow EMA, then signal EMA |
| Bollinger Bands | `bbands_<window>_<std>_*` | rolling mean ± standard deviation multiplier |
| Average True Range | `atr_<window>` | rolling mean of true range |

Default bundle:

```text
sma_20
sma_60
rsi_14
```

Full bundle:

```text
sma_20
sma_60
rsi_14
ema_20
macd_12_26_9_line
macd_12_26_9_signal
macd_12_26_9_histogram
bbands_20_2_middle
bbands_20_2_upper
bbands_20_2_lower
atr_14
```

## API contract

The existing OHLCV endpoint remains backward-compatible. Without `include_indicators=true`, every bar contains an empty `indicators` object.

```http
GET /api/v1/market/ohlcv?symbol=AAPL&start=2023-01-03&end=2023-04-10
```

With `include_indicators=true`, the response includes top-level indicator metadata and per-bar values.

```http
GET /api/v1/market/ohlcv?symbol=AAPL&start=2023-01-03&end=2023-04-10&include_indicators=true
```

Example bar:

```json
{
  "date": "2023-04-10",
  "open": 132.12,
  "high": 133.41,
  "low": 130.78,
  "close": 131.95,
  "adjusted_close": 131.95,
  "volume": 52200100,
  "provider": "csv",
  "is_fixture_data": true,
  "indicators": {
    "sma_20": 133.77299,
    "sma_60": 135.89411333333334,
    "rsi_14": 4.919182122762578
  }
}
```

## Custom syntax

The optional `indicators` query parameter accepts a comma-separated contract:

```text
sma:<window>
ema:<window>
rsi:<window>
atr:<window>
macd:<fast>:<slow>:<signal>
bbands:<window>[:standard_deviations]
```

Example:

```http
GET /api/v1/market/ohlcv?symbol=SPY&include_indicators=true&indicators=sma:10,rsi:7,macd:6:13:5,bbands:20:2,atr:14
```

## Warm-up behavior

Indicators are aligned with the input bars. Values before the indicator has enough data are returned as `null`, not removed. This keeps chart rendering, table previews, and future backtest signal generation aligned by date.

If the selected date range is too short, the API adds structured warnings:

```text
indicator_warmup_exceeds_series
indicator_no_valid_points
```

## Testing policy

Phase 2 includes direct unit tests for every implemented indicator family:

- SMA window mean;
- EMA warm-up and trend tracking;
- RSI on monotonic gains;
- MACD line / signal / histogram outputs;
- Bollinger upper / middle / lower ordering;
- ATR true range;
- custom indicator contract parsing.

API tests cover:

- indicator catalog;
- `include_indicators=true` default bundle;
- custom indicator specs;
- short-range warm-up warnings.
