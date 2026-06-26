from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Capability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    status: Literal["ready", "planned"]


class MarketCacheStatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbols: int = Field(ge=0)
    bars: int = Field(ge=0)
    sync_records: int = Field(ge=0)


class SystemInfoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: Literal["1"]
    phase_name: Literal["Market Data Layer"]
    cache: MarketCacheStatsResponse
    capabilities: list[Capability]
