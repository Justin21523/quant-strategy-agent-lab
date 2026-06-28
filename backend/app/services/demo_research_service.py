from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from app.domain.market import ProviderSelection
from app.domain.portfolio import PortfolioSelectionMode, RebalanceFrequency
from app.domain.quality import DataQualityGate
from app.domain.scanner import ScannerRules
from app.domain.universe import UniverseMember, UniverseSummary
from app.repositories.market_data_repository import MarketDataRepository
from app.services.data_quality_service import DataQualityService
from app.services.market_data_service import MarketDataService
from app.services.multi_backtest_service import MultiBacktestService
from app.services.portfolio_service import PortfolioService
from app.services.scanner_service import ScannerService

DEMO_UNIVERSE_ID = "demo_research_sample"
DEMO_START = date(2023, 1, 3)
DEMO_END = date(2025, 12, 31)
DEMO_PORTFOLIO_END = date(2023, 9, 29)


@dataclass(frozen=True, slots=True)
class DemoResearchRun:
    run_id: str
    summary: dict


class DemoResearchService:
    def __init__(
        self,
        *,
        repository: MarketDataRepository,
        market_data_service: MarketDataService,
        scanner_service: ScannerService,
        data_quality_service: DataQualityService,
        portfolio_service: PortfolioService,
        multi_backtest_service: MultiBacktestService,
    ) -> None:
        self.repository = repository
        self.market_data_service = market_data_service
        self.scanner_service = scanner_service
        self.data_quality_service = data_quality_service
        self.portfolio_service = portfolio_service
        self.multi_backtest_service = multi_backtest_service

    def seed_sample_universe(self) -> dict:
        summaries = [
            item
            for item in self.market_data_service.list_symbols(asset_type="equity")
            if item.symbol != "SPY"
        ][:20]
        members = tuple(
            UniverseMember(
                symbol=item.symbol.symbol,
                name=item.symbol.name,
                exchange=item.symbol.exchange,
                asset_type=item.symbol.asset_type,
                currency=item.symbol.currency,
                provider_symbol=item.symbol.symbol,
                metadata={"demo_role": "sample_equity"},
            )
            for item in summaries
        )
        summary = UniverseSummary(
            universe_id=DEMO_UNIVERSE_ID,
            name="Demo Research Sample",
            description="Deterministic 20-stock synthetic sample universe for in-app automation.",
            market="US",
            asset_type="equity",
            source="qsal_synthetic_fixture",
            source_url="backend/data/seed",
            member_count=len(members),
            refreshed_at=datetime.now(UTC).replace(microsecond=0),
        )
        self.repository.upsert_universe(summary, members)
        return {
            "universe_id": DEMO_UNIVERSE_ID,
            "member_count": len(members),
            "symbols": [member.symbol for member in members],
        }

    def run(self, *, progress=None) -> DemoResearchRun:
        def tick(processed: int, message: str) -> None:
            if progress:
                progress(processed, 7, message)

        started_at = datetime.now(UTC).replace(microsecond=0)
        tick(1, "Preparing deterministic sample universe.")
        universe = self.seed_sample_universe()

        tick(2, "Syncing sample market data from CSV fixtures.")
        sync = self.market_data_service.batch_sync_universe(
            DEMO_UNIVERSE_ID,
            start=DEMO_START,
            end=DEMO_END,
            provider=ProviderSelection.CSV,
            chunk_size=25,
            cursor=0,
            allow_fallback=False,
        )

        tick(3, "Generating data-quality report with pass/fail cases.")
        quality = self.data_quality_service.universe_report(
            DEMO_UNIVERSE_ID,
            start=DEMO_START,
            end=DEMO_END,
            limit=25,
        )

        tick(4, "Running permissive scanner across the sample universe.")
        scan = self.scanner_service.run_scan(
            universe_id=DEMO_UNIVERSE_ID,
            start=DEMO_START,
            end=DEMO_END,
            rules=_permissive_rules(),
            sort_key="return_60d_pct",
            result_limit=20,
            quality_gate=DataQualityGate(
                min_bars=120,
                allow_fixture_data=True,
                max_missing_weekdays=1000,
            ),
        )

        tick(5, "Running portfolio preset matrix.")
        portfolio_runs = []
        for name, frequency, top_n in (
            ("trend_momentum", RebalanceFrequency.MONTHLY, 8),
            ("low_volatility_trend", RebalanceFrequency.MONTHLY, 10),
            ("oversold_watchlist", RebalanceFrequency.WEEKLY, 5),
        ):
            run = self.portfolio_service.run_rebalance(
                selection_mode=PortfolioSelectionMode.FIXED_SCAN_RUN,
                universe_id=DEMO_UNIVERSE_ID,
                start=DEMO_START,
                end=DEMO_PORTFOLIO_END,
                frequency=frequency,
                top_n=top_n,
                initial_cash=100_000,
                commission=0.001,
                slippage=0.0005,
                lookback_days=365,
                scanner_preset_id=name,
                fixed_scan_run_id=scan.run_id,
                benchmark_symbol="SPY",
                quality_gate=DataQualityGate(min_bars=0, allow_fixture_data=True),
            )
            portfolio_runs.append(run)

        tick(6, "Running multi-strategy comparison.")
        multi_runs = []
        for template_id in ("buy_and_hold", "ma_crossover", "macd_trend_following"):
            multi_runs.append(
                self.multi_backtest_service.run(
                    scan_run_id=scan.run_id,
                    template_id=template_id,
                    parameters={},
                    top_n=6,
                    start=DEMO_START,
                    end=DEMO_PORTFOLIO_END,
                    initial_cash=100_000,
                    commission=0.001,
                    slippage=0.0005,
                )
            )

        tick(7, "Finalizing demo research summary.")
        run_id = f"demo_{started_at.strftime('%Y%m%d%H%M%S')}"
        failed_quality = [
            {
                "symbol": item.symbol,
                "warnings": list(item.warnings),
                "cached_bar_count": item.cached_bar_count,
                "missing_weekday_count": item.missing_weekday_count,
            }
            for item in quality.symbols
            if any(
                code in item.warnings
                for code in ("insufficient_sma_200", "insufficient_return_252d")
            )
            or item.missing_weekday_count > 0
        ]
        finished_at = datetime.now(UTC).replace(microsecond=0)
        portfolio_matrix = [_portfolio_summary(item) for item in portfolio_runs]
        strategy_comparison = [_strategy_summary(item) for item in multi_runs]
        best_portfolio = max(
            portfolio_matrix,
            key=lambda item: float(item.get("total_return_pct") or float("-inf")),
            default={},
        )
        best_strategy = max(
            strategy_comparison,
            key=lambda item: float(item.get("average_total_return_pct") or float("-inf")),
            default={},
        )
        summary = {
            "run_id": run_id,
            "status": "success",
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "universe": universe,
            "sync": {
                "run_id": sync.run_id,
                "processed": sync.processed,
                "successful": sync.successful,
                "failed": sync.failed,
            },
            "quality": {
                "covered_symbols": quality.covered_symbols,
                "member_count": quality.member_count,
                "coverage_pct": quality.coverage_pct,
                "fixture_symbols": quality.fixture_symbols,
                "sma_200_ready_symbols": quality.sma_200_ready_symbols,
                "return_252d_ready_symbols": quality.return_252d_ready_symbols,
                "symbols": [_quality_symbol_summary(item) for item in quality.symbols],
                "failed_examples": failed_quality[:6],
            },
            "scanner": {
                "run_id": scan.run_id,
                "matched_symbols": scan.matched_symbols,
                "skipped_symbols": scan.skipped_symbols,
                "top_symbols": [item.symbol for item in scan.results[:8]],
                "results": [_scanner_result_summary(item) for item in scan.results[:10]],
                "skipped": [
                    {
                        "symbol": item.symbol,
                        "reason": item.reason,
                        "cached_rows": item.cached_rows,
                        "required_rows": item.required_rows,
                    }
                    for item in scan.skipped[:8]
                ],
            },
            "portfolio_matrix": portfolio_matrix,
            "strategy_comparison": strategy_comparison,
            "best_portfolio_run_id": best_portfolio.get("run_id"),
            "best_multi_backtest_run_id": best_strategy.get("run_id"),
            "events": _workflow_events(
                started_at=started_at,
                finished_at=finished_at,
                universe=universe,
                sync={
                    "processed": sync.processed,
                    "successful": sync.successful,
                    "failed": sync.failed,
                },
                quality={
                    "coverage_pct": quality.coverage_pct,
                    "failed_examples": len(failed_quality),
                },
                scanner={
                    "matched_symbols": scan.matched_symbols,
                    "skipped_symbols": scan.skipped_symbols,
                },
                portfolio_runs=portfolio_matrix,
                strategy_runs=strategy_comparison,
            ),
        }
        return DemoResearchRun(run_id=run_id, summary=summary)

    def latest_summary(self) -> dict:
        for job in self.repository.list_jobs(limit=100):
            if job.kind.value != "research_demo":
                continue
            summary = self._summary_from_job(job.job_id)
            if summary and summary.get("events"):
                return summary
        return self.snapshot()

    def get_summary(self, run_id: str) -> dict | None:
        for job in self.repository.list_jobs(limit=100):
            summary = self._summary_from_job(job.job_id)
            if summary and summary.get("run_id") == run_id:
                return summary
        return None

    def snapshot(self) -> dict:
        return {
            "run_id": "demo_snapshot",
            "status": "snapshot",
            "universe": {
                "universe_id": DEMO_UNIVERSE_ID,
                "member_count": 20,
                "symbols": ["AAPL", "ALFA", "BRAV", "CHAR", "DELT", "ECHO", "FOXT", "GOLF"],
            },
            "sync": {"processed": 20, "successful": 20, "failed": 0},
            "quality": {
                "covered_symbols": 20,
                "member_count": 20,
                "coverage_pct": 100.0,
                "fixture_symbols": 20,
                "sma_200_ready_symbols": 18,
                "return_252d_ready_symbols": 18,
                "symbols": _snapshot_quality_symbols(),
                "failed_examples": [
                    {
                        "symbol": "ROMO",
                        "warnings": ["insufficient_sma_200", "insufficient_return_252d"],
                        "cached_bar_count": 162,
                        "missing_weekday_count": 620,
                    },
                    {
                        "symbol": "QUEB",
                        "warnings": ["contains_fixture_data"],
                        "cached_bar_count": 736,
                        "missing_weekday_count": 46,
                    },
                ],
            },
            "scanner": {
                "run_id": "scan_snapshot",
                "matched_symbols": 18,
                "skipped_symbols": 2,
                "top_symbols": ["PAPA", "HOTL", "DELT", "KILO", "NOVA", "ALFA"],
                "results": _snapshot_scanner_results(),
                "skipped": [
                    {
                        "symbol": "ROMO",
                        "reason": "quality_gate_failed",
                        "cached_rows": 162,
                        "required_rows": 200,
                    },
                    {
                        "symbol": "SIER",
                        "reason": "insufficient_cached_rows",
                        "cached_rows": 118,
                        "required_rows": 200,
                    },
                ],
            },
            "portfolio_matrix": [
                {
                    "run_id": "pf_snapshot_trend",
                    "preset": "trend_momentum",
                    "frequency": "monthly",
                    "top_n": 8,
                    "total_return_pct": 12.4,
                    "max_drawdown_pct": -5.6,
                    "sharpe_ratio": 1.18,
                    "final_equity": 112400,
                    "annual_return_pct": 15.8,
                    "annual_volatility_pct": 13.1,
                    "turnover_pct": 42.5,
                    "rebalance_count": 8,
                    "skipped_period_count": 0,
                    "equity_curve": _snapshot_curve(
                        100000, [101200, 102900, 101800, 105600, 108200, 110100, 109500, 112400]
                    ),
                    "drawdown_curve": _snapshot_drawdown([0, -0.8, -1.5, -0.4, 0, -0.6, -1.1, 0]),
                },
                {
                    "run_id": "pf_snapshot_low_vol",
                    "preset": "low_volatility_trend",
                    "frequency": "monthly",
                    "top_n": 10,
                    "total_return_pct": 8.9,
                    "max_drawdown_pct": -3.9,
                    "sharpe_ratio": 1.04,
                    "final_equity": 108900,
                    "annual_return_pct": 11.2,
                    "annual_volatility_pct": 9.7,
                    "turnover_pct": 31.2,
                    "rebalance_count": 8,
                    "skipped_period_count": 0,
                    "equity_curve": _snapshot_curve(
                        100000, [100800, 101700, 102600, 104100, 105300, 106700, 107500, 108900]
                    ),
                    "drawdown_curve": _snapshot_drawdown([0, -0.3, -0.8, -0.2, 0, -0.5, -0.7, 0]),
                },
                {
                    "run_id": "pf_snapshot_oversold",
                    "preset": "oversold_watchlist",
                    "frequency": "weekly",
                    "top_n": 5,
                    "total_return_pct": 4.2,
                    "max_drawdown_pct": -7.8,
                    "sharpe_ratio": 0.62,
                    "final_equity": 104200,
                    "annual_return_pct": 5.4,
                    "annual_volatility_pct": 15.3,
                    "turnover_pct": 88.9,
                    "rebalance_count": 38,
                    "skipped_period_count": 1,
                    "equity_curve": _snapshot_curve(
                        100000, [100300, 98300, 100600, 102000, 101100, 103700, 102600, 104200]
                    ),
                    "drawdown_curve": _snapshot_drawdown([0, -2.2, -1.1, 0, -1.4, 0, -1.9, -0.3]),
                },
            ],
            "strategy_comparison": [
                {
                    "run_id": "mb_snapshot_buy_hold",
                    "template_id": "buy_and_hold",
                    "successful_symbols": 6,
                    "failed_symbols": 0,
                    "average_total_return_pct": 9.8,
                    "best_symbol": "PAPA",
                    "worst_symbol": "CHAR",
                    "best_total_return_pct": 15.6,
                    "worst_total_return_pct": 1.9,
                },
                {
                    "run_id": "mb_snapshot_ma",
                    "template_id": "ma_crossover",
                    "successful_symbols": 6,
                    "failed_symbols": 0,
                    "average_total_return_pct": 6.1,
                    "best_symbol": "DELT",
                    "worst_symbol": "JULI",
                    "best_total_return_pct": 12.3,
                    "worst_total_return_pct": -2.4,
                },
                {
                    "run_id": "mb_snapshot_macd",
                    "template_id": "macd_trend_following",
                    "successful_symbols": 6,
                    "failed_symbols": 0,
                    "average_total_return_pct": 7.3,
                    "best_symbol": "KILO",
                    "worst_symbol": "ECHO",
                    "best_total_return_pct": 14.2,
                    "worst_total_return_pct": -1.1,
                },
            ],
            "best_portfolio_run_id": "pf_snapshot_trend",
            "best_multi_backtest_run_id": "mb_snapshot_buy_hold",
            "events": _snapshot_events(),
        }

    def _summary_from_job(self, job_id: str) -> dict | None:
        for event in reversed(self.repository.list_job_events(job_id)):
            summary = event.details.get("summary")
            if isinstance(summary, dict):
                return summary
        return None


def _permissive_rules() -> ScannerRules:
    return ScannerRules(
        enable_close_above_sma_200=False,
        enable_sma_20_above_sma_60=False,
        enable_rsi_range=False,
        enable_volume_ratio_20d=False,
        enable_return_60d=False,
        rsi_min=0,
        rsi_max=100,
        volume_ratio_20d_min=0,
        return_60d_min_pct=-100,
    )


def _quality_symbol_summary(item) -> dict[str, Any]:
    return {
        "symbol": item.symbol,
        "name": item.name,
        "exchange": item.exchange,
        "cached_bar_count": item.cached_bar_count,
        "first_cached_date": item.first_cached_date.isoformat() if item.first_cached_date else None,
        "last_cached_date": item.last_cached_date.isoformat() if item.last_cached_date else None,
        "missing_weekday_count": item.missing_weekday_count,
        "providers": list(item.providers),
        "contains_fixture_data": item.contains_fixture_data,
        "supports_sma_200": item.supports_sma_200,
        "supports_return_252d": item.supports_return_252d,
        "warnings": list(item.warnings),
    }


def _scanner_result_summary(item) -> dict[str, Any]:
    metrics = item.metrics
    score = (metrics.get("return_60d_pct") or 0) - (metrics.get("atr_pct") or 0) * 0.35
    return {
        "rank": item.rank,
        "symbol": item.symbol,
        "name": item.name,
        "score": round(float(score), 4),
        "rsi_14": metrics.get("rsi_14"),
        "atr_pct": metrics.get("atr_pct"),
        "volume_ratio_20d": metrics.get("volume_ratio_20d"),
        "return_20d_pct": metrics.get("return_20d_pct"),
        "return_60d_pct": metrics.get("return_60d_pct"),
        "return_252d_pct": metrics.get("return_252d_pct"),
    }


def _portfolio_summary(item) -> dict[str, Any]:
    return {
        "run_id": item.run_id,
        "preset": item.scanner_preset_id,
        "frequency": item.frequency.value,
        "top_n": item.top_n,
        "total_return_pct": item.performance.get("total_return_pct"),
        "max_drawdown_pct": item.performance.get("max_drawdown_pct"),
        "sharpe_ratio": item.performance.get("sharpe_ratio"),
        "annual_return_pct": item.performance.get("annual_return_pct"),
        "annual_volatility_pct": item.performance.get("annual_volatility_pct"),
        "final_equity": item.aggregate.get("final_equity"),
        "turnover_pct": item.aggregate.get("average_turnover_pct"),
        "rebalance_count": item.aggregate.get("rebalance_count"),
        "skipped_period_count": item.aggregate.get("skipped_period_count"),
        "relative_total_return_pct": item.aggregate.get("relative_total_return_pct"),
        "equity_curve": _sample_equity_curve(item.equity_curve),
        "drawdown_curve": _sample_drawdown_curve(item.equity_curve),
    }


def _strategy_summary(item) -> dict[str, Any]:
    returns = [
        result.metrics.get("total_return_pct")
        for result in item.results
        if isinstance(result.metrics.get("total_return_pct"), int | float)
    ]
    return {
        "run_id": item.run_id,
        "template_id": item.template_id,
        "status": item.status.value,
        "successful_symbols": item.successful_symbols,
        "failed_symbols": item.failed_symbols,
        "average_total_return_pct": item.aggregate.get("average_total_return_pct"),
        "best_symbol": item.aggregate.get("best_symbol"),
        "worst_symbol": item.aggregate.get("worst_symbol"),
        "best_total_return_pct": max(returns) if returns else None,
        "worst_total_return_pct": min(returns) if returns else None,
    }


def _sample_equity_curve(points) -> list[dict[str, Any]]:
    sampled = _sample_sequence(points, limit=28)
    return [
        {"date": point.date.isoformat(), "equity": point.equity, "drawdown_pct": point.drawdown_pct}
        for point in sampled
    ]


def _sample_drawdown_curve(points) -> list[dict[str, Any]]:
    sampled = _sample_sequence(points, limit=28)
    return [
        {"date": point.date.isoformat(), "drawdown_pct": point.drawdown_pct} for point in sampled
    ]


def _sample_sequence(items, *, limit: int):
    sequence = list(items)
    if len(sequence) <= limit:
        return sequence
    step = (len(sequence) - 1) / (limit - 1)
    indexes = sorted({round(index * step) for index in range(limit)})
    return [sequence[index] for index in indexes]


def _workflow_events(
    *,
    started_at: datetime,
    finished_at: datetime,
    universe: dict[str, Any],
    sync: dict[str, Any],
    quality: dict[str, Any],
    scanner: dict[str, Any],
    portfolio_runs: list[dict[str, Any]],
    strategy_runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    base = {
        "status": "success",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
    }
    return [
        {
            **base,
            "id": "load_data",
            "label": "Load Sample Universe",
            "route": "/market-data",
            "message": "Seed deterministic 20-stock research universe.",
            "metrics": {"symbols": universe.get("member_count", 0)},
        },
        {
            **base,
            "id": "sync",
            "label": "Batch Sync",
            "route": "/jobs",
            "message": "Sync cached OHLCV fixture data.",
            "metrics": sync,
        },
        {
            **base,
            "id": "quality",
            "label": "Quality Gates",
            "route": "/data-quality",
            "message": "Check coverage, missing dates, fixture flags, and indicator readiness.",
            "metrics": quality,
        },
        {
            **base,
            "id": "scanner",
            "label": "Scanner Ranking",
            "route": "/parameter-scanner",
            "message": "Rank sample stocks with technical indicators.",
            "metrics": scanner,
        },
        {
            **base,
            "id": "portfolio_matrix",
            "label": "Portfolio Matrix",
            "route": "/portfolio-rebalance",
            "message": "Run equal-weight preset rebalance tests.",
            "metrics": {"runs": len(portfolio_runs)},
        },
        {
            **base,
            "id": "strategy_matrix",
            "label": "Strategy Matrix",
            "route": "/comparison",
            "message": "Compare strategy templates across scanner candidates.",
            "metrics": {"runs": len(strategy_runs)},
        },
        {
            **base,
            "id": "performance",
            "label": "Performance Report",
            "route": "/performance-report",
            "message": "Summarize returns, drawdown, Sharpe, turnover, and failures.",
            "metrics": {
                "best_portfolio": portfolio_runs[0].get("preset") if portfolio_runs else None
            },
        },
        {
            **base,
            "id": "complete",
            "label": "Complete",
            "route": "/",
            "message": "Research workflow is ready for review.",
            "metrics": {"run_status": "success"},
        },
    ]


def _snapshot_quality_symbols() -> list[dict[str, Any]]:
    symbols = [
        "AAPL",
        "ALFA",
        "BRAV",
        "CHAR",
        "DELT",
        "ECHO",
        "FOXT",
        "GOLF",
        "HOTL",
        "KILO",
        "NOVA",
        "PAPA",
    ]
    rows = []
    for index, symbol in enumerate(symbols):
        cached = 736 - (index % 4) * 18
        missing = (index % 5) * 6
        rows.append(
            {
                "symbol": symbol,
                "name": f"{symbol} Synthetic Equity",
                "exchange": "NYSE",
                "cached_bar_count": cached,
                "first_cached_date": "2023-01-03",
                "last_cached_date": "2025-12-31",
                "missing_weekday_count": missing,
                "providers": ["csv"],
                "contains_fixture_data": True,
                "supports_sma_200": True,
                "supports_return_252d": True,
                "warnings": ["contains_fixture_data"] if missing else [],
            }
        )
    rows.extend(
        [
            {
                "symbol": "ROMO",
                "name": "ROMO Synthetic Equity",
                "exchange": "NYSE",
                "cached_bar_count": 162,
                "first_cached_date": "2025-05-19",
                "last_cached_date": "2025-12-31",
                "missing_weekday_count": 620,
                "providers": ["csv"],
                "contains_fixture_data": True,
                "supports_sma_200": False,
                "supports_return_252d": False,
                "warnings": ["insufficient_sma_200", "insufficient_return_252d"],
            },
            {
                "symbol": "SIER",
                "name": "SIER Synthetic Equity",
                "exchange": "NYSE",
                "cached_bar_count": 118,
                "first_cached_date": "2025-07-21",
                "last_cached_date": "2025-12-31",
                "missing_weekday_count": 664,
                "providers": ["csv"],
                "contains_fixture_data": True,
                "supports_sma_200": False,
                "supports_return_252d": False,
                "warnings": ["insufficient_sma_200", "insufficient_return_252d"],
            },
        ]
    )
    return rows


def _snapshot_scanner_results() -> list[dict[str, Any]]:
    rows = [
        ("PAPA", 21.4, 63.2, 3.1, 1.32, 5.1, 18.8),
        ("HOTL", 18.6, 58.7, 2.7, 1.18, 4.4, 15.6),
        ("DELT", 15.8, 61.1, 3.8, 1.06, 3.9, 13.7),
        ("KILO", 14.9, 54.8, 2.4, 0.98, 2.8, 12.9),
        ("NOVA", 12.1, 49.2, 2.1, 1.12, 1.9, 10.6),
        ("ALFA", 10.3, 52.5, 4.2, 0.92, 1.4, 8.4),
    ]
    return [
        {
            "rank": index,
            "symbol": symbol,
            "name": f"{symbol} Synthetic Equity",
            "score": round(return_60d - atr * 0.35, 4),
            "return_60d_pct": return_60d,
            "rsi_14": rsi,
            "atr_pct": atr,
            "volume_ratio_20d": volume_ratio,
            "return_20d_pct": return_20d,
            "return_252d_pct": return_252d,
        }
        for index, (
            symbol,
            return_60d,
            rsi,
            atr,
            volume_ratio,
            return_20d,
            return_252d,
        ) in enumerate(rows, start=1)
    ]


def _snapshot_curve(initial: float, values: list[float]) -> list[dict[str, Any]]:
    dates = [
        "2023-01-31",
        "2023-02-28",
        "2023-03-31",
        "2023-04-28",
        "2023-05-31",
        "2023-06-30",
        "2023-08-31",
        "2023-09-29",
    ]
    return [
        {
            "date": date_value,
            "equity": equity,
            "drawdown_pct": round((equity / max(initial, equity) - 1) * 100, 4),
        }
        for date_value, equity in zip(dates, values, strict=False)
    ]


def _snapshot_drawdown(values: list[float]) -> list[dict[str, Any]]:
    dates = [
        "2023-01-31",
        "2023-02-28",
        "2023-03-31",
        "2023-04-28",
        "2023-05-31",
        "2023-06-30",
        "2023-08-31",
        "2023-09-29",
    ]
    return [
        {"date": date_value, "drawdown_pct": value}
        for date_value, value in zip(dates, values, strict=False)
    ]


def _snapshot_events() -> list[dict[str, Any]]:
    started_at = datetime(2026, 1, 1, 9, 30, tzinfo=UTC)
    finished_at = datetime(2026, 1, 1, 9, 34, tzinfo=UTC)
    return _workflow_events(
        started_at=started_at,
        finished_at=finished_at,
        universe={"member_count": 20},
        sync={"processed": 20, "successful": 20, "failed": 0},
        quality={"coverage_pct": 100.0, "failed_examples": 2},
        scanner={"matched_symbols": 18, "skipped_symbols": 2},
        portfolio_runs=[{"preset": "trend_momentum"}],
        strategy_runs=[{"template_id": "buy_and_hold"}],
    )
