"""System metadata endpoint used by the Phase 0 frontend."""

from fastapi import APIRouter

from app.schemas.system import Capability, SystemInfoResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse, summary="Read project phase metadata")
async def system_info() -> SystemInfoResponse:
    return SystemInfoResponse(
        phase="0",
        phase_name="Foundation",
        description=(
            "Runnable frontend and backend skeleton with module boundaries, documentation, "
            "quality checks, and no fake quantitative results."
        ),
        capabilities=[
            Capability(key="frontend_shell", label="Modular frontend shell", status="ready"),
            Capability(key="backend_api", label="FastAPI application", status="ready"),
            Capability(key="openapi", label="OpenAPI documentation", status="ready"),
            Capability(key="market_data", label="Market data layer", status="planned"),
            Capability(key="backtesting", label="Backtest engine", status="planned"),
            Capability(key="agent", label="Agent workflow", status="planned"),
        ],
    )
