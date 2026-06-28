from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_universe_service
from app.domain.universe import UniverseDetail, UniverseMember, UniverseSummary
from app.schemas.universes import (
    UniverseDetailResponse,
    UniverseListResponse,
    UniverseMemberResponse,
    UniverseRefreshResponse,
    UniverseSummaryResponse,
)
from app.services.universe_service import UniverseService

router = APIRouter(prefix="/universes", tags=["market universes"])
UniverseServiceDependency = Annotated[UniverseService, Depends(get_universe_service)]


@router.get("", response_model=UniverseListResponse, summary="List market universes")
def list_universes(service: UniverseServiceDependency) -> UniverseListResponse:
    universes = [_summary_response(item) for item in service.list_universes()]
    return UniverseListResponse(total=len(universes), universes=universes)


@router.get(
    "/{universe_id}",
    response_model=UniverseDetailResponse,
    summary="Read one market universe",
)
def get_universe(universe_id: str, service: UniverseServiceDependency) -> UniverseDetailResponse:
    return _detail_response(service.get_universe(universe_id))


@router.post(
    "/us-common-stocks/refresh",
    response_model=UniverseRefreshResponse,
    summary="Refresh US common-stock universe from Nasdaq Trader",
)
def refresh_us_common_stocks(service: UniverseServiceDependency) -> UniverseRefreshResponse:
    result = service.refresh_us_common_stocks()
    return UniverseRefreshResponse(
        universe=_summary_response(result.summary),
        inserted_symbols=result.inserted_symbols,
        member_count=len(result.members),
    )


def _detail_response(detail: UniverseDetail) -> UniverseDetailResponse:
    return UniverseDetailResponse(
        universe=_summary_response(detail.summary),
        members=[_member_response(member) for member in detail.members],
    )


def _summary_response(summary: UniverseSummary) -> UniverseSummaryResponse:
    return UniverseSummaryResponse(
        universe_id=summary.universe_id,
        name=summary.name,
        description=summary.description,
        market=summary.market,
        asset_type=summary.asset_type,
        source=summary.source,
        source_url=summary.source_url,
        member_count=summary.member_count,
        refreshed_at=summary.refreshed_at,
    )


def _member_response(member: UniverseMember) -> UniverseMemberResponse:
    return UniverseMemberResponse(
        symbol=member.symbol,
        name=member.name,
        exchange=member.exchange,
        asset_type=member.asset_type,
        currency=member.currency,
        provider_symbol=member.provider_symbol,
        is_active=member.is_active,
    )
