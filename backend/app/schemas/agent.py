from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.backtest import BacktestStepStatus


class AgentWorkflowStepResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(ge=1)
    key: str
    label: str
    description: str
    status: BacktestStepStatus = BacktestStepStatus.PENDING


class AgentWorkflowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_key: str
    label: str
    phase: str
    total_steps: int = Field(ge=1)
    steps: list[AgentWorkflowStepResponse]
