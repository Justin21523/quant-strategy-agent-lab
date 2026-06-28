from fastapi import APIRouter

from app.api.routes import (
    agent,
    backtests,
    data_quality,
    demo,
    health,
    indicators,
    jobs,
    market,
    multi_backtests,
    portfolios,
    research,
    scans,
    strategies,
    system,
    universes,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(market.router)
api_router.include_router(indicators.router)
api_router.include_router(universes.router)
api_router.include_router(strategies.router)
api_router.include_router(backtests.router)
api_router.include_router(agent.router)
api_router.include_router(scans.router)
api_router.include_router(data_quality.router)
api_router.include_router(multi_backtests.router)
api_router.include_router(portfolios.router)
api_router.include_router(demo.router)
api_router.include_router(research.router)
api_router.include_router(jobs.router)
