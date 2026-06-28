from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.market import MarketBar


@dataclass(frozen=True, slots=True)
class DataQualityGate:
    min_bars: int = 0
    allow_fixture_data: bool = True
    min_last_cached_date: date | None = None
    max_missing_weekdays: int | None = None


@dataclass(frozen=True, slots=True)
class DataQualityGateResult:
    passed: bool
    failures: tuple[str, ...]
    details: dict[str, object]


def evaluate_quality_gate(
    bars: tuple[MarketBar, ...],
    gate: DataQualityGate | None,
    *,
    expected_weekdays: set[date] | None = None,
) -> DataQualityGateResult:
    if gate is None:
        return DataQualityGateResult(passed=True, failures=(), details={})
    failures: list[str] = []
    dates = {bar.trade_date for bar in bars}
    missing_weekdays = len((expected_weekdays or set()) - dates)
    contains_fixture = any(bar.is_fixture_data for bar in bars)
    last_date = bars[-1].trade_date if bars else None
    if len(bars) < gate.min_bars:
        failures.append("min_bars")
    if not gate.allow_fixture_data and contains_fixture:
        failures.append("fixture_data")
    if gate.min_last_cached_date and (last_date is None or last_date < gate.min_last_cached_date):
        failures.append("last_cached_date")
    if gate.max_missing_weekdays is not None and missing_weekdays > gate.max_missing_weekdays:
        failures.append("missing_weekdays")
    return DataQualityGateResult(
        passed=not failures,
        failures=tuple(failures),
        details={
            "cached_rows": len(bars),
            "min_bars": gate.min_bars,
            "contains_fixture_data": contains_fixture,
            "last_cached_date": last_date.isoformat() if last_date else None,
            "min_last_cached_date": gate.min_last_cached_date.isoformat()
            if gate.min_last_cached_date
            else None,
            "missing_weekdays": missing_weekdays,
            "max_missing_weekdays": gate.max_missing_weekdays,
        },
    )
