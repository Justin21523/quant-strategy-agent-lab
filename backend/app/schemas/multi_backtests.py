from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.multi_backtest import MultiBacktestStatus


class MultiBacktestRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scan_run_id: str
    template_id: str = "buy_and_hold"
    parameters: dict[str, Any] = Field(default_factory=dict)
    top_n: int = Field(default=10, ge=1, le=100)
    start: date
    end: date
    initial_cash: float = Field(default=100_000.0, gt=0)
    commission: float = Field(default=0.001, ge=0)
    slippage: float = Field(default=0.0005, ge=0)

    @model_validator(mode="after")
    def validate_dates(self) -> MultiBacktestRunRequest:
        if self.start > self.end:
            raise ValueError("start must be on or before end")
        return self


class MultiBacktestResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    symbol: str
    status: MultiBacktestStatus
    strategy_name: str
    metrics: dict[str, float | int | None]
    warnings: list[str]
    error: str | None


class MultiBacktestRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    scan_run_id: str
    template_id: str
    top_n: int = Field(ge=1)
    start: date
    end: date
    parameters: dict[str, Any]
    initial_cash: float
    commission: float
    slippage: float
    status: MultiBacktestStatus
    requested_symbols: int = Field(ge=0)
    successful_symbols: int = Field(ge=0)
    failed_symbols: int = Field(ge=0)
    aggregate: dict[str, object]
    created_at: datetime
    results: list[MultiBacktestResultResponse]


class MultiBacktestRunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    runs: list[MultiBacktestRunResponse]
