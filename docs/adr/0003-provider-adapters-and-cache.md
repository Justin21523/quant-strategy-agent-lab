# ADR-003: Provider adapters feed one normalized local cache

- Status: accepted
- Date: 2026-06-25

## Context

Indicators and backtests require stable, reproducible rows. Direct provider calls inside quantitative calculations would leak source-specific schemas, make tests network-dependent, and allow a page refresh to change research inputs unexpectedly.

## Decision

1. Every external source implements a provider protocol.
2. Provider payloads are converted into provider-neutral source bars.
3. One normalizer validates and enriches rows.
4. Normalized rows are persisted in SQLite.
5. Read endpoints serve SQLite only.
6. Synchronization is an explicit audited write action.
7. A deterministic synthetic CSV provider keeps development operational offline.
8. Fallback requires an explicit request flag and is disclosed in the response.

## Consequences

### Positive

- tests are deterministic;
- later indicator/backtest code has one input schema;
- data lineage and adjustment assumptions stay visible;
- network failure does not prevent a portfolio demo;
- provider replacement does not rewrite the frontend.

### Negative

- the cache needs schema and lifecycle management;
- overlapping provider writes require a clear replacement rule;
- the bundled fixture must be unmistakably labeled synthetic;
- real-time and intraday use cases are deferred.
