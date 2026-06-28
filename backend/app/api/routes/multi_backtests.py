from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_multi_backtest_service
from app.domain.multi_backtest import MultiBacktestResult, MultiBacktestRun
from app.schemas.multi_backtests import (
    MultiBacktestResultResponse,
    MultiBacktestRunListResponse,
    MultiBacktestRunRequest,
    MultiBacktestRunResponse,
)
from app.services.multi_backtest_service import MultiBacktestService

router = APIRouter(prefix="/multi-backtests", tags=["multi-asset backtests"])
MultiBacktestServiceDependency = Annotated[
    MultiBacktestService, Depends(get_multi_backtest_service)
]


@router.post(
    "/run",
    response_model=MultiBacktestRunResponse,
    summary="Run one strategy template across top scanner results",
)
def run_multi_backtest(
    request: MultiBacktestRunRequest,
    service: MultiBacktestServiceDependency,
) -> MultiBacktestRunResponse:
    return _run_response(
        service.run(
            scan_run_id=request.scan_run_id,
            template_id=request.template_id,
            parameters=request.parameters,
            top_n=request.top_n,
            start=request.start,
            end=request.end,
            initial_cash=request.initial_cash,
            commission=request.commission,
            slippage=request.slippage,
        )
    )


@router.get(
    "",
    response_model=MultiBacktestRunListResponse,
    summary="List recent multi-asset backtest runs",
)
def list_multi_backtests(
    service: MultiBacktestServiceDependency,
    limit: int = 20,
) -> MultiBacktestRunListResponse:
    runs = service.list_runs(limit=limit)
    return MultiBacktestRunListResponse(
        total=len(runs),
        runs=[_run_response(run) for run in runs],
    )


@router.get(
    "/{run_id}",
    response_model=MultiBacktestRunResponse,
    summary="Read one multi-asset backtest run",
)
def get_multi_backtest(
    run_id: str,
    service: MultiBacktestServiceDependency,
) -> MultiBacktestRunResponse:
    return _run_response(service.get(run_id))


def _run_response(run: MultiBacktestRun) -> MultiBacktestRunResponse:
    return MultiBacktestRunResponse(
        run_id=run.run_id,
        scan_run_id=run.scan_run_id,
        template_id=run.template_id,
        top_n=run.top_n,
        start=run.start_date,
        end=run.end_date,
        parameters=run.parameters,
        initial_cash=run.initial_cash,
        commission=run.commission,
        slippage=run.slippage,
        status=run.status,
        requested_symbols=run.requested_symbols,
        successful_symbols=run.successful_symbols,
        failed_symbols=run.failed_symbols,
        aggregate=run.aggregate,
        created_at=run.created_at,
        results=[_result_response(item) for item in run.results],
    )


def _result_response(item: MultiBacktestResult) -> MultiBacktestResultResponse:
    return MultiBacktestResultResponse(
        rank=item.rank,
        symbol=item.symbol,
        status=item.status,
        strategy_name=item.strategy_name,
        metrics=item.metrics,
        warnings=list(item.warnings),
        error=item.error,
    )
