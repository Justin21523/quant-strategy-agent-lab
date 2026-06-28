from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


class BacktestWarningSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class BacktestStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class BacktestWarning:
    code: str
    severity: BacktestWarningSeverity
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BacktestAgentStep:
    key: str
    status: BacktestStepStatus
    message: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BacktestAssumptions:
    price_field: str
    signal_timing: str
    fill_timing: str
    position_type: str
    max_positions: int
    commission: float
    slippage: float
    forced_final_liquidation: bool


@dataclass(frozen=True, slots=True)
class BacktestSignalPoint:
    date: date
    entry_signal: bool
    exit_signal: bool
    entry_reason: str | None
    exit_reason: str | None
    executed_order: str | None = None


@dataclass(frozen=True, slots=True)
class BacktestTrade:
    trade_id: int
    side: str
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    holding_period_bars: int
    entry_reason: str
    exit_reason: str
    commission_paid: float
    slippage_paid: float


@dataclass(frozen=True, slots=True)
class BacktestEquityPoint:
    date: date
    equity: float
    cash: float
    position_value: float
    drawdown_pct: float


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    total_return_pct: float
    annual_return_pct: float | None
    sharpe_ratio: float | None
    max_drawdown_pct: float
    win_rate_pct: float | None
    profit_factor: float | None
    trade_count: int
    exposure_time_pct: float
    average_trade_return_pct: float | None


@dataclass(frozen=True, slots=True)
class BacktestDataSource:
    provider: tuple[str, ...]
    dataset: tuple[str, ...]
    contains_fixture_data: bool
    effective_start: date
    effective_end: date
    bar_count: int


@dataclass(frozen=True, slots=True)
class BacktestResult:
    run_id: str
    strategy_id: str
    strategy_name: str
    symbol: str
    timeframe: str
    assumptions: BacktestAssumptions
    data_source: BacktestDataSource
    metrics: BacktestMetrics
    equity_curve: tuple[BacktestEquityPoint, ...]
    drawdown_curve: tuple[BacktestEquityPoint, ...]
    trades: tuple[BacktestTrade, ...]
    signals: tuple[BacktestSignalPoint, ...]
    warnings: tuple[BacktestWarning, ...]
    agent_steps: tuple[BacktestAgentStep, ...]
