from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from app.domain.errors import MarketDataError, ScanRunNotFoundError, UniverseNotFoundError
from app.domain.portfolio import (
    PortfolioEquityPoint,
    PortfolioHolding,
    PortfolioPreset,
    PortfolioRun,
    PortfolioRunStatus,
    PortfolioSelectionMode,
    RebalanceEvent,
    RebalanceFrequency,
    SkippedPeriod,
)
from app.domain.quality import DataQualityGate, evaluate_quality_gate
from app.domain.scanner import ScannerRules, SortDirection
from app.repositories.market_data_repository import MarketDataRepository
from app.services.performance_service import PerformanceService
from app.services.scanner_service import SCANNER_PRESETS, ScannerService

ProgressCallback = Callable[[int, int, str], None]

DEFAULT_PORTFOLIO_PRESETS: tuple[PortfolioPreset, ...] = (
    PortfolioPreset(
        preset_id="trend_momentum_monthly_top20",
        name="Trend Momentum Monthly Top 20",
        description="Monthly equal-weight portfolio from the Trend Momentum scanner preset.",
        config={
            "selection_mode": "rescan_each_period",
            "scanner_preset_id": "trend_momentum",
            "frequency": "monthly",
            "top_n": 20,
            "lookback_days": 365,
        },
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    ),
    PortfolioPreset(
        preset_id="low_volatility_trend_monthly_top30",
        name="Low Volatility Trend Monthly Top 30",
        description="Monthly equal-weight portfolio from low-volatility trend candidates.",
        config={
            "selection_mode": "rescan_each_period",
            "scanner_preset_id": "low_volatility_trend",
            "frequency": "monthly",
            "top_n": 30,
            "lookback_days": 365,
        },
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    ),
    PortfolioPreset(
        preset_id="oversold_watchlist_weekly_top10",
        name="Oversold Watchlist Weekly Top 10",
        description="Weekly equal-weight portfolio from oversold watchlist candidates.",
        config={
            "selection_mode": "rescan_each_period",
            "scanner_preset_id": "oversold_watchlist",
            "frequency": "weekly",
            "top_n": 10,
            "lookback_days": 365,
        },
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    ),
)


class PortfolioService:
    def __init__(
        self,
        *,
        repository: MarketDataRepository,
        scanner_service: ScannerService,
        performance_service: PerformanceService,
    ) -> None:
        self.repository = repository
        self.scanner_service = scanner_service
        self.performance_service = performance_service

    def initialize_presets(self) -> None:
        for preset in DEFAULT_PORTFOLIO_PRESETS:
            self.repository.upsert_portfolio_preset(preset)

    def list_presets(self) -> tuple[PortfolioPreset, ...]:
        self.initialize_presets()
        return self.repository.list_portfolio_presets()

    def get_preset(self, preset_id: str) -> PortfolioPreset | None:
        self.initialize_presets()
        return self.repository.get_portfolio_preset(preset_id)

    def save_preset(self, preset: PortfolioPreset) -> None:
        self.repository.upsert_portfolio_preset(preset)

    def list_runs(self, *, limit: int = 20) -> tuple[PortfolioRun, ...]:
        return self.repository.list_portfolio_runs(limit=limit)

    def get_run(self, run_id: str) -> PortfolioRun | None:
        return self.repository.get_portfolio_run(run_id)

    def run_rebalance(
        self,
        *,
        selection_mode: PortfolioSelectionMode,
        universe_id: str,
        start: date,
        end: date,
        frequency: RebalanceFrequency,
        top_n: int,
        initial_cash: float,
        commission: float,
        slippage: float,
        lookback_days: int = 365,
        scanner_preset_id: str | None = None,
        scanner_rules: ScannerRules | None = None,
        fixed_scan_run_id: str | None = None,
        benchmark_symbol: str = "SPY",
        quality_gate: DataQualityGate | None = None,
        progress: ProgressCallback | None = None,
    ) -> PortfolioRun:
        if start > end:
            raise MarketDataError("start must be on or before end", details={})
        universe = self.repository.get_universe(universe_id)
        if universe is None:
            raise UniverseNotFoundError(
                f"Unknown universe: {universe_id}",
                details={"universe_id": universe_id},
            )
        rules = scanner_rules or SCANNER_PRESETS.get(scanner_preset_id or "", ScannerRules())
        all_dates, price_map = self._price_map(
            tuple(member.symbol for member in universe.members),
            start,
            end,
        )
        if not all_dates:
            raise MarketDataError("No cached bars are available for the portfolio date range.")
        rebalance_dates = _rebalance_dates(all_dates, frequency)
        fixed_symbols = (
            self._fixed_symbols(fixed_scan_run_id, top_n)
            if selection_mode is PortfolioSelectionMode.FIXED_SCAN_RUN
            else ()
        )
        warnings = ["fixed_scan_run_static_ranking"] if fixed_symbols else []
        positions: dict[str, float] = {}
        cash = initial_cash
        peak = initial_cash
        equity_curve: list[PortfolioEquityPoint] = []
        holdings: list[PortfolioHolding] = []
        events: list[RebalanceEvent] = []
        skipped_periods: list[SkippedPeriod] = []
        latest_prices: dict[str, float] = {}
        total_steps = len(all_dates)

        for index, current_date in enumerate(all_dates, start=1):
            if progress:
                progress(index, total_steps, f"Portfolio date {current_date.isoformat()}")
            for symbol, by_date in price_map.items():
                if current_date in by_date:
                    latest_prices[symbol] = by_date[current_date]
            current_values = {
                symbol: shares * latest_prices.get(symbol, 0.0)
                for symbol, shares in positions.items()
            }
            equity_before_rebalance = cash + sum(current_values.values())
            if current_date in rebalance_dates:
                selected, excluded, scan_run_id, reason = self._select_symbols(
                    mode=selection_mode,
                    universe_id=universe_id,
                    current_date=current_date,
                    all_dates=all_dates,
                    top_n=top_n,
                    rules=rules,
                    sort_direction=SortDirection.DESC,
                    fixed_symbols=fixed_symbols,
                    price_map=price_map,
                    quality_gate=quality_gate,
                    lookback_days=lookback_days,
                )
                if not selected:
                    skipped_periods.append(
                        SkippedPeriod(
                            date=current_date,
                            reason=reason or "no_valid_symbols",
                            details={"excluded_symbols": excluded},
                        )
                    )
                else:
                    cost_rate = commission + slippage
                    investable = max(0.0, equity_before_rebalance * (1 - cost_rate))
                    target_value = investable / len(selected)
                    target_values = {symbol: target_value for symbol in selected}
                    traded_notional = sum(
                        abs(target_values.get(symbol, 0.0) - current_values.get(symbol, 0.0))
                        for symbol in set(target_values) | set(current_values)
                    )
                    cost = traded_notional * cost_rate
                    positions = {
                        symbol: target_values[symbol] / price_map[symbol][current_date]
                        for symbol in selected
                        if price_map[symbol].get(current_date)
                    }
                    cash = max(0.0, equity_before_rebalance - sum(target_values.values()) - cost)
                    events.append(
                        RebalanceEvent(
                            date=current_date,
                            selected_symbols=tuple(selected),
                            excluded_symbols=tuple(excluded),
                            turnover_pct=(traded_notional / equity_before_rebalance * 100)
                            if equity_before_rebalance
                            else 0.0,
                            traded_notional=round(traded_notional, 4),
                            cost=round(cost, 4),
                            scan_run_id=scan_run_id,
                        )
                    )
            position_value = sum(
                shares * latest_prices.get(symbol, 0.0) for symbol, shares in positions.items()
            )
            equity = cash + position_value
            peak = max(peak, equity)
            drawdown = (equity / peak - 1) * 100 if peak else 0.0
            equity_curve.append(
                PortfolioEquityPoint(
                    date=current_date,
                    equity=round(equity, 4),
                    cash=round(cash, 4),
                    position_value=round(position_value, 4),
                    drawdown_pct=round(drawdown, 4),
                )
            )
            for symbol, shares in positions.items():
                price = latest_prices.get(symbol)
                if price:
                    value = shares * price
                    holdings.append(
                        PortfolioHolding(
                            date=current_date,
                            symbol=symbol,
                            weight=(value / equity) if equity else 0.0,
                            shares=shares,
                            price=price,
                            value=round(value, 4),
                        )
                    )

        performance = self.performance_service.analyze(
            tuple((point.date, point.equity) for point in equity_curve)
        )
        benchmark = self._benchmark_report(benchmark_symbol, start, end, initial_cash)
        perf_dict = self.performance_service.to_dict(performance)
        benchmark_dict = self.performance_service.to_dict(benchmark)
        status = PortfolioRunStatus.SUCCESS if events else PortfolioRunStatus.FAILED
        if events and skipped_periods:
            status = PortfolioRunStatus.PARTIAL
        run = PortfolioRun(
            run_id=f"pf_{uuid4().hex[:12]}",
            status=status,
            selection_mode=selection_mode,
            universe_id=universe_id,
            scanner_preset_id=scanner_preset_id,
            fixed_scan_run_id=fixed_scan_run_id,
            top_n=top_n,
            frequency=frequency,
            start_date=start,
            end_date=end,
            lookback_days=lookback_days,
            initial_cash=initial_cash,
            commission=commission,
            slippage=slippage,
            benchmark_symbol=benchmark_symbol,
            scanner_rules=asdict(rules),
            quality_gate=_quality_gate_dict(quality_gate),
            performance=perf_dict,
            benchmark=benchmark_dict,
            aggregate={
                "final_equity": equity_curve[-1].equity if equity_curve else initial_cash,
                "rebalance_count": len(events),
                "skipped_period_count": len(skipped_periods),
                "average_turnover_pct": _average([item.turnover_pct for item in events]),
                "benchmark_symbol": benchmark_symbol,
                "relative_total_return_pct": (
                    perf_dict["total_return_pct"] - benchmark_dict["total_return_pct"]
                ),
            },
            warnings=tuple(warnings),
            created_at=datetime.now(UTC).replace(microsecond=0),
            equity_curve=tuple(equity_curve),
            holdings=tuple(holdings),
            rebalance_events=tuple(events),
            skipped_periods=tuple(skipped_periods),
        )
        self.repository.save_portfolio_run(run)
        return run

    def _fixed_symbols(self, fixed_scan_run_id: str | None, top_n: int) -> tuple[str, ...]:
        if not fixed_scan_run_id:
            return ()
        scan = self.repository.get_scan_run(fixed_scan_run_id)
        if scan is None:
            raise ScanRunNotFoundError(
                f"Unknown scan run: {fixed_scan_run_id}",
                details={"scan_run_id": fixed_scan_run_id},
            )
        return tuple(result.symbol for result in scan.results[:top_n])

    def _price_map(
        self, symbols: tuple[str, ...], start: date, end: date
    ) -> tuple[list[date], dict[str, dict[date, float]]]:
        price_map: dict[str, dict[date, float]] = {}
        dates: set[date] = set()
        for symbol in symbols:
            bars = self.repository.get_bars(symbol, start=start, end=end)
            if not bars:
                continue
            price_map[symbol] = {bar.trade_date: bar.close for bar in bars}
            dates.update(price_map[symbol])
        return sorted(dates), price_map

    def _select_symbols(
        self,
        *,
        mode: PortfolioSelectionMode,
        universe_id: str,
        current_date: date,
        all_dates: list[date],
        top_n: int,
        rules: ScannerRules,
        sort_direction: SortDirection,
        fixed_symbols: tuple[str, ...],
        price_map: dict[str, dict[date, float]],
        quality_gate: DataQualityGate | None,
        lookback_days: int,
    ) -> tuple[list[str], list[str], str | None, str | None]:
        scan_run_id = None
        previous_dates = [item for item in all_dates if item < current_date]
        scan_end = previous_dates[-1] if previous_dates else current_date
        scan_start = scan_end - timedelta(days=lookback_days)
        if mode is PortfolioSelectionMode.RESCAN_EACH_PERIOD:
            scan = self.scanner_service.run_scan(
                universe_id=universe_id,
                start=scan_start,
                end=scan_end,
                rules=rules,
                sort_direction=sort_direction,
                result_limit=max(top_n * 3, top_n),
                quality_gate=quality_gate,
            )
            scan_run_id = scan.run_id
            candidates = [item.symbol for item in scan.results]
        else:
            candidates = list(fixed_symbols)
        selected: list[str] = []
        excluded: list[str] = []
        expected_weekdays = _weekdays_between(scan_start, scan_end)
        for symbol in candidates:
            if symbol not in price_map or current_date not in price_map[symbol]:
                excluded.append(symbol)
                continue
            bars = self.repository.get_bars(symbol, start=scan_start, end=scan_end)
            gate = evaluate_quality_gate(bars, quality_gate, expected_weekdays=expected_weekdays)
            if not gate.passed:
                excluded.append(symbol)
                continue
            selected.append(symbol)
            if len(selected) >= top_n:
                break
        reason = "no_valid_symbols" if candidates else "no_candidates"
        return selected, excluded, scan_run_id, reason

    def _benchmark_report(self, symbol: str, start: date, end: date, initial_cash: float):
        bars = self.repository.get_bars(symbol, start=start, end=end)
        if not bars:
            return self.performance_service.analyze(())
        first_close = bars[0].close
        values = tuple(
            (bar.trade_date, initial_cash * (bar.close / first_close))
            for bar in bars
            if first_close
        )
        return self.performance_service.analyze(values)


def _rebalance_dates(dates: list[date], frequency: RebalanceFrequency) -> set[date]:
    selected: list[date] = []
    seen: set[tuple[int, int] | tuple[int, int, int]] = set()
    for trade_date in dates:
        key = (
            (trade_date.year, trade_date.month)
            if frequency is RebalanceFrequency.MONTHLY
            else (trade_date.isocalendar().year, trade_date.isocalendar().week, 0)
        )
        if key in seen:
            continue
        seen.add(key)
        selected.append(trade_date)
    return set(selected)


def _weekdays_between(start: date, end: date) -> set[date]:
    current = start
    days: set[date] = set()
    while current <= end:
        if current.weekday() < 5:
            days.add(current)
        current += timedelta(days=1)
    return days


def _average(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def _quality_gate_dict(gate: DataQualityGate | None) -> dict[str, object]:
    if gate is None:
        return {}
    return {
        "min_bars": gate.min_bars,
        "allow_fixture_data": gate.allow_fixture_data,
        "min_last_cached_date": gate.min_last_cached_date.isoformat()
        if gate.min_last_cached_date
        else None,
        "max_missing_weekdays": gate.max_missing_weekdays,
    }
