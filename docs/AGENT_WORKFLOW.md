# Agent Workflow

## Design goal

The Agent is an observable orchestrator around deterministic tools—not a mysterious narrator that invents a profitable number.

## Planned ordered steps

```text
strategy_received
strategy_parsed
strategy_validated
market_data_loaded
indicators_computed
signals_generated
backtest_executed
performance_analyzed
risk_explained
report_generated
```

## Step record

```json
{
  "step_key": "strategy_validated",
  "status": "success",
  "started_at": "2026-06-25T12:00:00Z",
  "finished_at": "2026-06-25T12:00:00.120Z",
  "summary": "Strategy DSL passed 14 validation checks.",
  "details": {},
  "warnings": []
}
```

## Status model

- `pending`
- `running`
- `success`
- `warning`
- `failed`
- `cancelled`

## Failure behavior

A failed deterministic tool stops dependent steps. The UI identifies the exact failed step, preserves prior successful evidence, and never asks an LLM to conceal or reinterpret an execution error.

## LLM boundaries

An optional local LLM may:

- map supported language to a draft DSL;
- summarize already-computed metrics;
- explain assumptions and observed failure modes;
- produce report prose from structured evidence.

It may not:

- execute generated code;
- modify historical data;
- replace deterministic metric calculations;
- claim causal certainty from correlation;
- omit data-quality or sample-size warnings.
