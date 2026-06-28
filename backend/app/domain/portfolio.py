from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class RebalanceFrequency(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class PortfolioSelectionMode(StrEnum):
    RESCAN_EACH_PERIOD = "rescan_each_period"
    FIXED_SCAN_RUN = "fixed_scan_run"


class PortfolioRunStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PortfolioEquityPoint:
    date: date
    equity: float
    cash: float
    position_value: float
    drawdown_pct: float


@dataclass(frozen=True, slots=True)
class PortfolioHolding:
    date: date
    symbol: str
    weight: float
    shares: float
    price: float
    value: float


@dataclass(frozen=True, slots=True)
class RebalanceEvent:
    date: date
    selected_symbols: tuple[str, ...]
    excluded_symbols: tuple[str, ...]
    turnover_pct: float
    traded_notional: float
    cost: float
    scan_run_id: str | None = None


@dataclass(frozen=True, slots=True)
class SkippedPeriod:
    date: date
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PortfolioPreset:
    preset_id: str
    name: str
    description: str
    config: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PortfolioRun:
    run_id: str
    status: PortfolioRunStatus
    selection_mode: PortfolioSelectionMode
    universe_id: str
    scanner_preset_id: str | None
    fixed_scan_run_id: str | None
    top_n: int
    frequency: RebalanceFrequency
    start_date: date
    end_date: date
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
    warnings: tuple[str, ...]
    created_at: datetime
    equity_curve: tuple[PortfolioEquityPoint, ...] = field(default_factory=tuple)
    holdings: tuple[PortfolioHolding, ...] = field(default_factory=tuple)
    rebalance_events: tuple[RebalanceEvent, ...] = field(default_factory=tuple)
    skipped_periods: tuple[SkippedPeriod, ...] = field(default_factory=tuple)
