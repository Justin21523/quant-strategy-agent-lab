from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class ScanStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True, slots=True)
class ScannerRules:
    enable_close_above_sma_200: bool = True
    enable_sma_20_above_sma_60: bool = True
    enable_rsi_range: bool = True
    enable_volume_ratio_20d: bool = True
    enable_return_20d: bool = False
    enable_return_60d: bool = True
    enable_return_252d: bool = False
    enable_atr_pct_max: bool = False
    close_above_sma_200: bool = True
    sma_20_above_sma_60: bool = True
    rsi_min: float = 40.0
    rsi_max: float = 70.0
    volume_ratio_20d_min: float = 1.0
    return_20d_min_pct: float = 0.0
    return_60d_min_pct: float = 0.0
    return_252d_min_pct: float = 0.0
    atr_pct_max: float = 12.0


@dataclass(frozen=True, slots=True)
class ScanResult:
    rank: int
    symbol: str
    name: str
    exchange: str
    metrics: dict[str, float | int | None]
    matched_rules: tuple[str, ...]
    failed_rules: tuple[str, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SkippedSymbol:
    symbol: str
    name: str
    reason: str
    cached_rows: int
    required_rows: int
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScanRun:
    run_id: str
    universe_id: str
    start_date: date
    end_date: date
    rules: ScannerRules
    sort_key: str
    sort_direction: SortDirection
    result_limit: int
    status: ScanStatus
    total_symbols: int
    analyzed_symbols: int
    matched_symbols: int
    skipped_symbols: int
    warnings: tuple[str, ...]
    created_at: datetime
    results: tuple[ScanResult, ...] = field(default_factory=tuple)
    skipped: tuple[SkippedSymbol, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
