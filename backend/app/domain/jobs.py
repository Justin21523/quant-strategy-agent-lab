from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobKind(StrEnum):
    MARKET_BATCH_SYNC = "market_batch_sync"
    SCAN_RUN = "scan_run"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"
    RESEARCH_DEMO = "research_demo"
    RESEARCH_PIPELINE = "research_pipeline"


@dataclass(frozen=True, slots=True)
class JobRun:
    job_id: str
    kind: JobKind
    status: JobStatus
    payload: dict[str, Any]
    processed: int
    total: int
    message: str
    result_type: str | None
    result_id: str | None
    error: str | None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class JobEvent:
    event_id: int
    job_id: str
    sequence: int
    status: JobStatus
    message: str
    processed: int
    total: int
    details: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
