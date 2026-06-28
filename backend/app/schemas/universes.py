from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UniverseMemberResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    name: str
    exchange: str
    asset_type: str
    currency: str
    provider_symbol: str
    is_active: bool


class UniverseSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    universe_id: str
    name: str
    description: str
    market: str
    asset_type: str
    source: str
    source_url: str
    member_count: int = Field(ge=0)
    refreshed_at: datetime


class UniverseListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    universes: list[UniverseSummaryResponse]


class UniverseDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    universe: UniverseSummaryResponse
    members: list[UniverseMemberResponse]


class UniverseRefreshResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    universe: UniverseSummaryResponse
    inserted_symbols: int = Field(ge=0)
    member_count: int = Field(ge=0)
