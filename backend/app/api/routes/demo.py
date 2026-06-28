from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import get_demo_research_service
from app.domain.errors import MarketDataError
from app.services.demo_research_service import DemoResearchService

router = APIRouter(prefix="/demo", tags=["research demo"])
DemoResearchServiceDependency = Annotated[DemoResearchService, Depends(get_demo_research_service)]


class DemoResearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: dict[str, Any]


@router.get(
    "/research/latest",
    response_model=DemoResearchResponse,
    summary="Read the latest research demo summary",
)
def latest_research_demo(
    service: DemoResearchServiceDependency,
) -> DemoResearchResponse:
    return DemoResearchResponse(summary=service.latest_summary())


@router.get(
    "/research/{run_id}",
    response_model=DemoResearchResponse,
    summary="Read one research demo summary",
)
def get_research_demo(
    run_id: str,
    service: DemoResearchServiceDependency,
) -> DemoResearchResponse:
    summary = service.get_summary(run_id)
    if summary is None:
        raise MarketDataError(f"Unknown research demo run: {run_id}", details={"run_id": run_id})
    return DemoResearchResponse(summary=summary)
