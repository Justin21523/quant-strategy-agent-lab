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

The OHLCV endpoint can optionally include a top-level indicator bundle. Without `include_indicators=true`, the `indicators` field is omitted.

```http
GET /api/v1/market/ohlcv?symbol=AAPL&start=2023-01-03&end=2023-04-10
```

With `include_indicators=true`, the response includes top-level indicator metadata and date-aligned series values.

```http
GET /api/v1/market/ohlcv?symbol=AAPL&start=2023-01-03&end=2023-04-10&include_indicators=true
```

Example indicator bundle shape:

```json
{
  "profile": "default",
  "count": 7,
  "series": [
    {
      "key": "sma_20",
      "kind": "sma",
      "label": "SMA 20",
      "pane": "price",
      "parameters": {"window": 20, "source": "close"},
      "warmup_period": 20,
      "values": [{"date": "2023-01-03", "values": {"sma_20": null}}]
    }
  ],
  "warnings": []
}
```

## Warm-up behavior

Indicators are aligned with the input bars. Values before the indicator has enough data are returned as `null`, not removed. This keeps chart rendering, table previews, and future backtest signal generation aligned by date.

If the selected date range is too short, the indicator bundle adds structured warnings:

```text
insufficient_warmup_rows
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
