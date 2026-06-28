from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkflowStepDefinition:
    sequence: int
    key: str
    label: str
    description: str


BACKTEST_WORKFLOW_STEPS: tuple[WorkflowStepDefinition, ...] = (
    WorkflowStepDefinition(
        sequence=1,
        key="strategy_received",
        label="Strategy received",
        description="Capture the rendered Strategy JSON DSL and execution assumptions.",
    ),
    WorkflowStepDefinition(
        sequence=2,
        key="validate_strategy",
        label="Strategy validated",
        description="Validate DSL structure, indicator references, and supported rule types.",
    ),
    WorkflowStepDefinition(
        sequence=3,
        key="fetch_market_data",
        label="Market data loaded",
        description="Load normalized OHLCV bars from the SQLite-backed market data layer.",
    ),
    WorkflowStepDefinition(
        sequence=4,
        key="compute_indicators",
        label="Indicators computed",
        description="Build the technical indicator feature frame required by the strategy.",
    ),
    WorkflowStepDefinition(
        sequence=5,
        key="generate_signals",
        label="Signals generated",
        description="Evaluate entry and exit rules on completed bars without look-ahead.",
    ),
    WorkflowStepDefinition(
        sequence=6,
        key="run_backtest",
        label="Backtest executed",
        description="Apply deterministic long-only order execution, fees, and slippage.",
    ),
    WorkflowStepDefinition(
        sequence=7,
        key="analyze_performance",
        label="Performance analyzed",
        description="Compute returns, Sharpe, drawdown, exposure, and trade metrics.",
    ),
    WorkflowStepDefinition(
        sequence=8,
        key="risk_review",
        label="Risk notes reviewed",
        description="Summarize data, sample-size, and execution warnings for the run.",
    ),
)


def workflow_step_definition(key: str) -> WorkflowStepDefinition | None:
    return next((step for step in BACKTEST_WORKFLOW_STEPS if step.key == key), None)
