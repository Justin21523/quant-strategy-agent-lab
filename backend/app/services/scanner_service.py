from __future__ import annotations

import math
from datetime import UTC, date, datetime
from statistics import fmean
from uuid import uuid4

from app.domain.errors import ScannerExecutionError, ScanRunNotFoundError, UniverseNotFoundError
from app.domain.market import MarketBar
from app.domain.quality import DataQualityGate, evaluate_quality_gate
from app.domain.scanner import (
    ScannerRules,
    ScanResult,
    ScanRun,
    ScanStatus,
    SkippedSymbol,
    SortDirection,
)
from app.repositories.market_data_repository import MarketDataRepository

DEFAULT_SORT_KEY = "return_60d_pct"

SCANNER_PRESETS: dict[str, ScannerRules] = {
    "trend_momentum": ScannerRules(
        rsi_min=45,
        rsi_max=75,
        volume_ratio_20d_min=1.0,
        return_60d_min_pct=5,
        enable_return_252d=True,
        return_252d_min_pct=10,
    ),
    "pullback_in_uptrend": ScannerRules(
        rsi_min=35,
        rsi_max=55,
        volume_ratio_20d_min=0.8,
        return_60d_min_pct=0,
        enable_atr_pct_max=True,
        atr_pct_max=8,
    ),
    "volume_breakout": ScannerRules(
        rsi_min=45,
        rsi_max=85,
        volume_ratio_20d_min=1.8,
        return_20d_min_pct=0,
        enable_return_20d=True,
    ),
    "low_volatility_trend": ScannerRules(
        rsi_min=40,
        rsi_max=70,
        volume_ratio_20d_min=0.8,
        return_60d_min_pct=2,
        enable_atr_pct_max=True,
        atr_pct_max=5,
    ),
    "oversold_watchlist": ScannerRules(
        enable_close_above_sma_200=False,
        enable_sma_20_above_sma_60=False,
        rsi_min=20,
        rsi_max=35,
        volume_ratio_20d_min=0.8,
        enable_return_60d=False,
    ),
}


class ScannerService:
    def __init__(self, repository: MarketDataRepository) -> None:
        self.repository = repository

    def run_scan(
        self,
        *,
        universe_id: str,
        start: date,
        end: date,
        rules: ScannerRules,
        sort_key: str = DEFAULT_SORT_KEY,
        sort_direction: SortDirection = SortDirection.DESC,
        result_limit: int = 100,
        quality_gate: DataQualityGate | None = None,
    ) -> ScanRun:
        if start > end:
            raise ScannerExecutionError(
                "start must be on or before end",
                details={"start": start.isoformat(), "end": end.isoformat()},
            )
        universe = self.repository.get_universe(universe_id)
        if universe is None:
            raise UniverseNotFoundError(
                f"Unknown universe: {universe_id}",
                details={"universe_id": universe_id},
            )
        raw_results: list[ScanResult] = []
        skipped_items: list[SkippedSymbol] = []
        warnings: list[str] = []
        analyzed = 0
        skipped = 0
        required_rows = _required_rows(rules)
        expected_weekdays = _weekdays_between(start, end)
        for member in universe.members:
            bars = self.repository.get_bars(member.symbol, start=start, end=end)
            if not bars:
                skipped += 1
                skipped_items.append(
                    SkippedSymbol(
                        symbol=member.symbol,
                        name=member.name,
                        reason="no_cached_bars",
                        cached_rows=0,
                        required_rows=required_rows,
                    )
                )
                continue
            gate_result = evaluate_quality_gate(
                bars, quality_gate, expected_weekdays=expected_weekdays
            )
            if not gate_result.passed:
                skipped += 1
                skipped_items.append(
                    SkippedSymbol(
                        symbol=member.symbol,
                        name=member.name,
                        reason="quality_gate_failed",
                        cached_rows=len(bars),
                        required_rows=max(required_rows, quality_gate.min_bars)
                        if quality_gate
                        else required_rows,
                        details={
                            "failures": list(gate_result.failures),
                            **gate_result.details,
                        },
                    )
                )
                continue
            if len(bars) < required_rows:
                skipped += 1
                skipped_items.append(
                    SkippedSymbol(
                        symbol=member.symbol,
                        name=member.name,
                        reason="insufficient_cached_rows",
                        cached_rows=len(bars),
                        required_rows=required_rows,
                    )
                )
                continue
            metrics = _metrics_from_bars(bars)
            missing_feature = _missing_feature(metrics, rules)
            if missing_feature:
                skipped += 1
                skipped_items.append(
                    SkippedSymbol(
                        symbol=member.symbol,
                        name=member.name,
                        reason="indicator_not_available",
                        cached_rows=len(bars),
                        required_rows=required_rows,
                        details={"feature": missing_feature},
                    )
                )
                continue
            analyzed += 1
            matched_rules, failed_rules = _evaluate_rules(metrics, rules)
            if failed_rules:
                continue
            raw_results.append(
                ScanResult(
                    rank=0,
                    symbol=member.symbol,
                    name=member.name,
                    exchange=member.exchange,
                    metrics=metrics,
                    matched_rules=tuple(matched_rules),
                    failed_rules=tuple(failed_rules),
                    warnings=(),
                )
            )
        if not raw_results:
            warnings.append("No symbols matched the scanner rules.")
        if sort_key not in _sortable_keys():
            raise ScannerExecutionError(
                "Unsupported scan sort key.",
                details={"sort_key": sort_key, "supported": sorted(_sortable_keys())},
            )
        reverse = sort_direction is SortDirection.DESC
        sorted_results = sorted(
            raw_results,
            key=lambda result: _sort_value(result.metrics.get(sort_key), reverse=reverse),
            reverse=reverse,
        )
        limited = tuple(
            ScanResult(
                rank=index + 1,
                symbol=result.symbol,
                name=result.name,
                exchange=result.exchange,
                metrics=result.metrics,
                matched_rules=result.matched_rules,
                failed_rules=result.failed_rules,
                warnings=result.warnings,
            )
            for index, result in enumerate(sorted_results[:result_limit])
        )
        status = ScanStatus.SUCCESS if analyzed else ScanStatus.FAILED
        if analyzed and skipped:
            status = ScanStatus.PARTIAL
        run = ScanRun(
            run_id=f"scan_{uuid4().hex[:12]}",
            universe_id=universe_id,
            start_date=start,
            end_date=end,
            rules=rules,
            sort_key=sort_key,
            sort_direction=sort_direction,
            result_limit=result_limit,
            status=status,
            total_symbols=len(universe.members),
            analyzed_symbols=analyzed,
            matched_symbols=len(raw_results),
            skipped_symbols=skipped,
            warnings=tuple(warnings),
            created_at=datetime.now(UTC).replace(microsecond=0),
            results=limited,
            skipped=tuple(skipped_items),
        )
        self.repository.save_scan_run(run)
        return run

    def list_scans(self, *, limit: int = 20) -> tuple[ScanRun, ...]:
        return self.repository.list_scan_runs(limit=limit)

    def get_scan(self, run_id: str) -> ScanRun:
        run = self.repository.get_scan_run(run_id)
        if run is None:
            raise ScanRunNotFoundError(f"Unknown scan run: {run_id}", details={"run_id": run_id})
        return run

    def presets(self) -> dict[str, ScannerRules]:
        return SCANNER_PRESETS


def _metrics_from_bars(bars: tuple[MarketBar, ...]) -> dict[str, float | int | None]:
    closes = [bar.close for bar in bars]
    volumes = [bar.volume for bar in bars]
    latest = bars[-1]
    sma_20 = _sma(closes, 20)
    sma_60 = _sma(closes, 60)
    sma_200 = _sma(closes, 200)
    atr_14 = _atr(bars, 14)
    volume_sma_20 = _sma([float(volume) for volume in volumes], 20)
    return {
        "close": latest.close,
        "volume": latest.volume,
        "sma_20": sma_20,
        "sma_60": sma_60,
        "sma_200": sma_200,
        "ema_20": _ema(closes, 20),
        "rsi_14": _rsi(closes, 14),
        "atr_14": atr_14,
        "atr_pct": (atr_14 / latest.close * 100) if atr_14 and latest.close else None,
        "volume_ratio_20d": (latest.volume / volume_sma_20) if volume_sma_20 else None,
        "return_20d_pct": _return_pct(closes, 20),
        "return_60d_pct": _return_pct(closes, 60),
        "return_252d_pct": _return_pct(closes, 252),
    }


def _evaluate_rules(
    metrics: dict[str, float | int | None], rules: ScannerRules
) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    failed: list[str] = []

    def check(name: str, passed: bool) -> None:
        (matched if passed else failed).append(name)

    if rules.enable_close_above_sma_200 and rules.close_above_sma_200:
        check("close_above_sma_200", _gt(metrics["close"], metrics["sma_200"]))
    if rules.enable_sma_20_above_sma_60 and rules.sma_20_above_sma_60:
        check("sma_20_above_sma_60", _gt(metrics["sma_20"], metrics["sma_60"]))
    if rules.enable_rsi_range:
        rsi = metrics["rsi_14"]
        check("rsi_range", rsi is not None and rules.rsi_min <= float(rsi) <= rules.rsi_max)
    if rules.enable_volume_ratio_20d:
        check("volume_ratio_20d", _gte(metrics["volume_ratio_20d"], rules.volume_ratio_20d_min))
    if rules.enable_return_20d:
        check("return_20d", _gt(metrics["return_20d_pct"], rules.return_20d_min_pct))
    if rules.enable_return_60d:
        check("return_60d", _gt(metrics["return_60d_pct"], rules.return_60d_min_pct))
    if rules.enable_return_252d:
        check("return_252d", _gt(metrics["return_252d_pct"], rules.return_252d_min_pct))
    if rules.enable_atr_pct_max:
        check("atr_pct_max", _lte(metrics["atr_pct"], rules.atr_pct_max))
    return matched, failed


def _sma(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return fmean(values[-window:])


def _ema(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    alpha = 2 / (window + 1)
    value = fmean(values[:window])
    for item in values[window:]:
        value = item * alpha + value * (1 - alpha)
    return value


def _rsi(values: list[float], window: int) -> float | None:
    if len(values) <= window:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for previous, current in zip(values[-window - 1 : -1], values[-window:], strict=True):
        change = current - previous
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    average_gain = fmean(gains)
    average_loss = fmean(losses)
    if average_loss == 0 and average_gain > 0:
        return 100.0
    if average_loss == 0:
        return 50.0
    relative_strength = average_gain / average_loss
    return 100 - (100 / (1 + relative_strength))


def _atr(bars: tuple[MarketBar, ...], window: int) -> float | None:
    if len(bars) <= window:
        return None
    ranges: list[float] = []
    for previous, current in zip(bars[-window - 1 : -1], bars[-window:], strict=True):
        ranges.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    return fmean(ranges)


def _return_pct(values: list[float], lookback: int) -> float | None:
    if len(values) <= lookback or values[-lookback - 1] == 0:
        return None
    return (values[-1] / values[-lookback - 1] - 1) * 100


def _gt(left: float | int | None, right: float | int | None) -> bool:
    return left is not None and right is not None and float(left) > float(right)


def _gte(left: float | int | None, right: float | int | None) -> bool:
    return left is not None and right is not None and float(left) >= float(right)


def _lte(left: float | int | None, right: float | int | None) -> bool:
    return left is not None and right is not None and float(left) <= float(right)


def _sort_value(value: float | int | None, *, reverse: bool) -> float:
    if value is None or not math.isfinite(float(value)):
        return -math.inf if reverse else math.inf
    return float(value)


def _sortable_keys() -> set[str]:
    return {
        "close",
        "volume",
        "sma_20",
        "sma_60",
        "sma_200",
        "ema_20",
        "rsi_14",
        "atr_14",
        "atr_pct",
        "volume_ratio_20d",
        "return_20d_pct",
        "return_60d_pct",
        "return_252d_pct",
    }


def _required_rows(rules: ScannerRules) -> int:
    required = 1
    if rules.enable_close_above_sma_200 and rules.close_above_sma_200:
        required = max(required, 200)
    if rules.enable_sma_20_above_sma_60 and rules.sma_20_above_sma_60:
        required = max(required, 60)
    if rules.enable_rsi_range:
        required = max(required, 15)
    if rules.enable_volume_ratio_20d:
        required = max(required, 20)
    if rules.enable_return_20d:
        required = max(required, 21)
    if rules.enable_return_60d:
        required = max(required, 61)
    if rules.enable_return_252d:
        required = max(required, 253)
    if rules.enable_atr_pct_max:
        required = max(required, 15)
    return required


def _missing_feature(metrics: dict[str, float | int | None], rules: ScannerRules) -> str | None:
    required_keys = []
    if rules.enable_close_above_sma_200 and rules.close_above_sma_200:
        required_keys.append("sma_200")
    if rules.enable_sma_20_above_sma_60 and rules.sma_20_above_sma_60:
        required_keys.extend(["sma_20", "sma_60"])
    if rules.enable_rsi_range:
        required_keys.append("rsi_14")
    if rules.enable_volume_ratio_20d:
        required_keys.append("volume_ratio_20d")
    if rules.enable_return_20d:
        required_keys.append("return_20d_pct")
    if rules.enable_return_60d:
        required_keys.append("return_60d_pct")
    if rules.enable_return_252d:
        required_keys.append("return_252d_pct")
    if rules.enable_atr_pct_max:
        required_keys.append("atr_pct")
    return next((key for key in required_keys if metrics.get(key) is None), None)


def _weekdays_between(start: date, end: date) -> set[date]:
    from datetime import timedelta

    current = start
    days: set[date] = set()
    while current <= end:
        if current.weekday() < 5:
            days.add(current)
        current += timedelta(days=1)
    return days
