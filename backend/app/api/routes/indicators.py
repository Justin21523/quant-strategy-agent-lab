from fastapi import APIRouter

from app.schemas.indicators import IndicatorCatalogItemResponse, IndicatorCatalogResponse
from app.services.indicator_service import IndicatorService

router = APIRouter(prefix="/indicators", tags=["indicator engine"])


@router.get(
    "/catalog", response_model=IndicatorCatalogResponse, summary="List supported indicators"
)
def indicator_catalog() -> IndicatorCatalogResponse:
    service = IndicatorService()
    indicators = [
        IndicatorCatalogItemResponse(
            kind=item.kind,
            label=item.label,
            description=item.description,
            default_parameters=item.default_parameters,
            pane=item.pane,
        )
        for item in service.catalog()
    ]
    return IndicatorCatalogResponse(total=len(indicators), indicators=indicators)
