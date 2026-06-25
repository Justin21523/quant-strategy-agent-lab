# Strategy JSON DSL — Provisional Contract

## Purpose

The Strategy JSON DSL is the safety and reproducibility boundary between a human or LLM description and deterministic quantitative code. Phase 3 will finalize and implement this contract.

## Principles

- declarative rules only;
- allow-listed indicators, operators, sources, and risk controls;
- no Python, JavaScript, SQL, shell commands, imports, or file paths;
- every indicator has a stable identifier;
- rules reference identifiers rather than embedded executable expressions;
- versioned schema and recorded parameters for every run.

## Draft document shape

```json
{
  "dsl_version": "1.0",
  "strategy_name": "MA Crossover with RSI Filter",
  "market": "US",
  "symbol": "AAPL",
  "timeframe": "1d",
  "date_range": {
    "start": "2020-01-01",
    "end": "2025-12-31"
  },
  "capital": {
    "initial_cash": 100000,
    "commission_rate": 0.001,
    "slippage_rate": 0.0005
  },
  "indicators": [
    { "id": "fast", "type": "SMA", "source": "close", "window": 20 },
    { "id": "slow", "type": "SMA", "source": "close", "window": 60 },
    { "id": "rsi", "type": "RSI", "source": "close", "window": 14 }
  ],
  "entry": {
    "operator": "AND",
    "conditions": [
      { "type": "CROSSOVER", "left": "fast", "right": "slow" },
      { "type": "LESS_THAN", "left": "rsi", "right": 70 }
    ]
  },
  "exit": {
    "operator": "OR",
    "conditions": [
      { "type": "CROSSUNDER", "left": "fast", "right": "slow" }
    ]
  },
  "risk": {
    "stop_loss_pct": 0.08,
    "take_profit_pct": 0.2,
    "max_position_pct": 1.0
  }
}
```

## Draft validation invariants

- start date must precede end date;
- indicator IDs are unique;
- every referenced indicator exists;
- windows are positive integers and compatible with available observations;
- fast MA must be less than slow MA for the MA crossover template;
- percentages use decimal form and remain inside documented bounds;
- unsupported fields fail validation instead of being silently ignored;
- entry and exit structures cannot be empty unless the selected template explicitly permits it.

## Natural-language parser rule

The parser may propose a DSL document. It may not execute it. The validation service decides whether the document is accepted, rejected, or returned with questions/warnings.
