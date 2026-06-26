from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.strategy import (
    StrategyIssueSeverity,
    StrategyParameterKind,
    StrategyTemplateCategory,
)

StrategyParameterScalar = int | float | str | bool


class StrategyParameterOptionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: StrategyParameterScalar
    label: str


class StrategyParameterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    kind: StrategyParameterKind
    default: StrategyParameterScalar
    description: str
    minimum: float | None
    maximum: float | None
    step: float | None
    unit: str | None
    options: list[StrategyParameterOptionResponse]


class StrategyTemplateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str
    category: StrategyTemplateCategory
    summary: str
    parameters: list[StrategyParameterResponse]
    tags: list[str]
    indicator_kinds: list[str]
    risk_notes: list[str]
    default_parameters: dict[str, StrategyParameterScalar]
    parameter_count: int = Field(ge=0)
    research_notes: str


class StrategyTemplateListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    templates: list[StrategyTemplateResponse]


class StrategyRenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: str | None = Field(default=None, min_length=1, max_length=80)
    parameters: dict[str, StrategyParameterScalar] = Field(default_factory=dict)
    symbol: str = Field(default="AAPL", min_length=1, max_length=24)
    market: str = Field(default="US", min_length=2, max_length=12)
    timeframe: Literal["1d"] = "1d"
    start: date | None = None
    end: date | None = None
    initial_cash: float = Field(default=100_000.0, gt=0, le=1_000_000_000)
    commission: float = Field(default=0.001, ge=0, le=0.25)
    slippage: float = Field(default=0.0005, ge=0, le=0.25)

    @field_validator("template_id")
    @classmethod
    def normalize_template_id(cls, value: str | None) -> str | None:
        return value.strip().lower().replace("-", "_") if value else value

    @field_validator("symbol", "market")
    @classmethod
    def uppercase_non_empty(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("value cannot be blank")
        return normalized

    @model_validator(mode="after")
    def validate_range(self) -> StrategyRenderRequest:
        if self.start and self.end and self.start > self.end:
            raise ValueError("start must be on or before end")
        return self


class StrategyValidationIssueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: StrategyIssueSeverity
    message: str
    path: str
    context: dict[str, object] = Field(default_factory=dict)


class StrategyValidationReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    issue_count: int = Field(ge=0)
    issues: list[StrategyValidationIssueResponse]


class StrategyRenderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dsl_version: str
    template: StrategyTemplateResponse
    parameters: dict[str, StrategyParameterScalar]
    required_indicators: list[str]
    validation: StrategyValidationReportResponse
    strategy_json: dict[str, Any]


class StrategyValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_json: dict[str, Any]
