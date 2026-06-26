from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app import __version__
from app.api.dependencies import get_app_settings, get_market_data_service
from app.core.config import Settings
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.market_data_service import MarketDataService

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Service liveness")
def health_check(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.project_name,
        version=__version__,
        environment=settings.environment,
        phase="phase-1",
        timestamp=datetime.now(UTC),
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Service readiness")
def readiness_check(
    service: Annotated[MarketDataService, Depends(get_market_data_service)],
) -> ReadinessResponse:
    database_ready = service.is_ready()
    return ReadinessResponse(
        status="ready" if database_ready else "not_ready",
        checks={"api": "ok", "database": "ok" if database_ready else "failed"},
    )
