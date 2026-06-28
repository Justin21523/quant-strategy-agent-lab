from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.scanner import ScanStatus, SortDirection
from app.schemas.quality import DataQualityGateRequest


class ScannerRulesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    rsi_min: float = Field(default=40.0, ge=0, le=100)
    rsi_max: float = Field(default=70.0, ge=0, le=100)
    volume_ratio_20d_min: float = Field(default=1.0, ge=0)
    return_20d_min_pct: float = 0.0
    return_60d_min_pct: float = 0.0
    return_252d_min_pct: float = 0.0
    atr_pct_max: float = Field(default=12.0, ge=0)

    @model_validator(mode="after")
    def validate_range(self) -> ScannerRulesRequest:
        if self.rsi_min > self.rsi_max:
            raise ValueError("rsi_min must be less than or equal to rsi_max")
        return self


class ScanRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    universe_id: str = "us_common_stocks"
    start: date
    end: date
    rules: ScannerRulesRequest = Field(default_factory=ScannerRulesRequest)
    quality_gate: DataQualityGateRequest | None = None
    sort_key: str = "return_60d_pct"
    sort_direction: SortDirection = SortDirection.DESC
    result_limit: int = Field(default=100, ge=1, le=500)


class ScanResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    symbol: str
    name: str
    exchange: str
    metrics: dict[str, float | int | None]
    matched_rules: list[str]
    failed_rules: list[str]
    warnings: list[str]


class SkippedSymbolResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    name: str
    reason: str
    cached_rows: int = Field(ge=0)
    required_rows: int = Field(ge=0)
    details: dict[str, object] = Field(default_factory=dict)


class ScanRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    universe_id: str
    start: date
    end: date
    rules: ScannerRulesRequest
    sort_key: str
    sort_direction: SortDirection
    result_limit: int
    status: ScanStatus
    total_symbols: int = Field(ge=0)
    analyzed_symbols: int = Field(ge=0)
    matched_symbols: int = Field(ge=0)
    skipped_symbols: int = Field(ge=0)
    warnings: list[str]
    created_at: datetime
    results: list[ScanResultResponse]
    skipped: list[SkippedSymbolResponse]


class ScannerCapabilityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_sort_key: Literal["return_60d_pct"]
    sortable_keys: list[str]
    default_rules: ScannerRulesRequest


class ScannerPresetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset_id: str
    name: str
    description: str
    rules: ScannerRulesRequest


class ScannerPresetListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    presets: list[ScannerPresetResponse]


class ScanRunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    runs: list[ScanRunResponse]
