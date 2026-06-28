from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class MultiBacktestStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class MultiBacktestResult:
    rank: int
    symbol: str
    status: MultiBacktestStatus
    strategy_name: str
    metrics: dict[str, float | int | None]
    warnings: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True, slots=True)
class MultiBacktestRun:
    run_id: str
    scan_run_id: str
    template_id: str
    top_n: int
    start_date: date
    end_date: date
    parameters: dict[str, Any]
    initial_cash: float
    commission: float
    slippage: float
    status: MultiBacktestStatus
    requested_symbols: int
    successful_symbols: int
    failed_symbols: int
    aggregate: dict[str, Any]
    created_at: datetime
    results: tuple[MultiBacktestResult, ...] = field(default_factory=tuple)
