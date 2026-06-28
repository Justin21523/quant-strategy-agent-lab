from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, date, datetime
from uuid import uuid4

from app.domain.errors import JobNotFoundError, MarketDataError
from app.domain.jobs import JobKind, JobRun, JobStatus
from app.domain.market import ProviderSelection
from app.domain.portfolio import PortfolioSelectionMode, RebalanceFrequency
from app.domain.quality import DataQualityGate
from app.domain.scanner import ScannerRules, SortDirection
from app.repositories.market_data_repository import MarketDataRepository
from app.services.demo_research_service import DemoResearchService
from app.services.market_data_service import MarketDataService
from app.services.portfolio_service import PortfolioService
from app.services.research_pipeline_service import ResearchPipelineService
from app.services.scanner_service import ScannerService

logger = logging.getLogger(__name__)


class JobCancelledError(Exception):
    pass


class JobService:
    def __init__(
        self,
        *,
        repository: MarketDataRepository,
        market_data_service: MarketDataService,
        scanner_service: ScannerService,
        portfolio_service: PortfolioService,
        demo_research_service: DemoResearchService,
        research_pipeline_service: ResearchPipelineService,
    ) -> None:
        self.repository = repository
        self.market_data_service = market_data_service
        self.scanner_service = scanner_service
        self.portfolio_service = portfolio_service
        self.demo_research_service = demo_research_service
        self.research_pipeline_service = research_pipeline_service
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None

    def start(self) -> None:
        self.repository.fail_interrupted_jobs()
        if self._worker and self._worker.is_alive():
            return
        self._worker = threading.Thread(target=self._run_loop, name="job-worker", daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=2)

    def enqueue(self, kind: JobKind, payload: dict) -> JobRun:
        now = datetime.now(UTC).replace(microsecond=0)
        job = JobRun(
            job_id=f"job_{uuid4().hex[:12]}",
            kind=kind,
            status=JobStatus.PENDING,
            payload=payload,
            processed=0,
            total=0,
            message="Job is pending.",
            result_type=None,
            result_id=None,
            error=None,
            created_at=now,
        )
        self.repository.create_job(job)
        self.repository.add_job_event(
            job.job_id,
            status=JobStatus.PENDING,
            message="Job was queued.",
        )
        return job

    def list_jobs(self, *, limit: int = 50) -> tuple[JobRun, ...]:
        return self.repository.list_jobs(limit=limit)

    def get_job(self, job_id: str) -> JobRun:
        job = self.repository.get_job(job_id)
        if job is None:
            raise JobNotFoundError(f"Unknown job: {job_id}", details={"job_id": job_id})
        return job

    def list_events(self, job_id: str):
        self.get_job(job_id)
        return self.repository.list_job_events(job_id)

    def cancel(self, job_id: str) -> JobRun:
        self.get_job(job_id)
        now = datetime.now(UTC).replace(microsecond=0)
        self.repository.update_job(
            job_id,
            status=JobStatus.CANCELLED,
            message="Job was cancelled.",
            finished_at=now,
        )
        self.repository.add_job_event(
            job_id,
            status=JobStatus.CANCELLED,
            message="Job was cancelled.",
        )
        return self.get_job(job_id)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            job = self.repository.claim_next_job()
            if job is None:
                time.sleep(0.1)
                continue
            try:
                self._execute(job)
            except JobCancelledError:
                self.repository.update_job(
                    job.job_id,
                    status=JobStatus.CANCELLED,
                    message="Job was cancelled.",
                    finished_at=datetime.now(UTC).replace(microsecond=0),
                )
            except Exception as exc:  # pragma: no cover - defensive worker boundary.
                logger.exception("Job failed job_id=%s kind=%s", job.job_id, job.kind)
                self.repository.update_job(
                    job.job_id,
                    status=JobStatus.FAILED,
                    message="Job failed.",
                    error=str(exc),
                    finished_at=datetime.now(UTC).replace(microsecond=0),
                )
                self.repository.add_job_event(
                    job.job_id,
                    status=JobStatus.FAILED,
                    message=str(exc),
                )

    def _execute(self, job: JobRun) -> None:
        self.repository.add_job_event(
            job.job_id,
            status=JobStatus.RUNNING,
            message="Job started.",
        )
        if job.kind is JobKind.MARKET_BATCH_SYNC:
            result = self._run_market_batch_sync(job)
            result_type = "batch_sync"
            result_id = result.run_id
        elif job.kind is JobKind.SCAN_RUN:
            result = self._run_scan(job)
            result_type = "scan"
            result_id = result.run_id
        elif job.kind is JobKind.PORTFOLIO_REBALANCE:
            result = self._run_portfolio(job)
            result_type = "portfolio_rebalance"
            result_id = result.run_id
        elif job.kind is JobKind.RESEARCH_DEMO:
            result = self._run_research_demo(job)
            result_type = "research_demo"
            result_id = result.run_id
        elif job.kind is JobKind.RESEARCH_PIPELINE:
            result = self._run_research_pipeline(job)
            result_type = "research_pipeline"
            result_id = result.run_id
        else:  # pragma: no cover
            raise MarketDataError(f"Unsupported job kind: {job.kind}")
        latest = self.get_job(job.job_id)
        processed = max(latest.processed, 1)
        total = max(latest.total, processed, 1)
        self.repository.add_job_event(
            job.job_id,
            status=JobStatus.SUCCESS,
            message="Job completed.",
            processed=processed,
            total=total,
            details={
                "result_type": result_type,
                "result_id": result_id,
                **(
                    {"summary": result.summary}
                    if result_type in {"research_demo", "research_pipeline"}
                    and hasattr(result, "summary")
                    else {}
                ),
            },
        )
        self.repository.update_job(
            job.job_id,
            status=JobStatus.SUCCESS,
            processed=processed,
            total=total,
            message="Job completed.",
            result_type=result_type,
            result_id=result_id,
            finished_at=datetime.now(UTC).replace(microsecond=0),
        )

    def _progress(self, job_id: str, processed: int, total: int, message: str) -> None:
        job = self.get_job(job_id)
        if job.status is JobStatus.CANCELLED:
            raise JobCancelledError
        self.repository.update_job(
            job_id,
            processed=processed,
            total=total,
            message=message,
        )
        self.repository.add_job_event(
            job_id,
            status=JobStatus.RUNNING,
            message=message,
            processed=processed,
            total=total,
        )

    def _run_market_batch_sync(self, job: JobRun):
        payload = job.payload
        self._progress(job.job_id, 0, 1, "Running market batch sync.")
        return self.market_data_service.batch_sync_universe(
            str(payload["universe_id"]),
            start=_date(payload["start"]),
            end=_date(payload["end"]),
            provider=ProviderSelection(str(payload.get("provider", "yfinance"))),
            chunk_size=int(payload.get("chunk_size", 50)),
            cursor=int(payload.get("cursor", 0)),
            allow_fallback=bool(payload.get("allow_fallback", False)),
            mode=str(payload.get("mode", "all")),
            stale_after=_optional_date(payload.get("stale_after")),
            failed_run_id=payload.get("failed_run_id"),
        )

    def _run_scan(self, job: JobRun):
        payload = job.payload
        self._progress(job.job_id, 0, 1, "Running stock scanner.")
        gate = _quality_gate(payload.get("quality_gate"))
        return self.scanner_service.run_scan(
            universe_id=str(payload.get("universe_id", "us_common_stocks")),
            start=_date(payload["start"]),
            end=_date(payload["end"]),
            rules=ScannerRules(**payload.get("rules", {})),
            sort_key=str(payload.get("sort_key", "return_60d_pct")),
            sort_direction=SortDirection(str(payload.get("sort_direction", "desc"))),
            result_limit=int(payload.get("result_limit", 100)),
            quality_gate=gate,
        )

    def _run_portfolio(self, job: JobRun):
        payload = job.payload
        return self.portfolio_service.run_rebalance(
            selection_mode=PortfolioSelectionMode(
                str(payload.get("selection_mode", "rescan_each_period"))
            ),
            universe_id=str(payload.get("universe_id", "us_common_stocks")),
            start=_date(payload["start"]),
            end=_date(payload["end"]),
            frequency=RebalanceFrequency(str(payload.get("frequency", "monthly"))),
            top_n=int(payload.get("top_n", 20)),
            initial_cash=float(payload.get("initial_cash", 100_000)),
            commission=float(payload.get("commission", 0.001)),
            slippage=float(payload.get("slippage", 0.0005)),
            lookback_days=int(payload.get("lookback_days", 365)),
            scanner_preset_id=payload.get("scanner_preset_id"),
            scanner_rules=ScannerRules(**payload["scanner_rules"])
            if payload.get("scanner_rules")
            else None,
            fixed_scan_run_id=payload.get("fixed_scan_run_id"),
            benchmark_symbol=str(payload.get("benchmark_symbol", "SPY")).upper(),
            quality_gate=_quality_gate(payload.get("quality_gate")),
            progress=lambda processed, total, message: self._progress(
                job.job_id, processed, total, message
            ),
        )

    def _run_research_demo(self, job: JobRun):
        return self.demo_research_service.run(
            progress=lambda processed, total, message: self._progress(
                job.job_id, processed, total, message
            )
        )

    def _run_research_pipeline(self, job: JobRun):
        return self.research_pipeline_service.run(
            job.payload,
            progress=lambda processed, total, message: self._progress(
                job.job_id, processed, total, message
            ),
        )


def _date(value: object) -> date:
    return date.fromisoformat(str(value))


def _optional_date(value: object | None) -> date | None:
    return date.fromisoformat(str(value)) if value else None


def _quality_gate(payload: object | None) -> DataQualityGate | None:
    if not isinstance(payload, dict):
        return None
    return DataQualityGate(
        min_bars=int(payload.get("min_bars", 0)),
        allow_fixture_data=bool(payload.get("allow_fixture_data", True)),
        min_last_cached_date=_optional_date(payload.get("min_last_cached_date")),
        max_missing_weekdays=int(payload["max_missing_weekdays"])
        if payload.get("max_missing_weekdays") is not None
        else None,
    )
