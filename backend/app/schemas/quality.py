from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class DataQualityGateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_bars: int = Field(default=0, ge=0)
    allow_fixture_data: bool = True
    min_last_cached_date: date | None = None
    max_missing_weekdays: int | None = Field(default=None, ge=0)
