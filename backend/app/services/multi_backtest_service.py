from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from app.domain.errors import (
    MarketDataError,
    MultiBacktestRunNotFoundError,
    ScanRunNotFoundError,
)
from app.domain.multi_backtest import (
    MultiBacktestResult,
    MultiBacktestRun,
    MultiBacktestStatus,
)
from app.domain.strategy import StrategyRenderContext
from app.repositories.market_data_repository import MarketDataRepository
from app.services.backtest_service import BacktestService
from app.services.strategy_template_service import StrategyTemplateService


class MultiBacktestService:
    def __init__(
        self,
        *,
        repository: MarketDataRepository,
        backtest_service: BacktestService,
        strategy_template_service: StrategyTemplateService,
    ) -> None:
        self.repository = repository
        self.backtest_service = backtest_service
        self.strategy_template_service = strategy_template_service

    def run(
        self,
        *,
        scan_run_id: str,
        template_id: str,
        parameters: dict,
        top_n: int,
        start: date,
        end: date,
        initial_cash: float,
        commission: float,
        slippage: float,
    ) -> MultiBacktestRun:
        scan = self.repository.get_scan_run(scan_run_id)
        if scan is None:
            raise ScanRunNotFoundError(
                f"Unknown scanner run: {scan_run_id}",
                details={"scan_run_id": scan_run_id},
            )
        candidates = scan.results[:top_n]
        results: list[MultiBacktestResult] = []
        for candidate in candidates:
            try:
                rendered = self.strategy_template_service.render_template(
                    template_id,
                    parameters=parameters,
                    context=StrategyRenderContext(
                        symbol=candidate.symbol,
                        market="US",
                        timeframe="1d",
                        start=start,
                        end=end,
                        initial_cash=initial_cash,
                        commission=commission,
                        slippage=slippage,
                    ),
                )
                backtest = self.backtest_service.run(rendered.strategy_json)
                final_equity = (
                    backtest.equity_curve[-1].equity if backtest.equity_curve else initial_cash
                )
                metrics = {
                    "total_return_pct": backtest.metrics.total_return_pct,
                    "annual_return_pct": backtest.metrics.annual_return_pct,
                    "sharpe_ratio": backtest.metrics.sharpe_ratio,
                    "max_drawdown_pct": backtest.metrics.max_drawdown_pct,
                    "win_rate_pct": backtest.metrics.win_rate_pct,
                    "profit_factor": backtest.metrics.profit_factor,
                    "trade_count": backtest.metrics.trade_count,
                    "exposure_time_pct": backtest.metrics.exposure_time_pct,
                    "average_trade_return_pct": backtest.metrics.average_trade_return_pct,
                    "final_equity": final_equity,
                }
                results.append(
                    MultiBacktestResult(
                        rank=candidate.rank,
                        symbol=candidate.symbol,
                        status=MultiBacktestStatus.SUCCESS,
                        strategy_name=backtest.strategy_name,
                        metrics=metrics,
                        warnings=tuple(warning.code for warning in backtest.warnings),
                    )
                )
            except MarketDataError as exc:
                results.append(
                    MultiBacktestResult(
                        rank=candidate.rank,
                        symbol=candidate.symbol,
                        status=MultiBacktestStatus.FAILED,
                        strategy_name=template_id,
                        metrics={},
                        warnings=(),
                        error=exc.message,
                    )
                )
        successful = sum(item.status is MultiBacktestStatus.SUCCESS for item in results)
        failed = len(results) - successful
        status = (
            MultiBacktestStatus.SUCCESS
            if failed == 0 and successful > 0
            else MultiBacktestStatus.FAILED
            if successful == 0
            else MultiBacktestStatus.PARTIAL
        )
        run = MultiBacktestRun(
            run_id=f"mbt_{uuid4().hex[:12]}",
            scan_run_id=scan_run_id,
            template_id=template_id,
            top_n=top_n,
            start_date=start,
            end_date=end,
            parameters=parameters,
            initial_cash=initial_cash,
            commission=commission,
            slippage=slippage,
            status=status,
            requested_symbols=len(candidates),
            successful_symbols=successful,
            failed_symbols=failed,
            aggregate=_aggregate(results),
            created_at=datetime.now(UTC).replace(microsecond=0),
            results=tuple(results),
        )
        self.repository.save_multi_backtest_run(run)
        return run

    def get(self, run_id: str) -> MultiBacktestRun:
        run = self.repository.get_multi_backtest_run(run_id)
        if run is None:
            raise MultiBacktestRunNotFoundError(
                f"Unknown multi-asset backtest run: {run_id}",
                details={"run_id": run_id},
            )
        return run

    def list_runs(self, limit: int = 20) -> tuple[MultiBacktestRun, ...]:
        return self.repository.list_multi_backtest_runs(limit=limit)


def _aggregate(results: list[MultiBacktestResult]) -> dict[str, float | int | None]:
    successes = [item for item in results if item.status is MultiBacktestStatus.SUCCESS]
    returns = [float(item.metrics["total_return_pct"]) for item in successes]
    drawdowns = [float(item.metrics["max_drawdown_pct"]) for item in successes]
    sharpes = [
        float(item.metrics["sharpe_ratio"])
        for item in successes
        if item.metrics.get("sharpe_ratio") is not None
    ]
    best = max(successes, key=lambda item: float(item.metrics["total_return_pct"]), default=None)
    worst = min(successes, key=lambda item: float(item.metrics["total_return_pct"]), default=None)
    return {
        "average_total_return_pct": _average(returns),
        "average_max_drawdown_pct": _average(drawdowns),
        "average_sharpe_ratio": _average(sharpes),
        "best_symbol": best.symbol if best else None,
        "best_total_return_pct": float(best.metrics["total_return_pct"]) if best else None,
        "worst_symbol": worst.symbol if worst else None,
        "worst_total_return_pct": float(worst.metrics["total_return_pct"]) if worst else None,
    }


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)
