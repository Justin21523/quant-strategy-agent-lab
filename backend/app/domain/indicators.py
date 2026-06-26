from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


class IndicatorKind(StrEnum):
    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"
    ATR = "atr"


class IndicatorPane(StrEnum):
    PRICE = "price"
    OSCILLATOR = "oscillator"
    VOLATILITY = "volatility"


class IndicatorWarningSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class IndicatorSpec:
    key: str
    kind: IndicatorKind
    label: str
    pane: IndicatorPane
    parameters: dict[str, int | float | str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class IndicatorPoint:
    date: date
    values: dict[str, float | None]


@dataclass(frozen=True, slots=True)
class IndicatorSeries:
    key: str
    kind: IndicatorKind
    label: str
    pane: IndicatorPane
    parameters: dict[str, int | float | str]
    warmup_period: int
    values: tuple[IndicatorPoint, ...]


@dataclass(frozen=True, slots=True)
class IndicatorWarning:
    code: str
    severity: IndicatorWarningSeverity
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class IndicatorBundle:
    profile: str
    count: int
    series: tuple[IndicatorSeries, ...]
    warnings: tuple[IndicatorWarning, ...]
