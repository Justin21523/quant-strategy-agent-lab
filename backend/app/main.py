import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.errors import market_data_error_handler
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.container import AppContainer
from app.core.logging import configure_logging
from app.domain.errors import MarketDataError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    logger.info("Starting %s version=%s", settings.project_name, __version__)
    app.state.container.initialize()
    yield
    logger.info("Stopping %s", settings.project_name)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)
    application = FastAPI(
        title=resolved.project_name,
        summary="Quantitative strategy research and backtesting API.",
        description=(
            "Educational and research API for normalized market data, strategy DSL validation, "
            "backtesting, performance analysis, and Agent workflow experiments."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{resolved.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )
    application.state.settings = resolved
    application.state.container = AppContainer.build(resolved)
    application.add_exception_handler(MarketDataError, market_data_error_handler)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.backend_cors_origins,
        allow_origin_regex=resolved.backend_cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=resolved.api_v1_prefix)

    @application.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "name": resolved.project_name,
            "version": __version__,
            "environment": resolved.environment,
            "phase": "phase-5",
            "docs": "/docs",
            "health": f"{resolved.api_v1_prefix}/health",
            "market": f"{resolved.api_v1_prefix}/market/symbols",
            "indicators": f"{resolved.api_v1_prefix}/indicators/catalog",
            "strategies": f"{resolved.api_v1_prefix}/strategies/templates",
            "backtests": f"{resolved.api_v1_prefix}/backtests/run",
            "disclaimer": "Educational and research use only; not investment advice.",
        }

    return application


app = create_app()
