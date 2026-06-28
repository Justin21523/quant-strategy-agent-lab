from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class SymbolQuality:
    symbol: str
    name: str
    exchange: str
    cached_bar_count: int
    first_cached_date: date | None
    last_cached_date: date | None
    missing_weekday_count: int
    providers: tuple[str, ...]
    contains_fixture_data: bool
    supports_sma_200: bool
    supports_return_252d: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UniverseQualityReport:
    universe_id: str
    member_count: int
    refreshed_at: datetime
    requested_start: date
    requested_end: date
    covered_symbols: int
    coverage_pct: float
    fixture_symbols: int
    sma_200_ready_symbols: int
    return_252d_ready_symbols: int
    generated_at: datetime
    symbols: tuple[SymbolQuality, ...]
