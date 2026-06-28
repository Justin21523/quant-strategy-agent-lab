from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_portfolio_service
from app.domain.errors import PortfolioPresetNotFoundError, PortfolioRunNotFoundError
from app.domain.portfolio import (
    PortfolioPreset,
    PortfolioRun,
)
from app.schemas.portfolios import (
    PortfolioEquityPointResponse,
    PortfolioHoldingResponse,
    PortfolioPresetListResponse,
    PortfolioPresetRequest,
    PortfolioPresetResponse,
    PortfolioRunListResponse,
    PortfolioRunResponse,
    RebalanceEventResponse,
    SkippedPeriodResponse,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolios", tags=["portfolio"])
PortfolioServiceDependency = Annotated[PortfolioService, Depends(get_portfolio_service)]


@router.get(
    "/rebalance",
    response_model=PortfolioRunListResponse,
    summary="List portfolio rebalance runs",
)
def list_rebalance_runs(
    service: PortfolioServiceDependency,
    limit: int = 20,
) -> PortfolioRunListResponse:
    runs = service.list_runs(limit=limit)
    return PortfolioRunListResponse(total=len(runs), runs=[_run_response(run) for run in runs])


@router.get(
    "/rebalance/{run_id}",
    response_model=PortfolioRunResponse,
    summary="Read one portfolio rebalance run",
)
def get_rebalance_run(
    run_id: str,
    service: PortfolioServiceDependency,
) -> PortfolioRunResponse:
    run = service.get_run(run_id)
    if run is None:
        raise PortfolioRunNotFoundError(
            f"Unknown portfolio run: {run_id}",
            details={"run_id": run_id},
        )
    return _run_response(run)


@router.get(
    "/presets",
    response_model=PortfolioPresetListResponse,
    summary="List portfolio presets",
)
def list_presets(service: PortfolioServiceDependency) -> PortfolioPresetListResponse:
    presets = service.list_presets()
    return PortfolioPresetListResponse(
        total=len(presets),
        presets=[_preset_response(item) for item in presets],
    )


@router.post(
    "/presets",
    response_model=PortfolioPresetResponse,
    summary="Save one portfolio preset",
)
def save_preset(
    request: PortfolioPresetRequest,
    service: PortfolioServiceDependency,
) -> PortfolioPresetResponse:
    preset = PortfolioPreset(
        preset_id=request.preset_id,
        name=request.name,
        description=request.description,
        config=request.config,
        created_at=datetime.now(UTC).replace(microsecond=0),
    )
    service.save_preset(preset)
    return _preset_response(preset)


@router.get(
    "/presets/{preset_id}",
    response_model=PortfolioPresetResponse,
    summary="Read one portfolio preset",
)
def get_preset(
    preset_id: str,
    service: PortfolioServiceDependency,
) -> PortfolioPresetResponse:
    preset = service.get_preset(preset_id)
    if preset is None:
        raise PortfolioPresetNotFoundError(
            f"Unknown portfolio preset: {preset_id}",
            details={"preset_id": preset_id},
        )
    return _preset_response(preset)


def _run_response(run: PortfolioRun) -> PortfolioRunResponse:
    return PortfolioRunResponse(
        run_id=run.run_id,
        status=run.status,
        selection_mode=run.selection_mode,
        universe_id=run.universe_id,
        scanner_preset_id=run.scanner_preset_id,
        fixed_scan_run_id=run.fixed_scan_run_id,
        top_n=run.top_n,
        frequency=run.frequency,
        start=run.start_date,
        end=run.end_date,
        lookback_days=run.lookback_days,
        initial_cash=run.initial_cash,
        commission=run.commission,
        slippage=run.slippage,
        benchmark_symbol=run.benchmark_symbol,
        scanner_rules=run.scanner_rules,
        quality_gate=run.quality_gate,
        performance=run.performance,
        benchmark=run.benchmark,
        aggregate=run.aggregate,
        warnings=list(run.warnings),
        created_at=run.created_at,
        equity_curve=[
            PortfolioEquityPointResponse(
                date=point.date,
                equity=point.equity,
                cash=point.cash,
                position_value=point.position_value,
                drawdown_pct=point.drawdown_pct,
            )
            for point in run.equity_curve
        ],
        holdings=[
            PortfolioHoldingResponse(
                date=item.date,
                symbol=item.symbol,
                weight=item.weight,
                shares=item.shares,
                price=item.price,
                value=item.value,
            )
            for item in run.holdings
        ],
        rebalance_events=[
            RebalanceEventResponse(
                date=item.date,
                selected_symbols=list(item.selected_symbols),
                excluded_symbols=list(item.excluded_symbols),
                turnover_pct=item.turnover_pct,
                traded_notional=item.traded_notional,
                cost=item.cost,
                scan_run_id=item.scan_run_id,
            )
            for item in run.rebalance_events
        ],
        skipped_periods=[
            SkippedPeriodResponse(
                date=item.date,
                reason=item.reason,
                details=item.details,
            )
            for item in run.skipped_periods
        ],
    )


def _preset_response(preset: PortfolioPreset) -> PortfolioPresetResponse:
    return PortfolioPresetResponse(
        preset_id=preset.preset_id,
        name=preset.name,
        description=preset.description,
        config=preset.config,
        created_at=preset.created_at,
    )
