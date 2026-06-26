# Strategy JSON DSL — Phase 3 Contract

## Purpose

The Strategy JSON DSL is the safety and reproducibility boundary between a user-facing strategy template and deterministic quantitative code. Phase 3 implements this contract through deterministic templates only. Natural-language parsing and arbitrary code generation remain out of scope.

## Safety principles

- declarative rules only;
- allow-listed template parameters, indicators, operators, sources, and risk controls;
- no Python, JavaScript, SQL, shell commands, imports, or file paths;
- every indicator has a stable identifier;
- rules reference identifiers rather than executable expressions;
- versioned schema and recorded template parameters for every render;
- backend validation is authoritative.

## Implemented templates

| Template ID | Category | Indicators | Entry idea |
|---|---|---|---|
| `buy_and_hold` | baseline | none | enter on first bar |
| `ma_crossover` | trend following | SMA | fast SMA crosses above slow SMA |
| `ma_crossover_rsi` | trend following | SMA, RSI | crossover plus RSI ceiling |
| `rsi_mean_reversion` | mean reversion | RSI | RSI below oversold threshold |
| `macd_trend_following` | trend following | MACD | MACD line crosses above signal |

## Example document

```json
{
  "dsl_version": "1.0",
  "strategy_id": "ma_crossover_rsi",
  "strategy_name": "SMA 20/60 Crossover + RSI Filter",
  "template_id": "ma_crossover_rsi",
  "market": "US",
  "symbol": "AAPL",
  "timeframe": "1d",
  "date_range": {
    "start": "2023-01-03",
    "end": "2025-12-31"
  },
  "capital": {
    "initial_cash": 100000,
    "commission": 0.001,
    "slippage": 0.0005
  },
  "indicators": [
    { "id": "sma_fast", "type": "SMA", "source": "close", "window": 20 },
    { "id": "sma_slow", "type": "SMA", "source": "close", "window": 60 },
    { "id": "rsi", "type": "RSI", "source": "close", "window": 14 }
  ],
  "entry_rules": {
    "operator": "AND",
    "conditions": [
      { "type": "CROSSOVER", "left": "sma_fast", "right": "sma_slow" },
      { "type": "LESS_THAN", "left": "rsi", "right": 70 }
    ]
  },
  "exit_rules": {
    "operator": "OR",
    "conditions": [
      { "type": "CROSSUNDER", "left": "sma_fast", "right": "sma_slow" },
      { "type": "GREATER_THAN", "left": "rsi", "right": 80 }
    ]
  },
  "risk_rules": {
    "stop_loss_pct": 0.08,
    "take_profit_pct": 0.2,
    "max_position_pct": 1.0
  },
  "metadata": {
    "source": "strategy_template_system",
    "template_parameters": {
      "fast_window": 20,
      "slow_window": 60,
      "rsi_window": 14
    },
    "disclaimer": "Educational research output only. Historical backtests do not guarantee future performance."
  }
}
```

## Validation invariants

The Phase 3 validation service checks:

- required top-level fields;
- supported `dsl_version`;
- daily timeframe only (`1d`);
- indicator IDs exist and are unique;
- entry and exit rule groups are non-empty;
- rule operators are `AND` or `OR`;
- rule references point to a known indicator, indicator output, OHLCV field, or number;
- `initial_cash`, `commission`, and `slippage` are non-negative;
- `max_position_pct` is greater than 0 and at most 1.

Template rendering also validates parameter constraints:

- unknown template parameters are rejected;
- numeric parameters must be numeric and inside bounds;
- `fast_window < slow_window` for MA and MACD templates;
- RSI entry thresholds must be ordered correctly.

## API ownership

The Strategy Builder frontend does not construct rule logic locally. It sends the selected template, market context, and typed parameters to:

```text
POST /api/v1/strategies/templates/{template_id}/render
```

The backend returns the authoritative Strategy JSON DSL preview and validation report.

## Natural-language parser rule

A future natural-language parser may propose a DSL document. It may not execute it. The validation service decides whether the document is accepted, rejected, or returned with warnings.
