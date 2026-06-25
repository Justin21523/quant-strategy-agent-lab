# Backtest Engine Design Notes

## Status

Planned for Phase 4. This document records invariants early so the UI cannot dictate incorrect financial semantics later.

## Required inputs

- normalized OHLCV bars with source and timezone metadata;
- validated Strategy JSON DSL;
- initial cash and position-sizing rule;
- commission and slippage assumptions;
- execution timing convention;
- benchmark definition.

## Execution questions that must be explicit

- Is a signal calculated on close and filled on the next open, or filled on the same close?
- Can multiple positions overlap?
- Are fractional shares permitted?
- How are gaps through stop prices handled?
- Are dividends and splits included in the series?
- What occurs when volume or price is missing?

The first engine will prefer conservative, understandable assumptions over maximum flexibility.

## Required outputs

```text
run metadata
strategy snapshot
warnings
signal series
trade ledger
equity series
drawdown series
benchmark series
summary metrics
engine version
```

## Integrity rules

- no look-ahead access to future bars;
- warm-up periods cannot trade before all required indicators are valid;
- transaction costs are applied on every fill;
- cash and positions reconcile after each event;
- trade ledger totals reconcile to final equity;
- no silent replacement of NaN or infinite values;
- identical input data and configuration must produce identical output.

## Testing strategy

Hand-calculated tiny datasets will be used before real provider data. Tests must cover no-trade, one-trade, losing-trade, gap, warm-up, cost, and end-of-data cases.
