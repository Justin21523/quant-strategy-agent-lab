from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class ProviderName(StrEnum):
    CSV = "csv"
    YFINANCE = "yfinance"
    FINMIND = "finmind"


class ProviderSelection(StrEnum):
    AUTO = "auto"
    CSV = "csv"
    YFINANCE = "yfinance"
    FINMIND = "finmind"


class AssetType(StrEnum):
    EQUITY = "equity"
    ETF = "etf"
    INDEX = "index"
    UNKNOWN = "unknown"


class WarningSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SyncStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class MarketSymbol:
    symbol: str
    name: str
    market: str
    asset_type: str
    exchange: str
    currency: str
    timezone: str
    default_provider: str = ProviderName.YFINANCE.value
    supported_providers: tuple[str, ...] = (
        ProviderName.YFINANCE.value,
        ProviderName.CSV.value,
    )
    is_demo: bool = True


@dataclass(frozen=True, slots=True)
class SourceBar:
    trade_date: date
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    adjusted_close: float | None
    volume: float | int | None


@dataclass(frozen=True, slots=True)
class MarketBar:
    symbol: str
    interval: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int
    provider: str
    dataset: str
    source_timezone: str
    currency: str
    is_adjusted: bool
    is_fixture_data: bool
    retrieved_at: datetime


@dataclass(frozen=True, slots=True)
class ProviderFetchResult:
    symbol: MarketSymbol
    provider: ProviderName
    dataset: str
    bars: tuple[SourceBar, ...]
    is_adjusted: bool
    is_fixture_data: bool
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DataQualityWarning:
    code: str
    severity: WarningSeverity
    message: str
    affected_rows: int = 0
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    bars: tuple[MarketBar, ...]
    warnings: tuple[DataQualityWarning, ...]


@dataclass(frozen=True, slots=True)
class CachedSymbolSummary:
    symbol: MarketSymbol
    cached_bar_count: int
    first_cached_date: date | None
    last_cached_date: date | None
    cached_providers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MarketCacheStats:
    symbols: int
    bars: int
    sync_records: int


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    provider: str
    status: str
    configured: bool
    supports_sync: bool
    notes: str


@dataclass(frozen=True, slots=True)
class MarketSeries:
    symbol: MarketSymbol
    cache_summary: CachedSymbolSummary
    bars: tuple[MarketBar, ...]
    requested_start: date | None
    requested_end: date | None
    effective_start: date
    effective_end: date
    providers: tuple[str, ...]
    datasets: tuple[str, ...]
    latest_retrieved_at: datetime
    contains_fixture_data: bool
    warnings: tuple[DataQualityWarning, ...]


@dataclass(frozen=True, slots=True)
class SymbolSyncOutcome:
    symbol: str
    status: SyncStatus
    requested_provider: str
    provider_used: str | None
    fallback_used: bool
    bars_received: int
    bars_stored: int
    effective_start: date | None
    effective_end: date | None
    is_fixture_data: bool
    warnings: tuple[DataQualityWarning, ...]
    attempts: tuple[str, ...]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class BatchSyncResult:
    run_id: str
    child_sync_run_id: str
    universe_id: str
    cursor_start: int
    cursor_end: int
    next_cursor: int | None
    complete: bool
    processed: int
    successful: int
    failed: int
    outcomes: tuple[SymbolSyncOutcome, ...]
