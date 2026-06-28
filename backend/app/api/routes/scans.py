from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_scanner_service
from app.domain.quality import DataQualityGate
from app.domain.scanner import ScannerRules, ScanResult, ScanRun, SkippedSymbol
from app.schemas.scans import (
    ScannerCapabilityResponse,
    ScannerPresetListResponse,
    ScannerPresetResponse,
    ScannerRulesRequest,
    ScanResultResponse,
    ScanRunListResponse,
    ScanRunRequest,
    ScanRunResponse,
    SkippedSymbolResponse,
)
from app.services.scanner_service import ScannerService

router = APIRouter(prefix="/scans", tags=["stock scanner"])
ScannerServiceDependency = Annotated[ScannerService, Depends(get_scanner_service)]


@router.get(
    "/capabilities",
    response_model=ScannerCapabilityResponse,
    summary="Describe scanner defaults and sortable metrics",
)
def scanner_capabilities() -> ScannerCapabilityResponse:
    return ScannerCapabilityResponse(
        default_sort_key="return_60d_pct",
        sortable_keys=[
            "close",
            "volume",
            "sma_20",
            "sma_60",
            "sma_200",
            "ema_20",
            "rsi_14",
            "atr_14",
            "atr_pct",
            "volume_ratio_20d",
            "return_20d_pct",
            "return_60d_pct",
            "return_252d_pct",
        ],
        default_rules=ScannerRulesRequest(),
    )


@router.post("/run", response_model=ScanRunResponse, summary="Run a stock scanner")
def run_scan(
    request: ScanRunRequest,
    service: ScannerServiceDependency,
) -> ScanRunResponse:
    run = service.run_scan(
        universe_id=request.universe_id,
        start=request.start,
        end=request.end,
        rules=ScannerRules(**request.rules.model_dump()),
        sort_key=request.sort_key,
        sort_direction=request.sort_direction,
        result_limit=request.result_limit,
        quality_gate=DataQualityGate(**request.quality_gate.model_dump())
        if request.quality_gate
        else None,
    )
    return _run_response(run)


@router.get("", response_model=ScanRunListResponse, summary="List recent scanner runs")
def list_scans(service: ScannerServiceDependency, limit: int = 20) -> ScanRunListResponse:
    runs = service.list_scans(limit=limit)
    return ScanRunListResponse(
        total=len(runs),
        runs=[_run_response(run) for run in runs],
    )


@router.get(
    "/presets",
    response_model=ScannerPresetListResponse,
    summary="List built-in scanner presets",
)
def list_presets(service: ScannerServiceDependency) -> ScannerPresetListResponse:
    labels = {
        "trend_momentum": (
            "Trend Momentum",
            "Large-cap style trend screen focused on SMA alignment, RSI strength, and 60D return.",
        ),
        "pullback_in_uptrend": (
            "Pullback in Uptrend",
            "Uptrend candidates with moderate RSI after a short-term pullback.",
        ),
        "volume_breakout": (
            "Volume Breakout",
            "Symbols with positive medium-term return and elevated 20D volume ratio.",
        ),
        "low_volatility_trend": (
            "Low Volatility Trend",
            "Trend candidates constrained by ATR percent for smoother behavior.",
        ),
        "oversold_watchlist": (
            "Oversold Watchlist",
            "Relaxed trend watchlist for oversold names that need manual review.",
        ),
    }
    presets = []
    for preset_id, rules in service.presets().items():
        name, description = labels[preset_id]
        presets.append(
            ScannerPresetResponse(
                preset_id=preset_id,
                name=name,
                description=description,
                rules=ScannerRulesRequest(**asdict(rules)),
            )
        )
    return ScannerPresetListResponse(total=len(presets), presets=presets)


@router.get("/{run_id}", response_model=ScanRunResponse, summary="Read one scanner run")
def get_scan(run_id: str, service: ScannerServiceDependency) -> ScanRunResponse:
    return _run_response(service.get_scan(run_id))


def _run_response(run: ScanRun) -> ScanRunResponse:
    return ScanRunResponse(
        run_id=run.run_id,
        universe_id=run.universe_id,
        start=run.start_date,
        end=run.end_date,
        rules=ScannerRulesRequest(**asdict(run.rules)),
        sort_key=run.sort_key,
        sort_direction=run.sort_direction,
        result_limit=run.result_limit,
        status=run.status,
        total_symbols=run.total_symbols,
        analyzed_symbols=run.analyzed_symbols,
        matched_symbols=run.matched_symbols,
        skipped_symbols=run.skipped_symbols,
        warnings=list(run.warnings),
        created_at=run.created_at,
        results=[_result_response(result) for result in run.results],
        skipped=[_skipped_response(item) for item in run.skipped],
    )


def _result_response(result: ScanResult) -> ScanResultResponse:
    return ScanResultResponse(
        rank=result.rank,
        symbol=result.symbol,
        name=result.name,
        exchange=result.exchange,
        metrics=result.metrics,
        matched_rules=list(result.matched_rules),
        failed_rules=list(result.failed_rules),
        warnings=list(result.warnings),
    )


def _skipped_response(item: SkippedSymbol) -> SkippedSymbolResponse:
    return SkippedSymbolResponse(
        symbol=item.symbol,
        name=item.name,
        reason=item.reason,
        cached_rows=item.cached_rows,
        required_rows=item.required_rows,
        details=item.details,
    )
