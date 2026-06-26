from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.domain.indicators import (
    IndicatorBundle,
    IndicatorKind,
    IndicatorPane,
    IndicatorPoint,
    IndicatorSeries,
    IndicatorSpec,
    IndicatorWarning,
    IndicatorWarningSeverity,
)
from app.domain.market import MarketBar


@dataclass(frozen=True, slots=True)
class IndicatorCatalogItem:
    kind: IndicatorKind
    label: str
    description: str
    default_parameters: dict[str, int | float | str]
    pane: IndicatorPane


class IndicatorService:
    """Compute deterministic technical indicators from normalized OHLCV bars.

    The service intentionally depends on provider-neutral MarketBar objects, not raw
    yfinance, CSV, or FinMind payloads. That keeps Phase 2 indicator logic reusable by
    the future Strategy DSL, backtest engine, and parameter scanner.
    """

    def catalog(self) -> tuple[IndicatorCatalogItem, ...]:
        return (
            IndicatorCatalogItem(
                kind=IndicatorKind.SMA,
                label="Simple Moving Average",
                description="Rolling arithmetic mean of the selected price source.",
                default_parameters={"window": 20, "source": "close"},
                pane=IndicatorPane.PRICE,
            ),
            IndicatorCatalogItem(
                kind=IndicatorKind.EMA,
                label="Exponential Moving Average",
                description="Exponentially weighted moving average of the selected price source.",
                default_parameters={"window": 20, "source": "close"},
                pane=IndicatorPane.PRICE,
            ),
            IndicatorCatalogItem(
                kind=IndicatorKind.RSI,
                label="Relative Strength Index",
                description="Wilder-style momentum oscillator scaled between 0 and 100.",
                default_parameters={"window": 14, "source": "close"},
                pane=IndicatorPane.OSCILLATOR,
            ),
            IndicatorCatalogItem(
                kind=IndicatorKind.MACD,
                label="Moving Average Convergence/Divergence",
                description="Fast EMA minus slow EMA, with a signal EMA and histogram.",
                default_parameters={"fast": 12, "slow": 26, "signal": 9, "source": "close"},
                pane=IndicatorPane.OSCILLATOR,
            ),
            IndicatorCatalogItem(
                kind=IndicatorKind.BOLLINGER_BANDS,
                label="Bollinger Bands",
                description="Rolling mean plus and minus a standard-deviation envelope.",
                default_parameters={"window": 20, "stddev": 2, "source": "close"},
                pane=IndicatorPane.PRICE,
            ),
            IndicatorCatalogItem(
                kind=IndicatorKind.ATR,
                label="Average True Range",
                description="Wilder-style average of true range for volatility analysis.",
                default_parameters={"window": 14},
                pane=IndicatorPane.VOLATILITY,
            ),
        )

    def default_specs(self) -> tuple[IndicatorSpec, ...]:
        return (
            IndicatorSpec(
                key="sma_20",
                kind=IndicatorKind.SMA,
                label="SMA 20",
                pane=IndicatorPane.PRICE,
                parameters={"window": 20, "source": "close"},
            ),
            IndicatorSpec(
                key="sma_60",
                kind=IndicatorKind.SMA,
                label="SMA 60",
                pane=IndicatorPane.PRICE,
                parameters={"window": 60, "source": "close"},
            ),
            IndicatorSpec(
                key="ema_20",
                kind=IndicatorKind.EMA,
                label="EMA 20",
                pane=IndicatorPane.PRICE,
                parameters={"window": 20, "source": "close"},
            ),
            IndicatorSpec(
                key="rsi_14",
                kind=IndicatorKind.RSI,
                label="RSI 14",
                pane=IndicatorPane.OSCILLATOR,
                parameters={"window": 14, "source": "close"},
            ),
            IndicatorSpec(
                key="macd_12_26_9",
                kind=IndicatorKind.MACD,
                label="MACD 12/26/9",
                pane=IndicatorPane.OSCILLATOR,
                parameters={"fast": 12, "slow": 26, "signal": 9, "source": "close"},
            ),
            IndicatorSpec(
                key="bbands_20_2",
                kind=IndicatorKind.BOLLINGER_BANDS,
                label="Bollinger Bands 20/2",
                pane=IndicatorPane.PRICE,
                parameters={"window": 20, "stddev": 2, "source": "close"},
            ),
            IndicatorSpec(
                key="atr_14",
                kind=IndicatorKind.ATR,
                label="ATR 14",
                pane=IndicatorPane.VOLATILITY,
                parameters={"window": 14},
            ),
        )

    def compute_default_bundle(
        self, bars: Sequence[MarketBar], *, profile: str = "default"
    ) -> IndicatorBundle:
        return self.compute_bundle(bars, specs=self.default_specs(), profile=profile)

    def compute_bundle(
        self,
        bars: Sequence[MarketBar],
        *,
        specs: Sequence[IndicatorSpec],
        profile: str,
    ) -> IndicatorBundle:
        frame = self._frame_from_bars(bars)
        warnings = self._warnings_for_specs(frame, specs)
        series = tuple(self._compute_series(frame, spec) for spec in specs)
        return IndicatorBundle(
            profile=profile, count=len(series), series=series, warnings=tuple(warnings)
        )

    def _compute_series(self, frame: pd.DataFrame, spec: IndicatorSpec) -> IndicatorSeries:
        if spec.kind is IndicatorKind.SMA:
            return self._sma(frame, spec)
        if spec.kind is IndicatorKind.EMA:
            return self._ema(frame, spec)
        if spec.kind is IndicatorKind.RSI:
            return self._rsi(frame, spec)
        if spec.kind is IndicatorKind.MACD:
            return self._macd(frame, spec)
        if spec.kind is IndicatorKind.BOLLINGER_BANDS:
            return self._bollinger_bands(frame, spec)
        if spec.kind is IndicatorKind.ATR:
            return self._atr(frame, spec)
        raise ValueError(f"Unsupported indicator kind: {spec.kind}")

    def _sma(self, frame: pd.DataFrame, spec: IndicatorSpec) -> IndicatorSeries:
        window = _positive_int(spec.parameters.get("window"), "window")
        source = _source_name(spec.parameters.get("source", "close"))
        values = frame[source].rolling(window=window, min_periods=window).mean()
        return _series(spec, warmup=window, columns={spec.key: values}, dates=frame["date"])

    def _ema(self, frame: pd.DataFrame, spec: IndicatorSpec) -> IndicatorSeries:
        window = _positive_int(spec.parameters.get("window"), "window")
        source = _source_name(spec.parameters.get("source", "close"))
        values = frame[source].ewm(span=window, adjust=False, min_periods=window).mean()
        return _series(spec, warmup=window, columns={spec.key: values}, dates=frame["date"])

    def _rsi(self, frame: pd.DataFrame, spec: IndicatorSpec) -> IndicatorSeries:
        window = _positive_int(spec.parameters.get("window"), "window")
        source = _source_name(spec.parameters.get("source", "close"))
        delta = frame[source].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        average_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
        average_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
        relative_strength = average_gain / average_loss
        raw_rsi = 100 - (100 / (1 + relative_strength))
        rsi = raw_rsi.mask((average_loss == 0) & (average_gain > 0), 100.0)
        rsi = rsi.mask((average_loss == 0) & (average_gain == 0), 50.0)
        return _series(spec, warmup=window, columns={spec.key: rsi}, dates=frame["date"])

    def _macd(self, frame: pd.DataFrame, spec: IndicatorSpec) -> IndicatorSeries:
        fast = _positive_int(spec.parameters.get("fast"), "fast")
        slow = _positive_int(spec.parameters.get("slow"), "slow")
        signal_window = _positive_int(spec.parameters.get("signal"), "signal")
        source = _source_name(spec.parameters.get("source", "close"))
        if fast >= slow:
            raise ValueError("MACD fast period must be smaller than slow period.")
        fast_ema = frame[source].ewm(span=fast, adjust=False, min_periods=fast).mean()
        slow_ema = frame[source].ewm(span=slow, adjust=False, min_periods=slow).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=signal_window, adjust=False, min_periods=signal_window).mean()
        histogram = macd - signal
        return _series(
            spec,
            warmup=slow + signal_window - 1,
            columns={"macd": macd, "signal": signal, "histogram": histogram},
            dates=frame["date"],
        )

    def _bollinger_bands(self, frame: pd.DataFrame, spec: IndicatorSpec) -> IndicatorSeries:
        window = _positive_int(spec.parameters.get("window"), "window")
        stddev = _positive_float(spec.parameters.get("stddev"), "stddev")
        source = _source_name(spec.parameters.get("source", "close"))
        middle = frame[source].rolling(window=window, min_periods=window).mean()
        rolling_std = frame[source].rolling(window=window, min_periods=window).std(ddof=0)
        upper = middle + stddev * rolling_std
        lower = middle - stddev * rolling_std
        return _series(
            spec,
            warmup=window,
            columns={"middle": middle, "upper": upper, "lower": lower},
            dates=frame["date"],
        )

    def _atr(self, frame: pd.DataFrame, spec: IndicatorSpec) -> IndicatorSeries:
        window = _positive_int(spec.parameters.get("window"), "window")
        previous_close = frame["close"].shift(1)
        true_range = pd.concat(
            [
                frame["high"] - frame["low"],
                (frame["high"] - previous_close).abs(),
                (frame["low"] - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = true_range.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
        return _series(spec, warmup=window, columns={spec.key: atr}, dates=frame["date"])

    @staticmethod
    def _frame_from_bars(bars: Sequence[MarketBar]) -> pd.DataFrame:
        frame = pd.DataFrame(
            [
                {
                    "date": bar.trade_date,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "adjusted_close": bar.adjusted_close,
                    "volume": bar.volume,
                }
                for bar in bars
            ]
        )
        if frame.empty:
            raise ValueError("Indicator computation requires at least one OHLCV bar.")
        return frame.sort_values("date").reset_index(drop=True)

    @staticmethod
    def _warnings_for_specs(
        frame: pd.DataFrame,
        specs: Sequence[IndicatorSpec],
    ) -> list[IndicatorWarning]:
        warnings: list[IndicatorWarning] = []
        row_count = len(frame)
        max_warmup = max((_warmup_from_spec(spec) for spec in specs), default=0)
        if row_count < max_warmup:
            warnings.append(
                IndicatorWarning(
                    code="insufficient_warmup_rows",
                    severity=IndicatorWarningSeverity.WARNING,
                    message=(
                        "The selected range is shorter than at least one indicator warm-up period; "
                        "initial values will be null."
                    ),
                    context={"rows": row_count, "required_warmup": max_warmup},
                )
            )
        return warnings


def _warmup_from_spec(spec: IndicatorSpec) -> int:
    if spec.kind is IndicatorKind.MACD:
        slow = _positive_int(spec.parameters.get("slow"), "slow")
        signal = _positive_int(spec.parameters.get("signal"), "signal")
        return slow + signal - 1
    if spec.kind is IndicatorKind.BOLLINGER_BANDS:
        return _positive_int(spec.parameters.get("window"), "window")
    return _positive_int(spec.parameters.get("window", 1), "window")


def _series(
    spec: IndicatorSpec,
    *,
    warmup: int,
    columns: dict[str, pd.Series],
    dates: pd.Series,
) -> IndicatorSeries:
    points = []
    for index, trade_date in enumerate(dates):
        values = {name: _json_number(column.iloc[index]) for name, column in columns.items()}
        points.append(IndicatorPoint(date=trade_date, values=values))
    return IndicatorSeries(
        key=spec.key,
        kind=spec.kind,
        label=spec.label,
        pane=spec.pane,
        parameters=spec.parameters,
        warmup_period=warmup,
        values=tuple(points),
    )


def _json_number(value: object) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result) or pd.isna(result):
        return None
    return result


def _positive_int(value: object, name: str) -> int:
    try:
        result = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if result <= 0:
        raise ValueError(f"{name} must be positive.")
    return result


def _positive_float(value: object, name: str) -> float:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not np.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be positive.")
    return result


def _source_name(value: object) -> str:
    source = str(value)
    if source not in {"open", "high", "low", "close", "adjusted_close"}:
        raise ValueError(f"Unsupported indicator source: {source}")
    return source
