from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.backtest import BacktestStepStatus, BacktestWarningSeverity


class BacktestRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_json: dict[str, Any]


class BacktestWarningResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: BacktestWarningSeverity
    message: str
    context: dict[str, object] = Field(default_factory=dict)


class BacktestAgentStepResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(ge=1)
    key: str
    label: str
    description: str
    status: BacktestStepStatus
    message: str
    detail: dict[str, object] = Field(default_factory=dict)
    duration_ms: float | None = Field(default=None, ge=0)


class BacktestDataSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    market: str
    timeframe: Literal["1d"]
    start: date
    end: date
    bars: int = Field(ge=1)
    providers: list[str]
    datasets: list[str]
    contains_fixture_data: bool


class BacktestDataSourceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: list[str]
    dataset: list[str]
    contains_fixture_data: bool
    effective_start: date
    effective_end: date
    bar_count: int = Field(ge=1)


class BacktestMetricsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_return_pct: float
    annual_return_pct: float | None
    sharpe_ratio: float | None
    max_drawdown_pct: float
    win_rate_pct: float | None
    profit_factor: float | None
    trade_count: int = Field(ge=0)
    exposure_time_pct: float = Field(ge=0, le=100)
    average_trade_return_pct: float | None
    final_equity: float


class BacktestEquityPointResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    equity: float
    cash: float
    position_value: float
    drawdown_pct: float
    in_position: bool = False


class BacktestDrawdownPointResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    drawdown_pct: float


class BacktestTradeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trade_id: str
    legacy_trade_id: int = Field(ge=1)
    side: Literal["long"]
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    shares: int = Field(ge=0)
    quantity: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    holding_period_bars: int = Field(ge=0)
    entry_reason: str
    exit_reason: str
    entry_commission: float = Field(ge=0)
    exit_commission: float = Field(ge=0)
    commission_paid: float = Field(ge=0)
    slippage_paid: float = Field(ge=0)


class BacktestSignalPointResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_id: str
    date: date
    entry_signal: bool
    exit_signal: bool
    entry_reason: str | None
    exit_reason: str | None
    executed_order: Literal["entry", "exit"] | None = None
    side: Literal["buy", "sell"] | None = None
    reason: str | None = None
    status: Literal["none", "scheduled", "executed"] = "none"
    signal_price: float | None = None
    execution_date: date | None = None
    execution_price: float | None = None
    details: dict[str, object] = Field(default_factory=dict)


class BacktestRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    created_at: datetime
    status: Literal["success"]
    strategy_id: str
    strategy_name: str
    symbol: str
    timeframe: Literal["1d"]
    assumptions: dict[str, object]
    data: BacktestDataSummaryResponse
    data_source: BacktestDataSourceResponse
    metrics: BacktestMetricsResponse
    equity_curve: list[BacktestEquityPointResponse]
    drawdown_curve: list[BacktestDrawdownPointResponse]
    trades: list[BacktestTradeResponse]
    signals: list[BacktestSignalPointResponse]
    warnings: list[BacktestWarningResponse]
    agent_steps: list[BacktestAgentStepResponse]
