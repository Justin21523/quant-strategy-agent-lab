from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_data_quality_service
from app.domain.data_quality import SymbolQuality, UniverseQualityReport
from app.schemas.data_quality import SymbolQualityResponse, UniverseQualityReportResponse
from app.services.data_quality_service import DataQualityService

router = APIRouter(prefix="/data-quality", tags=["data quality"])
DataQualityServiceDependency = Annotated[DataQualityService, Depends(get_data_quality_service)]


@router.get(
    "/universes/{universe_id}",
    response_model=UniverseQualityReportResponse,
    summary="Report cached data quality for a universe",
)
def universe_quality_report(
    universe_id: str,
    service: DataQualityServiceDependency,
    start: date,
    end: date,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> UniverseQualityReportResponse:
    return _report_response(service.universe_report(universe_id, start=start, end=end, limit=limit))


def _report_response(report: UniverseQualityReport) -> UniverseQualityReportResponse:
    return UniverseQualityReportResponse(
        universe_id=report.universe_id,
        member_count=report.member_count,
        refreshed_at=report.refreshed_at,
        requested_start=report.requested_start,
        requested_end=report.requested_end,
        covered_symbols=report.covered_symbols,
        coverage_pct=report.coverage_pct,
        fixture_symbols=report.fixture_symbols,
        sma_200_ready_symbols=report.sma_200_ready_symbols,
        return_252d_ready_symbols=report.return_252d_ready_symbols,
        generated_at=report.generated_at,
        symbols=[_symbol_response(item) for item in report.symbols],
    )


def _symbol_response(item: SymbolQuality) -> SymbolQualityResponse:
    return SymbolQualityResponse(
        symbol=item.symbol,
        name=item.name,
        exchange=item.exchange,
        cached_bar_count=item.cached_bar_count,
        first_cached_date=item.first_cached_date,
        last_cached_date=item.last_cached_date,
        missing_weekday_count=item.missing_weekday_count,
        providers=list(item.providers),
        contains_fixture_data=item.contains_fixture_data,
        supports_sma_200=item.supports_sma_200,
        supports_return_252d=item.supports_return_252d,
        warnings=list(item.warnings),
    )
