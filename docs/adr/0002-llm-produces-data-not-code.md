# ADR-0002: LLM produces Strategy DSL, not executable code

- Status: Accepted
- Date: 2026-06-25

The LLM may produce a versioned JSON Strategy DSL with allow-listed indicators, operators, parameters, and risk rules. Pydantic validation and deterministic tools own execution. Arbitrary generated Python is rejected for security, reproducibility, testing, and explainability.
