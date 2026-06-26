from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.market import DataQualityWarning, MarketSeries


class IndicatorType(StrEnum):
    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bbands"
    ATR = "atr"


class PriceSource(StrEnum):
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    ADJUSTED_CLOSE = "adjusted_close"


@dataclass(frozen=True, slots=True)
class IndicatorSpec:
    indicator_type: IndicatorType
    window: int | None = None
    source: PriceSource = PriceSource.CLOSE
    identifier: str | None = None
    fast_window: int | None = None
    slow_window: int | None = None
    signal_window: int | None = None
    standard_deviations: float | None = None

    @property
    def key(self) -> str:
        if self.identifier:
            return self.identifier
        if self.indicator_type is IndicatorType.SMA:
            return f"sma_{self.window}"
        if self.indicator_type is IndicatorType.EMA:
            return f"ema_{self.window}"
        if self.indicator_type is IndicatorType.RSI:
            return f"rsi_{self.window}"
        if self.indicator_type is IndicatorType.ATR:
            return f"atr_{self.window}"
        if self.indicator_type is IndicatorType.MACD:
            return f"macd_{self.fast_window}_{self.slow_window}_{self.signal_window}"
        if self.indicator_type is IndicatorType.BOLLINGER_BANDS:
            return f"bbands_{self.window}_{self.standard_deviations:g}"
        return self.indicator_type.value

    @property
    def output_keys(self) -> tuple[str, ...]:
        base_key = self.key
        if self.indicator_type in {
            IndicatorType.SMA,
            IndicatorType.EMA,
            IndicatorType.RSI,
            IndicatorType.ATR,
        }:
            return (base_key,)
        if self.indicator_type is IndicatorType.MACD:
            return (f"{base_key}_line", f"{base_key}_signal", f"{base_key}_histogram")
        if self.indicator_type is IndicatorType.BOLLINGER_BANDS:
            return (f"{base_key}_middle", f"{base_key}_upper", f"{base_key}_lower")
        return (base_key,)

    @property
    def warmup_period(self) -> int:
        if self.indicator_type in {
            IndicatorType.SMA,
            IndicatorType.EMA,
            IndicatorType.RSI,
            IndicatorType.ATR,
            IndicatorType.BOLLINGER_BANDS,
        }:
            return int(self.window or 0)
        if self.indicator_type is IndicatorType.MACD:
            return int((self.slow_window or 0) + (self.signal_window or 0) - 1)
        return 0


@dataclass(frozen=True, slots=True)
class IndicatorPoint:
    date: object
    values: dict[str, float | None]


@dataclass(frozen=True, slots=True)
class IndicatorSeries:
    spec: IndicatorSpec
    output_keys: tuple[str, ...]
    points: tuple[IndicatorPoint, ...]
    warmup_period: int
    valid_points: int
    warnings: tuple[DataQualityWarning, ...] = ()


@dataclass(frozen=True, slots=True)
class IndicatorBundle:
    market_series: MarketSeries
    specs: tuple[IndicatorSpec, ...]
    series: tuple[IndicatorSeries, ...]
    warnings: tuple[DataQualityWarning, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def output_keys(self) -> tuple[str, ...]:
        keys: list[str] = []
        for indicator_series in self.series:
            keys.extend(indicator_series.output_keys)
        return tuple(keys)
