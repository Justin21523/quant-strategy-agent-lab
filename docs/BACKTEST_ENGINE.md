# Backtest Engine Design

> Status: planned for Phase 4. Phase 1 only establishes the normalized market-data input contract.

## Required inputs

Every run must freeze:

- symbol, market, interval, provider lineage, and effective date range;
- selected price field (`close` or `adjusted_close`);
- Strategy DSL version and normalized strategy document;
- initial capital;
- commission and slippage;
- order timing and fill model;
- position sizing and cash constraints;
- warm-up rows;
- benchmark;
- engine version and generation timestamp.

## Timing rule

The MVP will avoid same-bar look-ahead:

```text
signal calculated from bar t close
→ order submitted after bar t
→ fill at bar t+1 open, subject to costs and available cash
```

## Required outputs

- immutable run identifier and assumptions;
- entry/exit signals;
- trade ledger;
- daily cash, holdings, equity, and drawdown series;
- rejected-order diagnostics;
- benchmark curve;
- metric inputs and results.

## Integrity checks

- no indicator may read future rows;
- trade and equity ledgers must reconcile;
- fees and slippage must be visible;
- missing next-bar fills must be deterministic;
- stop-loss gap behavior must be documented;
- repeated runs over the same data and DSL must match;
- fixture-data runs remain visibly labeled.
