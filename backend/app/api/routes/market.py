import json
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_market_data_service
from app.domain.indicators import IndicatorBundle, IndicatorSeries, IndicatorWarning
from app.domain.market import (
    CachedSymbolSummary,
    DataQualityWarning,
    MarketSeries,
    ProviderInfo,
    SymbolSyncOutcome,
    SyncStatus,
)
from app.schemas.indicators import (
    IndicatorBundleResponse,
    IndicatorPointResponse,
    IndicatorSeriesResponse,
    IndicatorWarningResponse,
)
from app.schemas.market import (
    BatchSyncRequest,
    BatchSyncResponse,
    BatchSyncRunListResponse,
    BatchSyncRunResponse,
    DataQualityWarningResponse,
    DataSourceResponse,
    DateRangeResponse,
    OHLCVBarResponse,
    OHLCVResponse,
    ProviderListResponse,
    ProviderStatusResponse,
    SymbolListResponse,
    SymbolResponse,
    SymbolSyncResultResponse,
    SyncRequest,
    SyncResponse,
    SyncRunRecordListResponse,
    SyncRunRecordResponse,
)
from app.services.indicator_service import IndicatorService
from app.services.market_data_service import MarketDataService

router = APIRouter(prefix="/market", tags=["market data"])
ServiceDependency = Annotated[MarketDataService, Depends(get_market_data_service)]


@router.get(
    "/providers",
    response_model=ProviderListResponse,
    summary="List market-data provider capabilities",
)
def list_providers(service: ServiceDependency) -> ProviderListResponse:
    providers = [_provider_response(item) for item in service.provider_infos()]
    return ProviderListResponse(total=len(providers), providers=providers)


@router.get("/symbols", response_model=SymbolListResponse, summary="List supported symbols")
def list_symbols(
    service: ServiceDependency,
    market: Annotated[str | None, Query(min_length=2, max_length=12)] = None,
    asset_type: Annotated[str | None, Query(min_length=2, max_length=32)] = None,
) -> SymbolListResponse:
    summaries = service.list_symbols(market=market, asset_type=asset_type)
    providers = [_provider_response(item) for item in service.provider_infos()]
    symbols = [_symbol_response(item) for item in summaries]
    return SymbolListResponse(total=len(symbols), symbols=symbols, providers=providers)


@router.get("/ohlcv", response_model=OHLCVResponse, summary="Read cached daily OHLCV")
def get_ohlcv(
    service: ServiceDependency,
    symbol: Annotated[str, Query(min_length=1, max_length=24)],
    start: date | None = None,
    end: date | None = None,
    interval: Annotated[str, Query(pattern="^1d$")] = "1d",
    include_indicators: bool = False,
) -> OHLCVResponse:
    series = service.get_series(symbol, start=start, end=end, interval=interval)
    indicators = None
    if include_indicators:
        indicators = IndicatorService().compute_default_bundle(series.bars)
    return _series_response(series, indicators=indicators)


@router.post("/sync", response_model=SyncResponse, summary="Synchronize provider data into cache")
def sync_market_data(request: SyncRequest, service: ServiceDependency) -> SyncResponse:
    run_id, outcomes = service.sync(
        tuple(request.symbols),
        start=request.start,
        end=request.end,
        provider=request.provider,
        allow_fallback=request.allow_fallback,
    )
    successful = sum(item.status is SyncStatus.SUCCESS for item in outcomes)
    failed = len(outcomes) - successful
    overall = "success" if failed == 0 else "failed" if successful == 0 else "partial"
    return SyncResponse(
        run_id=run_id,
        status=overall,
        requested_range=DateRangeResponse(start=request.start, end=request.end),
        results=[_sync_result_response(item) for item in outcomes],
        successful=successful,
        failed=failed,
    )


@router.post(
    "/batch-sync",
    response_model=BatchSyncResponse,
    summary="Synchronize one chunk from a market universe into cache",
)
def batch_sync_market_data(
    request: BatchSyncRequest, service: ServiceDependency
) -> BatchSyncResponse:
    result = service.batch_sync_universe(
        request.universe_id,
        start=request.start,
        end=request.end,
        provider=request.provider,
        chunk_size=request.chunk_size,
        cursor=request.cursor,
        allow_fallback=request.allow_fallback,
        mode=request.mode,
        stale_after=request.stale_after,
        failed_run_id=request.failed_run_id,
    )
    return BatchSyncResponse(
        run_id=result.run_id,
        child_sync_run_id=result.child_sync_run_id,
        universe_id=result.universe_id,
        cursor_start=result.cursor_start,
        cursor_end=result.cursor_end,
        next_cursor=result.next_cursor,
        complete=result.complete,
        processed=result.processed,
        successful=result.successful,
        failed=result.failed,
        results=[_sync_result_response(item) for item in result.outcomes],
    )


@router.get(
    "/batch-sync/runs",
    response_model=BatchSyncRunListResponse,
    summary="List recent market batch-sync runs",
)
def list_batch_sync_runs(
    service: ServiceDependency,
    universe_id: str | None = None,
    limit: int = 20,
) -> BatchSyncRunListResponse:
    rows = service.repository.list_batch_sync_runs(universe_id=universe_id, limit=limit)
    runs = [_batch_sync_run_response(row) for row in rows]
    return BatchSyncRunListResponse(total=len(runs), runs=runs)


@router.get(
    "/sync-runs",
    response_model=SyncRunRecordListResponse,
    summary="List symbol-level market sync records",
)
def list_sync_runs(
    service: ServiceDependency,
    run_id: str | None = None,
    limit: int = 100,
) -> SyncRunRecordListResponse:
    rows = service.repository.list_sync_runs(run_id=run_id, limit=limit)
    records = [_sync_run_record_response(row) for row in rows]
    return SyncRunRecordListResponse(total=len(records), records=records)


def _series_response(
    series: MarketSeries, *, indicators: IndicatorBundle | None = None
) -> OHLCVResponse:
    cache = series.cache_summary
    summary = SymbolResponse(
        symbol=series.symbol.symbol,
        name=series.symbol.name,
        market=series.symbol.market,
        asset_type=series.symbol.asset_type,
        exchange=series.symbol.exchange,
        currency=series.symbol.currency,
        timezone=series.symbol.timezone,
        default_provider=series.symbol.default_provider,
        supported_providers=list(series.symbol.supported_providers),
        is_demo=series.symbol.is_demo,
        cached_bar_count=cache.cached_bar_count,
        first_cached_date=cache.first_cached_date,
        last_cached_date=cache.last_cached_date,
        cached_providers=list(cache.cached_providers),
    )
    raw_present = any(not bar.is_adjusted for bar in series.bars)
    adjustment = "raw_ohlc_with_adjusted_close" if raw_present else "adjusted_ohlc_snapshot"
    return OHLCVResponse(
        symbol=summary,
        interval="1d",
        requested_range=DateRangeResponse(
            start=series.requested_start,
            end=series.requested_end,
        ),
        effective_range=DateRangeResponse(
            start=series.effective_start,
            end=series.effective_end,
        ),
        source=DataSourceResponse(
            providers=list(series.providers),
            datasets=list(series.datasets),
            served_from_cache=True,
            retrieved_at=series.latest_retrieved_at,
            source_timezone=series.symbol.timezone,
            currency=series.symbol.currency,
            adjustment=adjustment,
            contains_fixture_data=series.contains_fixture_data,
        ),
        count=len(series.bars),
        warnings=[_warning_response(warning) for warning in series.warnings],
        bars=[
            OHLCVBarResponse(
                date=bar.trade_date,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                adjusted_close=bar.adjusted_close,
                volume=bar.volume,
                provider=bar.provider,
                is_fixture_data=bar.is_fixture_data,
            )
            for bar in series.bars
        ],
        indicators=_indicator_bundle_response(indicators) if indicators else None,
    )


def _indicator_bundle_response(bundle: IndicatorBundle) -> IndicatorBundleResponse:
    return IndicatorBundleResponse(
        profile=bundle.profile,
        count=bundle.count,
        warnings=[_indicator_warning_response(warning) for warning in bundle.warnings],
        series=[_indicator_series_response(item) for item in bundle.series],
    )


def _indicator_series_response(series: IndicatorSeries) -> IndicatorSeriesResponse:
    return IndicatorSeriesResponse(
        key=series.key,
        kind=series.kind,
        label=series.label,
        pane=series.pane,
        parameters=series.parameters,
        warmup_period=series.warmup_period,
        values=[
            IndicatorPointResponse(date=point.date, values=point.values) for point in series.values
        ],
    )


def _indicator_warning_response(warning: IndicatorWarning) -> IndicatorWarningResponse:
    return IndicatorWarningResponse(
        code=warning.code,
        severity=warning.severity,
        message=warning.message,
        context=warning.context,
    )


def _sync_result_response(item: SymbolSyncOutcome) -> SymbolSyncResultResponse:
    return SymbolSyncResultResponse(
        symbol=item.symbol,
        status=item.status,
        requested_provider=item.requested_provider,
        provider_used=item.provider_used,
        fallback_used=item.fallback_used,
        bars_received=item.bars_received,
        bars_stored=item.bars_stored,
        effective_range=DateRangeResponse(
            start=item.effective_start,
            end=item.effective_end,
        ),
        is_fixture_data=item.is_fixture_data,
        warnings=[_warning_response(warning) for warning in item.warnings],
        attempts=list(item.attempts),
        error=item.error,
    )


def _batch_sync_run_response(row: dict[str, object]) -> BatchSyncRunResponse:
    return BatchSyncRunResponse(
        run_id=str(row["run_id"]),
        child_sync_run_id=str(row["child_sync_run_id"]),
        universe_id=str(row["universe_id"]),
        requested_provider=str(row["requested_provider"]),
        requested_range=DateRangeResponse(
            start=_optional_date(row["requested_start"]),
            end=_optional_date(row["requested_end"]),
        ),
        chunk_size=int(row["chunk_size"]),
        cursor_start=int(row["cursor_start"]),
        cursor_end=int(row["cursor_end"]),
        next_cursor=int(row["next_cursor"]) if row["next_cursor"] is not None else None,
        complete=bool(row["complete"]),
        processed=int(row["processed"]),
        successful=int(row["successful"]),
        failed=int(row["failed"]),
        created_at=datetime.fromisoformat(str(row["created_at"])),
    )


def _sync_run_record_response(row: dict[str, object]) -> SyncRunRecordResponse:
    warnings = json.loads(str(row["warnings_json"]))
    return SyncRunRecordResponse(
        run_id=str(row["run_id"]),
        symbol=str(row["symbol"]),
        requested_provider=str(row["requested_provider"]),
        provider_used=str(row["provider_used"]) if row["provider_used"] else None,
        requested_range=DateRangeResponse(
            start=_optional_date(row["requested_start"]),
            end=_optional_date(row["requested_end"]),
        ),
        effective_range=DateRangeResponse(
            start=_optional_date(row["effective_start"]),
            end=_optional_date(row["effective_end"]),
        ),
        status=SyncStatus(str(row["status"])),
        bars_received=int(row["bars_received"]),
        bars_stored=int(row["bars_stored"]),
        fallback_used=bool(row["fallback_used"]),
        is_fixture_data=bool(row["is_fixture_data"]),
        warnings=[
            DataQualityWarningResponse(
                code=str(item["code"]),
                severity=item["severity"],
                message=str(item["message"]),
                affected_rows=int(item.get("affected_rows", 0)),
                context=dict(item.get("context", {})),
            )
            for item in warnings
        ],
        attempts=list(json.loads(str(row["attempts_json"]))),
        error=str(row["error"]) if row["error"] else None,
        created_at=datetime.fromisoformat(str(row["created_at"])),
    )


def _optional_date(value: object) -> date | None:
    return date.fromisoformat(str(value)) if value else None


def _symbol_response(summary: CachedSymbolSummary) -> SymbolResponse:
    symbol = summary.symbol
    return SymbolResponse(
        symbol=symbol.symbol,
        name=symbol.name,
        market=symbol.market,
        asset_type=symbol.asset_type,
        exchange=symbol.exchange,
        currency=symbol.currency,
        timezone=symbol.timezone,
        default_provider=symbol.default_provider,
        supported_providers=list(symbol.supported_providers),
        is_demo=symbol.is_demo,
        cached_bar_count=summary.cached_bar_count,
        first_cached_date=summary.first_cached_date,
        last_cached_date=summary.last_cached_date,
        cached_providers=list(summary.cached_providers),
    )


def _warning_response(warning: DataQualityWarning) -> DataQualityWarningResponse:
    return DataQualityWarningResponse(
        code=warning.code,
        severity=warning.severity,
        message=warning.message,
        affected_rows=warning.affected_rows,
        context=warning.context,
    )


def _provider_response(provider: ProviderInfo) -> ProviderStatusResponse:
    return ProviderStatusResponse(
        provider=provider.provider,
        status=provider.status,
        configured=provider.configured,
        supports_sync=provider.supports_sync,
        notes=provider.notes,
    )
