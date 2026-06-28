from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

from app.domain.jobs import JobKind
from app.domain.market import ProviderSelection
from app.domain.portfolio import PortfolioSelectionMode, RebalanceFrequency
from app.domain.quality import DataQualityGate
from app.domain.research import ResearchPreset
from app.domain.scanner import ScannerRules, SortDirection
from app.repositories.market_data_repository import MarketDataRepository
from app.services.data_quality_service import DataQualityService
from app.services.demo_research_service import (
    DEMO_UNIVERSE_ID,
    DemoResearchRun,
    DemoResearchService,
    _portfolio_summary,
    _quality_symbol_summary,
    _scanner_result_summary,
    _strategy_summary,
)
from app.services.market_data_service import MarketDataService
from app.services.multi_backtest_service import MultiBacktestService
from app.services.portfolio_service import PortfolioService
from app.services.research_report_service import ResearchReportService
from app.services.scanner_service import SCANNER_PRESETS, ScannerService

ProgressCallback = Callable[[int, int, str], None]

DEFAULT_RESEARCH_PRESETS: tuple[ResearchPreset, ...] = (
    ResearchPreset(
        preset_id="demo_quick_research",
        name="Demo Quick Research",
        description="Fixture-backed end-to-end research workflow for the sample universe.",
        config={
            "run_label": "Demo Quick Research",
            "universe_id": "demo_research_sample",
            "start": "2023-01-03",
            "end": "2025-12-31",
            "provider": "csv",
            "sync_mode": "all",
            "sync_chunk_size": 25,
            "allow_fallback": False,
            "benchmark_symbol": "SPY",
            "initial_cash": 100000,
            "commission": 0.001,
            "slippage": 0.0005,
            "quality_gate": {
                "min_bars": 120,
                "allow_fixture_data": True,
                "max_missing_weekdays": 1000,
            },
            "scanner_config": {
                "preset_id": "trend_momentum",
                "sort_key": "return_60d_pct",
                "sort_direction": "desc",
                "result_limit": 12,
                "rules": {
                    "enable_close_above_sma_200": False,
                    "enable_sma_20_above_sma_60": False,
                    "enable_rsi_range": False,
                    "enable_volume_ratio_20d": False,
                    "enable_return_20d": False,
                    "enable_return_60d": False,
                    "enable_return_252d": False,
                    "enable_atr_pct_max": False,
                    "close_above_sma_200": True,
                    "sma_20_above_sma_60": True,
                    "rsi_min": 0,
                    "rsi_max": 100,
                    "volume_ratio_20d_min": 0,
                    "return_20d_min_pct": 0,
                    "return_60d_min_pct": -100,
                    "return_252d_min_pct": 0,
                    "atr_pct_max": 12,
                },
            },
            "portfolio_matrix_configs": [
                {
                    "label": "Trend Momentum Monthly Top 8",
                    "scanner_preset_id": "trend_momentum",
                    "frequency": "monthly",
                    "top_n": 8,
                    "lookback_days": 365,
                    "start": "2023-01-03",
                    "end": "2023-09-29",
                },
                {
                    "label": "Low Volatility Monthly Top 10",
                    "scanner_preset_id": "low_volatility_trend",
                    "frequency": "monthly",
                    "top_n": 10,
                    "lookback_days": 365,
                    "start": "2023-01-03",
                    "end": "2023-09-29",
                },
                {
                    "label": "Oversold Weekly Top 5",
                    "scanner_preset_id": "oversold_watchlist",
                    "frequency": "weekly",
                    "top_n": 5,
                    "lookback_days": 365,
                    "start": "2023-01-03",
                    "end": "2023-09-29",
                },
            ],
            "strategy_matrix_configs": [
                {
                    "template_id": "buy_and_hold",
                    "top_n": 6,
                    "start": "2023-01-03",
                    "end": "2023-09-29",
                },
                {
                    "template_id": "ma_crossover",
                    "top_n": 6,
                    "start": "2023-01-03",
                    "end": "2023-09-29",
                },
                {
                    "template_id": "macd_trend_following",
                    "top_n": 6,
                    "start": "2023-01-03",
                    "end": "2023-09-29",
                },
            ],
        },
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    ),
)


class ResearchPipelineService:
    def __init__(
        self,
        *,
        repository: MarketDataRepository,
        market_data_service: MarketDataService,
        scanner_service: ScannerService,
        data_quality_service: DataQualityService,
        portfolio_service: PortfolioService,
        multi_backtest_service: MultiBacktestService,
        demo_research_service: DemoResearchService,
        report_service: ResearchReportService | None = None,
    ) -> None:
        self.repository = repository
        self.market_data_service = market_data_service
        self.scanner_service = scanner_service
        self.data_quality_service = data_quality_service
        self.portfolio_service = portfolio_service
        self.multi_backtest_service = multi_backtest_service
        self.demo_research_service = demo_research_service
        self.report_service = report_service or ResearchReportService()

    def initialize_presets(self) -> None:
        for preset in DEFAULT_RESEARCH_PRESETS:
            if self.repository.get_research_preset(preset.preset_id) is None:
                self.repository.upsert_research_preset(preset)

    def list_presets(self) -> tuple[ResearchPreset, ...]:
        return self.repository.list_research_presets()

    def get_preset(self, preset_id: str) -> ResearchPreset | None:
        return self.repository.get_research_preset(preset_id)

    def save_preset(self, preset: ResearchPreset) -> None:
        self.repository.upsert_research_preset(preset)

    def render_markdown_report(self, run_id: str) -> str | None:
        summary = self.get_summary(run_id)
        return self.report_service.markdown(summary) if summary else None

    def export_artifact(
        self,
        run_id: str,
        *,
        artifact: str,
        format_: str,
    ) -> str | None:
        summary = self.get_summary(run_id)
        if summary is None:
            return None
        if format_ == "json":
            return self.report_service.json_artifact(summary, artifact)
        if format_ == "csv":
            return self.report_service.csv_artifact(summary, artifact)
        raise ValueError(f"Unsupported research export format: {format_}")

    def run(
        self,
        payload: dict[str, Any],
        *,
        progress: ProgressCallback | None = None,
    ) -> DemoResearchRun:
        started_at = datetime.now(UTC).replace(microsecond=0)
        universe_id = str(payload.get("universe_id", DEMO_UNIVERSE_ID))
        start = _date(payload.get("start"), date(2023, 1, 3))
        end = _date(payload.get("end"), date(2025, 12, 31))
        portfolio_configs = list(payload.get("portfolio_matrix_configs") or [])
        strategy_configs = list(payload.get("strategy_matrix_configs") or [])
        total = 4 + len(portfolio_configs) + len(strategy_configs)

        def tick(processed: int, message: str) -> None:
            if progress:
                progress(processed, total, message)

        tick(1, "Preparing research universe.")
        if universe_id == DEMO_UNIVERSE_ID:
            universe = self.demo_research_service.seed_sample_universe()
        else:
            stored = self.repository.get_universe(universe_id)
            universe = {
                "universe_id": universe_id,
                "member_count": len(stored.members) if stored else 0,
                "symbols": [member.symbol for member in stored.members[:20]] if stored else [],
            }

        tick(2, "Syncing research universe market data.")
        sync = self.market_data_service.batch_sync_universe(
            universe_id,
            start=start,
            end=end,
            provider=ProviderSelection(str(payload.get("provider", "csv"))),
            chunk_size=int(payload.get("sync_chunk_size", 25)),
            cursor=0,
            allow_fallback=bool(payload.get("allow_fallback", False)),
            mode=str(payload.get("sync_mode", "all")),
            stale_after=_optional_date(payload.get("stale_after")),
        )

        tick(3, "Generating research data-quality report.")
        quality = self.data_quality_service.universe_report(
            universe_id,
            start=start,
            end=end,
            limit=500,
        )
        quality_gate = _quality_gate(payload.get("quality_gate"))
        scanner_config = dict(payload.get("scanner_config") or {})
        scanner_rules = _scanner_rules(scanner_config)

        tick(4, "Running research scanner.")
        scan = self.scanner_service.run_scan(
            universe_id=universe_id,
            start=start,
            end=end,
            rules=scanner_rules,
            sort_key=str(scanner_config.get("sort_key", "return_60d_pct")),
            sort_direction=SortDirection(str(scanner_config.get("sort_direction", "desc"))),
            result_limit=int(scanner_config.get("result_limit", 20)),
            quality_gate=quality_gate,
        )

        portfolio_runs = []
        for index, config in enumerate(portfolio_configs, start=1):
            tick(4 + index, f"Running portfolio matrix: {config.get('label') or index}.")
            portfolio_runs.append(
                self.portfolio_service.run_rebalance(
                    selection_mode=PortfolioSelectionMode.FIXED_SCAN_RUN,
                    universe_id=universe_id,
                    start=_date(config.get("start"), start),
                    end=_date(config.get("end"), end),
                    frequency=RebalanceFrequency(str(config.get("frequency", "monthly"))),
                    top_n=int(config.get("top_n", 8)),
                    initial_cash=float(payload.get("initial_cash", 100_000)),
                    commission=float(payload.get("commission", 0.001)),
                    slippage=float(payload.get("slippage", 0.0005)),
                    lookback_days=int(config.get("lookback_days", 365)),
                    scanner_preset_id=config.get("scanner_preset_id"),
                    fixed_scan_run_id=scan.run_id,
                    benchmark_symbol=str(payload.get("benchmark_symbol", "SPY")).upper(),
                    quality_gate=quality_gate,
                )
            )

        strategy_offset = 4 + len(portfolio_configs)
        multi_runs = []
        for index, config in enumerate(strategy_configs, start=1):
            tick(strategy_offset + index, f"Running strategy matrix: {config.get('template_id')}.")
            multi_runs.append(
                self.multi_backtest_service.run(
                    scan_run_id=scan.run_id,
                    template_id=str(config.get("template_id", "buy_and_hold")),
                    parameters=dict(config.get("parameters") or {}),
                    top_n=int(config.get("top_n", 6)),
                    start=_date(config.get("start"), start),
                    end=_date(config.get("end"), end),
                    initial_cash=float(payload.get("initial_cash", 100_000)),
                    commission=float(payload.get("commission", 0.001)),
                    slippage=float(payload.get("slippage", 0.0005)),
                )
            )

        tick(total, "Finalizing research pipeline summary.")
        finished_at = datetime.now(UTC).replace(microsecond=0)
        run_id = f"rp_{started_at.strftime('%Y%m%d%H%M%S')}"
        failed_quality = [
            _quality_symbol_summary(item)
            for item in quality.symbols
            if item.warnings or item.missing_weekday_count > 0
        ][:8]
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
            "run_label": str(payload.get("run_label", "Research Pipeline")),
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
                "failed_examples": failed_quality,
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
            "config": payload,
            "events": _pipeline_events(
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

    def latest_summary(self) -> dict[str, Any] | None:
        summaries = self.list_summaries(limit=1)
        return summaries[0] if summaries else None

    def get_summary(self, run_id: str) -> dict[str, Any] | None:
        for summary in self.list_summaries(limit=200):
            if summary.get("run_id") == run_id:
                return summary
        return None

    def list_summaries(self, *, limit: int = 20) -> list[dict[str, Any]]:
        summaries = []
        for job in self.repository.list_jobs(limit=200):
            if job.kind is not JobKind.RESEARCH_PIPELINE:
                continue
            summary = self._summary_from_job(job.job_id)
            if summary:
                summaries.append(summary)
            if len(summaries) >= limit:
                break
        return summaries

    def _summary_from_job(self, job_id: str) -> dict[str, Any] | None:
        for event in reversed(self.repository.list_job_events(job_id)):
            summary = event.details.get("summary")
            if isinstance(summary, dict) and summary.get("run_id"):
                return summary
        return None


def _scanner_rules(config: dict[str, Any]) -> ScannerRules:
    if config.get("rules"):
        return ScannerRules(**dict(config["rules"]))
    preset_id = str(config.get("preset_id", "trend_momentum"))
    return SCANNER_PRESETS.get(preset_id, ScannerRules())


def _quality_gate(payload: object | None) -> DataQualityGate:
    data = dict(payload or {})
    return DataQualityGate(
        min_bars=int(data.get("min_bars", 200)),
        allow_fixture_data=bool(data.get("allow_fixture_data", True)),
        min_last_cached_date=_optional_date(data.get("min_last_cached_date")),
        max_missing_weekdays=data.get("max_missing_weekdays", 1000),
    )


def _date(value: object | None, default: date) -> date:
    return date.fromisoformat(str(value)) if value else default


def _optional_date(value: object | None) -> date | None:
    return date.fromisoformat(str(value)) if value else None


def _pipeline_events(
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
            "id": "universe",
            "label": "Universe",
            "route": "/research-lab",
            "message": "Prepare selected research universe.",
            "metrics": {"symbols": universe.get("member_count", 0)},
        },
        {
            **base,
            "id": "sync",
            "label": "Batch Sync",
            "route": "/jobs",
            "message": "Sync or refresh cached OHLCV data.",
            "metrics": sync,
        },
        {
            **base,
            "id": "quality",
            "label": "Quality Gates",
            "route": "/data-quality",
            "message": "Measure coverage and indicator readiness.",
            "metrics": quality,
        },
        {
            **base,
            "id": "scanner",
            "label": "Scanner",
            "route": "/parameter-scanner",
            "message": "Rank symbols with the configured scanner.",
            "metrics": scanner,
        },
        {
            **base,
            "id": "portfolio_matrix",
            "label": "Portfolio Matrix",
            "route": "/portfolio-rebalance",
            "message": "Compare rebalance presets.",
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
            "id": "report",
            "label": "Report",
            "route": "/research-lab",
            "message": "Save chart-ready research summary.",
            "metrics": {
                "best_portfolio": portfolio_runs[0].get("preset") if portfolio_runs else None
            },
        },
    ]
