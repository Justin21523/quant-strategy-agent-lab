from __future__ import annotations

from fastapi import APIRouter

from app.domain.agent_workflow import BACKTEST_WORKFLOW_STEPS
from app.domain.backtest import BacktestStepStatus
from app.schemas.agent import AgentWorkflowResponse, AgentWorkflowStepResponse

router = APIRouter(prefix="/agent", tags=["agent workflow"])


@router.get(
    "/backtest-workflow",
    response_model=AgentWorkflowResponse,
    summary="Describe the canonical backtest Agent workflow",
)
def backtest_workflow() -> AgentWorkflowResponse:
    steps = [
        AgentWorkflowStepResponse(
            sequence=step.sequence,
            key=step.key,
            label=step.label,
            description=step.description,
            status=BacktestStepStatus.PENDING,
        )
        for step in BACKTEST_WORKFLOW_STEPS
    ]
    return AgentWorkflowResponse(
        workflow_key="backtest_workflow",
        label="Backtest Agent Timeline",
        phase="phase-6",
        total_steps=len(steps),
        steps=steps,
    )
