from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.core.container import AppContainer
from app.services.market_data_service import MarketDataService


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_market_data_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> MarketDataService:
    return container.market_data_service


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings
