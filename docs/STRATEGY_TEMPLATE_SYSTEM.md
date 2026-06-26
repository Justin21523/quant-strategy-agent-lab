# Strategy Template System — Phase 3

Phase 3 adds a deterministic strategy-template layer between the Phase 2 indicator engine and the future Phase 4 backtest engine.

The design rule is strict: **templates render declarative Strategy JSON DSL only. They never generate or execute arbitrary Python code.**

## Implemented templates

| Template ID | Category | Purpose |
|---|---|---|
| `buy_and_hold` | baseline | Enter once and hold to the final bar; useful as a passive benchmark. |
| `ma_crossover` | trend following | Buy when fast SMA crosses above slow SMA; exit on the reverse cross. |
| `ma_crossover_rsi` | trend following | MA crossover entry filtered by RSI ceiling. |
| `rsi_mean_reversion` | mean reversion | Buy oversold RSI and exit after RSI recovers. |
| `macd_trend_following` | trend following | Buy MACD line crossover above signal; exit on reverse cross. |

## Backend modules

```text
backend/app/domain/strategy.py
backend/app/services/strategy_template_service.py
backend/app/schemas/strategies.py
backend/app/api/routes/strategies.py
```

## API endpoints

```http
GET  /api/v1/strategies/templates
GET  /api/v1/strategies/templates/{template_id}
POST /api/v1/strategies/templates/{template_id}/render
POST /api/v1/strategies/render
POST /api/v1/strategies/validate
```

`POST /api/v1/strategies/render` accepts the `template_id` in the request body. The path-based render endpoint is convenient for a selected UI template.

## Render request

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

## Response shape

```json
{
  "dsl_version": "1.0",
  "template": {},
  "parameters": {},
  "required_indicators": ["sma_fast", "sma_slow", "rsi"],
  "validation": {
    "valid": true,
    "issue_count": 0,
    "issues": []
  },
  "strategy_json": {}
}
```

## Validation scope

The validator checks:

- top-level DSL fields;
- supported DSL version;
- daily timeframe only;
- unique indicator IDs;
- rule group operator is `AND` or `OR`;
- condition references point to known indicators or price fields;
- capital assumptions are non-negative;
- `max_position_pct` is greater than 0 and at most 1.

Parameter normalization also rejects:

- unknown template parameters;
- values outside parameter min/max ranges;
- unsupported select options;
- fast moving-average windows greater than or equal to slow windows;
- RSI entry thresholds that conflict with exit thresholds.

## Frontend page

```text
/#/strategy-builder
```

The Vanilla JS Strategy Builder supports:

- template cards;
- typed parameter form;
- symbol context loaded from Phase 1 market catalog;
- live backend render;
- Strategy JSON preview;
- backend validation issue list;
- copy-to-clipboard action;
- research disclaimer.

## Phase 4 handoff

Phase 4 should consume `strategy_json` directly. It should not infer strategy behavior from template names or UI state. The first backtest implementation can focus on these rule primitives:

```text
ENTER_ON_FIRST_BAR
EXIT_ON_LAST_BAR
CROSSOVER
CROSSUNDER
LESS_THAN
GREATER_THAN
```
