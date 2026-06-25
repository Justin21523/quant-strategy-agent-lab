# Architecture Decision Log

## ADR-001 — Vanilla JavaScript with ES modules

**Status:** accepted

The educational goal is to practice browser fundamentals. Vite supplies development and build tooling, but no UI framework owns rendering, routing, state, or components.

## ADR-002 — FastAPI backend

**Status:** accepted

Python is the primary quantitative ecosystem for later phases. FastAPI provides typed contracts, OpenAPI generation, async-capable endpoints, and a straightforward testing model.

## ADR-003 — Version the API immediately

**Status:** accepted

All application endpoints use `/api/v1` from Phase 0. This prevents early convenience URLs from becoming permanent accidental contracts.

## ADR-004 — No fake quantitative output

**Status:** accepted

Placeholder pages are allowed; fabricated backtest metrics are not. Each capability is marked `ready` or `planned` so reviewers are not misled.

## ADR-005 — LLM output is a constrained DSL, never executable code

**Status:** accepted

The later natural-language parser may emit only allow-listed JSON structures. The backend validates every field before using deterministic indicator and backtest services.

## ADR-006 — Backtest reproducibility over visual spectacle

**Status:** accepted

Every run will eventually store data provenance, date range, costs, execution assumptions, strategy version, parameters, metrics, trades, and warnings before chart polish is considered complete.
