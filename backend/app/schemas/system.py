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

    phase: Literal["3"]
    phase_name: Literal["Strategy Template System"]
    cache: MarketCacheStatsResponse
    strategy_templates: int = Field(ge=0)
    capabilities: list[Capability]
