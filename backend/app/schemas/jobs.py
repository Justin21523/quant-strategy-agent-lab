from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.jobs import JobKind, JobStatus
from app.schemas.market import BatchSyncRequest
from app.schemas.portfolios import PortfolioRebalanceRequest
from app.schemas.research import ResearchPipelineRunRequest
from app.schemas.scans import ScanRunRequest


class JobRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    kind: JobKind
    status: JobStatus
    payload: dict[str, Any]
    processed: int = Field(ge=0)
    total: int = Field(ge=0)
    message: str
    result_type: str | None
    result_id: str | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class JobRunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    jobs: list[JobRunResponse]


class JobEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: int
    job_id: str
    sequence: int
    status: JobStatus
    message: str
    processed: int = Field(ge=0)
    total: int = Field(ge=0)
    details: dict[str, Any]
    created_at: datetime | None


class JobEventListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    events: list[JobEventResponse]


class BatchSyncJobRequest(BatchSyncRequest):
    pass


class ScanRunJobRequest(ScanRunRequest):
    pass


class PortfolioRebalanceJobRequest(PortfolioRebalanceRequest):
    pass


class ResearchPipelineJobRequest(ResearchPipelineRunRequest):
    pass
