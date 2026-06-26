from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.domain.indicators import IndicatorKind, IndicatorPane, IndicatorWarningSeverity


class IndicatorCatalogItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: IndicatorKind
    label: str
    description: str
    default_parameters: dict[str, int | float | str]
    pane: IndicatorPane


class IndicatorCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    indicators: list[IndicatorCatalogItemResponse]


class IndicatorWarningResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: IndicatorWarningSeverity
    message: str
    context: dict[str, object] = Field(default_factory=dict)


class IndicatorPointResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    values: dict[str, float | None]


class IndicatorSeriesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    kind: IndicatorKind
    label: str
    pane: IndicatorPane
    parameters: dict[str, int | float | str]
    warmup_period: int = Field(ge=0)
    values: list[IndicatorPointResponse]


class IndicatorBundleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: str
    count: int = Field(ge=0)
    series: list[IndicatorSeriesResponse]
    warnings: list[IndicatorWarningResponse]
