from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SymbolQualityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    name: str
    exchange: str
    cached_bar_count: int = Field(ge=0)
    first_cached_date: date | None
    last_cached_date: date | None
    missing_weekday_count: int = Field(ge=0)
    providers: list[str]
    contains_fixture_data: bool
    supports_sma_200: bool
    supports_return_252d: bool
    warnings: list[str]


class UniverseQualityReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    universe_id: str
    member_count: int = Field(ge=0)
    refreshed_at: datetime
    requested_start: date
    requested_end: date
    covered_symbols: int = Field(ge=0)
    coverage_pct: float = Field(ge=0, le=100)
    fixture_symbols: int = Field(ge=0)
    sma_200_ready_symbols: int = Field(ge=0)
    return_252d_ready_symbols: int = Field(ge=0)
    generated_at: datetime
    symbols: list[SymbolQualityResponse]
