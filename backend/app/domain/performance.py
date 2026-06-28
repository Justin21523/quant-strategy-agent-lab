from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class PerformancePoint:
    date: date
    value: float


@dataclass(frozen=True, slots=True)
class MonthlyReturn:
    year: int
    month: int
    return_pct: float


@dataclass(frozen=True, slots=True)
class PerformanceReport:
    total_return_pct: float
    cagr_pct: float | None
    annual_return_pct: float | None
    annual_volatility_pct: float | None
    sharpe_ratio: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None
    max_drawdown_pct: float
    rolling_drawdown: tuple[PerformancePoint, ...]
    monthly_returns: tuple[MonthlyReturn, ...]
