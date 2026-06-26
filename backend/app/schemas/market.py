from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.market import ProviderSelection, SyncStatus, WarningSeverity


class DateRangeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: date | None
    end: date | None


class DataQualityWarningResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: WarningSeverity
    message: str
    affected_rows: int = Field(default=0, ge=0)
    context: dict[str, object] = Field(default_factory=dict)


class ProviderStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    status: Literal["ready", "reserved", "unavailable"]
    configured: bool
    supports_sync: bool
    notes: str


class ProviderListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    providers: list[ProviderStatusResponse]


class SymbolResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    name: str
    market: str
    asset_type: str
    exchange: str
    currency: str
    timezone: str
    default_provider: str
    supported_providers: list[str]
    is_demo: bool
    cached_bar_count: int = Field(ge=0)
    first_cached_date: date | None
    last_cached_date: date | None
    cached_providers: list[str]


class SymbolListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    symbols: list[SymbolResponse]
    providers: list[ProviderStatusResponse]


class OHLCVBarResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int = Field(ge=0)
    provider: str
    is_fixture_data: bool


class DataSourceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providers: list[str]
    datasets: list[str]
    served_from_cache: bool
    retrieved_at: datetime
    source_timezone: str
    currency: str
    adjustment: str
    contains_fixture_data: bool


class OHLCVResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: SymbolResponse
    interval: Literal["1d"]
    requested_range: DateRangeResponse
    effective_range: DateRangeResponse
    source: DataSourceResponse
    count: int = Field(ge=1)
    warnings: list[DataQualityWarningResponse]
    bars: list[OHLCVBarResponse]


class SyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbols: list[str] = Field(min_length=1, max_length=20)
    provider: ProviderSelection = ProviderSelection.AUTO
    start: date
    end: date
    allow_fallback: bool = True

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, values: list[str]) -> list[str]:
        normalized = [value.strip().upper() for value in values if value.strip()]
        if not normalized:
            raise ValueError("at least one non-empty symbol is required")
        return normalized

    @model_validator(mode="after")
    def validate_request(self) -> SyncRequest:
        if self.start > self.end:
            raise ValueError("start must be on or before end")
        if len(set(self.symbols)) != len(self.symbols):
            raise ValueError("symbols must be unique")
        return self


class SymbolSyncResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    status: SyncStatus
    requested_provider: str
    provider_used: str | None
    fallback_used: bool
    bars_received: int = Field(ge=0)
    bars_stored: int = Field(ge=0)
    effective_range: DateRangeResponse
    is_fixture_data: bool
    warnings: list[DataQualityWarningResponse]
    attempts: list[str]
    error: str | None


class SyncResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: Literal["success", "partial", "failed"]
    requested_range: DateRangeResponse
    results: list[SymbolSyncResultResponse]
    successful: int = Field(ge=0)
    failed: int = Field(ge=0)
