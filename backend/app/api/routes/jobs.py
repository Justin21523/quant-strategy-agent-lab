from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_job_service
from app.domain.jobs import JobEvent, JobKind, JobRun
from app.schemas.jobs import (
    BatchSyncJobRequest,
    JobEventListResponse,
    JobEventResponse,
    JobRunListResponse,
    JobRunResponse,
    PortfolioRebalanceJobRequest,
    ResearchPipelineJobRequest,
    ScanRunJobRequest,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])
JobServiceDependency = Annotated[JobService, Depends(get_job_service)]


@router.post(
    "/market/batch-sync",
    response_model=JobRunResponse,
    summary="Queue a market batch sync job",
)
def queue_market_batch_sync(
    request: BatchSyncJobRequest,
    service: JobServiceDependency,
) -> JobRunResponse:
    return _job_response(
        service.enqueue(JobKind.MARKET_BATCH_SYNC, request.model_dump(mode="json"))
    )


@router.post(
    "/scans/run",
    response_model=JobRunResponse,
    summary="Queue a scanner job",
)
def queue_scan(
    request: ScanRunJobRequest,
    service: JobServiceDependency,
) -> JobRunResponse:
    return _job_response(service.enqueue(JobKind.SCAN_RUN, request.model_dump(mode="json")))


@router.post(
    "/portfolios/rebalance/run",
    response_model=JobRunResponse,
    summary="Queue a portfolio rebalance job",
)
def queue_portfolio_rebalance(
    request: PortfolioRebalanceJobRequest,
    service: JobServiceDependency,
) -> JobRunResponse:
    return _job_response(
        service.enqueue(JobKind.PORTFOLIO_REBALANCE, request.model_dump(mode="json"))
    )


@router.post(
    "/demo/research/run",
    response_model=JobRunResponse,
    summary="Queue the in-app research demo workflow",
)
def queue_research_demo(service: JobServiceDependency) -> JobRunResponse:
    return _job_response(service.enqueue(JobKind.RESEARCH_DEMO, {}))


@router.post(
    "/research/pipeline/run",
    response_model=JobRunResponse,
    summary="Queue a configurable research pipeline job",
)
def queue_research_pipeline(
    request: ResearchPipelineJobRequest,
    service: JobServiceDependency,
) -> JobRunResponse:
    return _job_response(
        service.enqueue(JobKind.RESEARCH_PIPELINE, request.model_dump(mode="json"))
    )


@router.get("", response_model=JobRunListResponse, summary="List jobs")
def list_jobs(service: JobServiceDependency, limit: int = 50) -> JobRunListResponse:
    jobs = service.list_jobs(limit=limit)
    return JobRunListResponse(total=len(jobs), jobs=[_job_response(job) for job in jobs])


@router.get("/{job_id}", response_model=JobRunResponse, summary="Read one job")
def get_job(job_id: str, service: JobServiceDependency) -> JobRunResponse:
    return _job_response(service.get_job(job_id))


@router.get(
    "/{job_id}/events",
    response_model=JobEventListResponse,
    summary="Read one job event stream",
)
def get_job_events(job_id: str, service: JobServiceDependency) -> JobEventListResponse:
    events = service.list_events(job_id)
    return JobEventListResponse(
        total=len(events),
        events=[_event_response(event) for event in events],
    )


@router.post("/{job_id}/cancel", response_model=JobRunResponse, summary="Cancel one job")
def cancel_job(job_id: str, service: JobServiceDependency) -> JobRunResponse:
    return _job_response(service.cancel(job_id))


def _job_response(job: JobRun) -> JobRunResponse:
    return JobRunResponse(
        job_id=job.job_id,
        kind=job.kind,
        status=job.status,
        payload=job.payload,
        processed=job.processed,
        total=job.total,
        message=job.message,
        result_type=job.result_type,
        result_id=job.result_id,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _event_response(event: JobEvent) -> JobEventResponse:
    return JobEventResponse(
        event_id=event.event_id,
        job_id=event.job_id,
        sequence=event.sequence,
        status=event.status,
        message=event.message,
        processed=event.processed,
        total=event.total,
        details=event.details,
        created_at=event.created_at,
    )
