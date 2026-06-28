from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.portfolio import (
    PortfolioRunStatus,
    PortfolioSelectionMode,
    RebalanceFrequency,
)
from app.domain.scanner import SortDirection
from app.schemas.quality import DataQualityGateRequest
from app.schemas.scans import ScannerRulesRequest


class PortfolioRebalanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selection_mode: PortfolioSelectionMode = PortfolioSelectionMode.RESCAN_EACH_PERIOD
    universe_id: str = "us_common_stocks"
    scanner_preset_id: str | None = "trend_momentum"
    scanner_rules: ScannerRulesRequest | None = None
    fixed_scan_run_id: str | None = None
    sort_direction: SortDirection = SortDirection.DESC
    top_n: int = Field(default=20, ge=1, le=100)
    frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
    start: date
    end: date
    lookback_days: int = Field(default=365, ge=30, le=1500)
    initial_cash: float = Field(default=100_000.0, gt=0)
    commission: float = Field(default=0.001, ge=0)
    slippage: float = Field(default=0.0005, ge=0)
    benchmark_symbol: str = "SPY"
    quality_gate: DataQualityGateRequest = Field(default_factory=DataQualityGateRequest)

    @model_validator(mode="after")
    def validate_request(self) -> PortfolioRebalanceRequest:
        if self.start > self.end:
            raise ValueError("start must be on or before end")
        if (
            self.selection_mode is PortfolioSelectionMode.FIXED_SCAN_RUN
            and not self.fixed_scan_run_id
        ):
            raise ValueError("fixed_scan_run_id is required for fixed_scan_run mode")
        return self


class PortfolioEquityPointResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    equity: float
    cash: float
    position_value: float
    drawdown_pct: float


class PortfolioHoldingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    symbol: str
    weight: float
    shares: float
    price: float
    value: float


class RebalanceEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    selected_symbols: list[str]
    excluded_symbols: list[str]
    turnover_pct: float
    traded_notional: float
    cost: float
    scan_run_id: str | None


class SkippedPeriodResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    reason: str
    details: dict[str, object]


class PortfolioRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: PortfolioRunStatus
    selection_mode: PortfolioSelectionMode
    universe_id: str
    scanner_preset_id: str | None
    fixed_scan_run_id: str | None
    top_n: int
    frequency: RebalanceFrequency
    start: date
    end: date
    lookback_days: int
    initial_cash: float
    commission: float
    slippage: float
    benchmark_symbol: str
    scanner_rules: dict[str, Any]
    quality_gate: dict[str, Any]
    performance: dict[str, Any]
    benchmark: dict[str, Any]
    aggregate: dict[str, Any]
    warnings: list[str]
    created_at: datetime
    equity_curve: list[PortfolioEquityPointResponse]
    holdings: list[PortfolioHoldingResponse]
    rebalance_events: list[RebalanceEventResponse]
    skipped_periods: list[SkippedPeriodResponse]


class PortfolioRunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    runs: list[PortfolioRunResponse]


class PortfolioPresetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset_id: str
    name: str
    description: str
    config: dict[str, Any]


class PortfolioPresetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset_id: str
    name: str
    description: str
    config: dict[str, Any]
    created_at: datetime


class PortfolioPresetListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    presets: list[PortfolioPresetResponse]
