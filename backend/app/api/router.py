from fastapi import APIRouter

from app.api.routes import health, indicators, market, strategies, system

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(market.router)
api_router.include_router(indicators.router)
api_router.include_router(strategies.router)
