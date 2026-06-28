from __future__ import annotations

import math
from datetime import date
from statistics import fmean, pstdev

from app.domain.performance import MonthlyReturn, PerformancePoint, PerformanceReport

TRADING_DAYS_PER_YEAR = 252


class PerformanceService:
    def analyze(self, values: tuple[tuple[date, float], ...]) -> PerformanceReport:
        if not values:
            return _empty_report()
        returns = _daily_returns(values)
        first_value = values[0][1]
        last_value = values[-1][1]
        total_return = (last_value / first_value - 1) * 100 if first_value else 0.0
        years = max((values[-1][0] - values[0][0]).days / 365.25, 0)
        cagr = (
            ((last_value / first_value) ** (1 / years) - 1) * 100 if first_value and years else None
        )
        annual_return = fmean(returns) * TRADING_DAYS_PER_YEAR * 100 if returns else None
        volatility = (
            pstdev(returns) * math.sqrt(TRADING_DAYS_PER_YEAR) * 100 if len(returns) > 1 else None
        )
        downside = [item for item in returns if item < 0]
        downside_dev = (
            pstdev(downside) * math.sqrt(TRADING_DAYS_PER_YEAR) if len(downside) > 1 else None
        )
        sharpe = (annual_return / volatility) if annual_return is not None and volatility else None
        sortino = (
            annual_return / (downside_dev * 100)
            if annual_return is not None and downside_dev
            else None
        )
        drawdowns = _drawdowns(values)
        max_drawdown = min((point.value for point in drawdowns), default=0.0)
        calmar = (cagr / abs(max_drawdown)) if cagr is not None and max_drawdown < 0 else None
        return PerformanceReport(
            total_return_pct=round(total_return, 4),
            cagr_pct=_round_optional(cagr),
            annual_return_pct=_round_optional(annual_return),
            annual_volatility_pct=_round_optional(volatility),
            sharpe_ratio=_round_optional(sharpe),
            sortino_ratio=_round_optional(sortino),
            calmar_ratio=_round_optional(calmar),
            max_drawdown_pct=round(max_drawdown, 4),
            rolling_drawdown=tuple(drawdowns),
            monthly_returns=tuple(_monthly_returns(values)),
        )

    def to_dict(self, report: PerformanceReport) -> dict[str, object]:
        return {
            "total_return_pct": report.total_return_pct,
            "cagr_pct": report.cagr_pct,
            "annual_return_pct": report.annual_return_pct,
            "annual_volatility_pct": report.annual_volatility_pct,
            "sharpe_ratio": report.sharpe_ratio,
            "sortino_ratio": report.sortino_ratio,
            "calmar_ratio": report.calmar_ratio,
            "max_drawdown_pct": report.max_drawdown_pct,
            "rolling_drawdown": [
                {"date": point.date.isoformat(), "drawdown_pct": point.value}
                for point in report.rolling_drawdown
            ],
            "monthly_returns": [
                {
                    "year": item.year,
                    "month": item.month,
                    "return_pct": item.return_pct,
                }
                for item in report.monthly_returns
            ],
        }


def _empty_report() -> PerformanceReport:
    return PerformanceReport(
        total_return_pct=0.0,
        cagr_pct=None,
        annual_return_pct=None,
        annual_volatility_pct=None,
        sharpe_ratio=None,
        sortino_ratio=None,
        calmar_ratio=None,
        max_drawdown_pct=0.0,
        rolling_drawdown=(),
        monthly_returns=(),
    )


def _daily_returns(values: tuple[tuple[date, float], ...]) -> list[float]:
    returns = []
    for previous, current in zip(values[:-1], values[1:], strict=True):
        if previous[1]:
            returns.append(current[1] / previous[1] - 1)
    return returns


def _drawdowns(values: tuple[tuple[date, float], ...]) -> list[PerformancePoint]:
    peak = values[0][1] if values else 0.0
    points: list[PerformancePoint] = []
    for trade_date, value in values:
        peak = max(peak, value)
        drawdown = (value / peak - 1) * 100 if peak else 0.0
        points.append(PerformancePoint(date=trade_date, value=round(drawdown, 4)))
    return points


def _monthly_returns(values: tuple[tuple[date, float], ...]) -> list[MonthlyReturn]:
    if not values:
        return []
    grouped: dict[tuple[int, int], list[float]] = {}
    for trade_date, value in values:
        grouped.setdefault((trade_date.year, trade_date.month), []).append(value)
    returns = []
    for (year, month), month_values in sorted(grouped.items()):
        if month_values[0]:
            returns.append(
                MonthlyReturn(
                    year=year,
                    month=month,
                    return_pct=round((month_values[-1] / month_values[0] - 1) * 100, 4),
                )
            )
    return returns


def _round_optional(value: float | None) -> float | None:
    return round(value, 4) if value is not None and math.isfinite(value) else None
