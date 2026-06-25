"""Schemas for Phase 0 system endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: str
    version: str
    environment: str
    timestamp: datetime


class Capability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    status: Literal["ready", "planned"]


class SystemInfoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: str
    phase_name: str
    description: str
    capabilities: list[Capability]
