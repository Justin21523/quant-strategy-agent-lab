from __future__ import annotations

from datetime import date
from uuid import uuid4

from app.domain.errors import (
    InvalidDateRangeError,
    MarketDataError,
    MarketDataLimitError,
    MarketDataNotFoundError,
    UniverseNotFoundError,
    UnsupportedProviderError,
)
from app.domain.market import (
    BatchSyncResult,
    CachedSymbolSummary,
    DataQualityWarning,
    MarketCacheStats,
    MarketSeries,
    ProviderInfo,
    ProviderName,
    ProviderSelection,
    SymbolSyncOutcome,
    SyncStatus,
    WarningSeverity,
)
from app.providers.base import MarketDataProvider
from app.providers.csv_provider import CsvMarketDataProvider
from app.repositories.market_data_repository import MarketDataRepository
from app.services.market_data_normalizer import MarketDataNormalizer


class MarketDataService:
    def __init__(
        self,
        *,
        repository: MarketDataRepository,
        providers: dict[ProviderName, MarketDataProvider],
        normalizer: MarketDataNormalizer,
        seed_demo_data: bool,
        max_response_bars: int,
    ) -> None:
        self.repository = repository
        self.providers = providers
        self.normalizer = normalizer
        self.seed_demo_data = seed_demo_data
        self.max_response_bars = max_response_bars

    def initialize(self) -> None:
        self.repository.initialize()
        csv_provider = self._csv_provider()
        self.repository.upsert_symbols(csv_provider.list_symbols())
        if self.seed_demo_data:
            self.bootstrap_csv_seed()

    def is_ready(self) -> bool:
        return self.repository.ping()

    def bootstrap_csv_seed(self) -> dict[str, int]:
        provider = self._csv_provider()
        imported = 0
        for symbol in provider.list_symbols():
            fetched = provider.fetch_ohlcv(symbol)
            normalized = self.normalizer.normalize(fetched)
            imported += self.repository.insert_bars_if_missing(normalized.bars)
        return {"imported_bars": imported}

    def cache_stats(self) -> MarketCacheStats:
        return self.repository.stats()

    def list_symbols(
        self, *, market: str | None = None, asset_type: str | None = None
    ) -> tuple[CachedSymbolSummary, ...]:
        return self.repository.list_symbol_summaries(market=market, asset_type=asset_type)

    def provider_infos(self) -> tuple[ProviderInfo, ...]:
        yfinance = self.providers[ProviderName.YFINANCE]
        finmind = self.providers[ProviderName.FINMIND]
        return (
            ProviderInfo(
                provider=ProviderName.CSV.value,
                status="ready",
                configured=True,
                supports_sync=True,
                notes="Deterministic offline CSV fixtures for AAPL, SPY, and QQQ.",
            ),
            ProviderInfo(
                provider=ProviderName.YFINANCE.value,
                status="ready" if getattr(yfinance, "enabled", True) else "unavailable",
                configured=getattr(yfinance, "enabled", True),
                supports_sync=getattr(yfinance, "enabled", True),
                notes="Optional network provider. Raw OHLC plus adjusted close are cached locally.",
            ),
            ProviderInfo(
                provider=ProviderName.FINMIND.value,
                status="reserved",
                configured=getattr(finmind, "configured", False),
                supports_sync=False,
                notes="Adapter boundary reserved for TaiwanStockPrice in a later phase.",
            ),
        )

    def get_series(
        self,
        symbol: str,
        *,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> MarketSeries:
        self._validate_range(start, end)
        catalog_symbol = self.repository.get_symbol(symbol)
        cache_summary = self.repository.get_symbol_summary(catalog_symbol.symbol)
        bars = self.repository.get_bars(
            catalog_symbol.symbol, interval=interval, start=start, end=end
        )
        if not bars:
            raise MarketDataNotFoundError(
                "No cached market data matches the requested range.",
                details={"symbol": catalog_symbol.symbol, "start": start, "end": end},
            )
        if len(bars) > self.max_response_bars:
            raise MarketDataLimitError(
                "The requested series exceeds the response row limit.",
                details={"count": len(bars), "limit": self.max_response_bars},
            )

        effective_start = bars[0].trade_date
        effective_end = bars[-1].trade_date
        providers = tuple(sorted({bar.provider for bar in bars}))
        datasets = tuple(sorted({bar.dataset for bar in bars}))
        warnings: list[DataQualityWarning] = []
        contains_fixture = any(bar.is_fixture_data for bar in bars)
        if contains_fixture:
            warnings.append(
                DataQualityWarning(
                    code="synthetic_fixture_data",
                    severity=WarningSeverity.INFO,
                    message=(
                        "This response includes deterministic offline fixture rows. "
                        "They are not observed, live, or current market data."
                    ),
                )
            )
        if start and effective_start > start:
            warnings.append(
                DataQualityWarning(
                    code="requested_start_not_available",
                    severity=WarningSeverity.WARNING,
                    message="Cached data begins after the requested start date.",
                    context={
                        "requested": start.isoformat(),
                        "effective": effective_start.isoformat(),
                    },
                )
            )
        if end and effective_end < end:
            warnings.append(
                DataQualityWarning(
                    code="requested_end_not_available",
                    severity=WarningSeverity.WARNING,
                    message="Cached data ends before the requested end date.",
                    context={"requested": end.isoformat(), "effective": effective_end.isoformat()},
                )
            )
        if len(providers) > 1:
            warnings.append(
                DataQualityWarning(
                    code="mixed_sources",
                    severity=WarningSeverity.INFO,
                    message="The selected range contains rows from multiple providers.",
                    context={"providers": list(providers)},
                )
            )

        return MarketSeries(
            symbol=catalog_symbol,
            cache_summary=cache_summary,
            bars=bars,
            requested_start=start,
            requested_end=end,
            effective_start=effective_start,
            effective_end=effective_end,
            providers=providers,
            datasets=datasets,
            latest_retrieved_at=max(bar.retrieved_at for bar in bars),
            contains_fixture_data=contains_fixture,
            warnings=tuple(warnings),
        )

    def sync(
        self,
        symbols: tuple[str, ...],
        *,
        start: date,
        end: date,
        provider: ProviderSelection,
        allow_fallback: bool,
    ) -> tuple[str, tuple[SymbolSyncOutcome, ...]]:
        self._validate_range(start, end)
        run_id = f"sync_{uuid4().hex[:12]}"
        outcomes: list[SymbolSyncOutcome] = []
        for requested_symbol in symbols:
            normalized_symbol = requested_symbol.strip().upper()
            try:
                catalog_symbol = self.repository.get_symbol(normalized_symbol)
            except MarketDataError as exc:
                outcome = SymbolSyncOutcome(
                    symbol=normalized_symbol,
                    status=SyncStatus.FAILED,
                    requested_provider=provider.value,
                    provider_used=None,
                    fallback_used=False,
                    bars_received=0,
                    bars_stored=0,
                    effective_start=None,
                    effective_end=None,
                    is_fixture_data=False,
                    warnings=(),
                    attempts=(),
                    error=exc.message,
                )
                outcomes.append(outcome)
                continue

            sequence = self._provider_sequence(provider, allow_fallback)
            attempts: list[str] = []
            outcome: SymbolSyncOutcome | None = None
            for index, provider_name in enumerate(sequence):
                adapter = self.providers.get(provider_name)
                if adapter is None:
                    attempts.append(f"{provider_name.value}: provider adapter unavailable")
                    continue
                try:
                    fetched = adapter.fetch_ohlcv(catalog_symbol, start, end)
                    normalized = self.normalizer.normalize(fetched, start=start, end=end)
                    stored = self.repository.upsert_bars(normalized.bars)
                    warnings = list(normalized.warnings)
                    fallback_used = index > 0
                    if fallback_used:
                        warnings.append(
                            DataQualityWarning(
                                code="provider_fallback_used",
                                severity=WarningSeverity.WARNING,
                                message=(
                                    f"The requested provider failed; {provider_name.value} "
                                    "was used as a fallback."
                                ),
                                context={"attempts": attempts.copy()},
                            )
                        )
                    outcome = SymbolSyncOutcome(
                        symbol=catalog_symbol.symbol,
                        status=SyncStatus.SUCCESS,
                        requested_provider=provider.value,
                        provider_used=provider_name.value,
                        fallback_used=fallback_used,
                        bars_received=len(fetched.bars),
                        bars_stored=stored,
                        effective_start=normalized.bars[0].trade_date,
                        effective_end=normalized.bars[-1].trade_date,
                        is_fixture_data=fetched.is_fixture_data,
                        warnings=tuple(warnings),
                        attempts=tuple(attempts + [f"{provider_name.value}: success"]),
                    )
                    break
                except MarketDataError as exc:
                    attempts.append(f"{provider_name.value}: {exc.message}")

            if outcome is None:
                outcome = SymbolSyncOutcome(
                    symbol=catalog_symbol.symbol,
                    status=SyncStatus.FAILED,
                    requested_provider=provider.value,
                    provider_used=None,
                    fallback_used=False,
                    bars_received=0,
                    bars_stored=0,
                    effective_start=None,
                    effective_end=None,
                    is_fixture_data=False,
                    warnings=(),
                    attempts=tuple(attempts),
                    error="All configured provider attempts failed.",
                )
            self.repository.record_sync(
                run_id,
                outcome,
                requested_start=start,
                requested_end=end,
            )
            outcomes.append(outcome)
        return run_id, tuple(outcomes)

    def batch_sync_universe(
        self,
        universe_id: str,
        *,
        start: date,
        end: date,
        provider: ProviderSelection = ProviderSelection.YFINANCE,
        chunk_size: int = 50,
        cursor: int = 0,
        allow_fallback: bool = False,
        mode: str = "all",
        stale_after: date | None = None,
        failed_run_id: str | None = None,
    ) -> BatchSyncResult:
        self._validate_range(start, end)
        universe = self.repository.get_universe(universe_id)
        if universe is None:
            raise UniverseNotFoundError(
                f"Unknown universe: {universe_id}",
                details={"universe_id": universe_id},
            )
        members = self._batch_members(
            universe.members,
            mode=mode,
            stale_after=stale_after,
            failed_run_id=failed_run_id,
        )
        cursor_start = max(0, cursor)
        cursor_end = min(len(members), cursor_start + chunk_size)
        chunk = members[cursor_start:cursor_end]
        child_sync_run_id, outcomes = self.sync(
            tuple(member.symbol for member in chunk),
            start=start,
            end=end,
            provider=provider,
            allow_fallback=allow_fallback,
        )
        successful = sum(item.status is SyncStatus.SUCCESS for item in outcomes)
        failed = len(outcomes) - successful
        next_cursor = None if cursor_end >= len(members) else cursor_end
        complete = next_cursor is None
        run_id = f"batch_sync_{uuid4().hex[:12]}"
        self.repository.record_batch_sync(
            run_id=run_id,
            universe_id=universe_id,
            requested_provider=provider.value,
            requested_start=start,
            requested_end=end,
            chunk_size=chunk_size,
            cursor_start=cursor_start,
            cursor_end=cursor_end,
            next_cursor=next_cursor,
            complete=complete,
            processed=len(outcomes),
            successful=successful,
            failed=failed,
            child_sync_run_id=child_sync_run_id,
        )
        return BatchSyncResult(
            run_id=run_id,
            child_sync_run_id=child_sync_run_id,
            universe_id=universe_id,
            cursor_start=cursor_start,
            cursor_end=cursor_end,
            next_cursor=next_cursor,
            complete=complete,
            processed=len(outcomes),
            successful=successful,
            failed=failed,
            outcomes=outcomes,
        )

    def _batch_members(
        self,
        members,
        *,
        mode: str,
        stale_after: date | None,
        failed_run_id: str | None,
    ):
        if mode == "all":
            return tuple(members)
        if mode == "missing_or_stale":
            if stale_after is None:
                raise InvalidDateRangeError("stale_after is required for missing_or_stale mode")
            selected = []
            for member in members:
                summary = self.repository.get_symbol_summary(member.symbol)
                if summary.last_cached_date is None or summary.last_cached_date < stale_after:
                    selected.append(member)
            return tuple(selected)
        if mode == "retry_failed":
            if not failed_run_id:
                raise InvalidDateRangeError("failed_run_id is required for retry_failed mode")
            records = self.repository.list_sync_runs(run_id=failed_run_id, limit=10_000)
            failed_symbols = {
                str(record["symbol"]).upper()
                for record in records
                if record.get("status") == SyncStatus.FAILED.value
            }
            return tuple(member for member in members if member.symbol.upper() in failed_symbols)
        raise InvalidDateRangeError(
            f"Unsupported batch sync mode: {mode}",
            details={"mode": mode},
        )

    def _provider_sequence(
        self, selection: ProviderSelection, allow_fallback: bool
    ) -> tuple[ProviderName, ...]:
        if selection is ProviderSelection.AUTO:
            if allow_fallback:
                return (ProviderName.YFINANCE, ProviderName.CSV)
            return (ProviderName.YFINANCE,)
        try:
            requested = ProviderName(selection.value)
        except ValueError as exc:
            raise UnsupportedProviderError(
                f"Unsupported provider: {selection.value}",
                details={"provider": selection.value},
            ) from exc
        if allow_fallback and requested is not ProviderName.CSV:
            return (requested, ProviderName.CSV)
        return (requested,)

    @staticmethod
    def _validate_range(start: date | None, end: date | None) -> None:
        if start and end and start > end:
            raise InvalidDateRangeError(
                "start must be on or before end",
                details={"start": start.isoformat(), "end": end.isoformat()},
            )

    def _csv_provider(self) -> CsvMarketDataProvider:
        provider = self.providers[ProviderName.CSV]
        if not isinstance(provider, CsvMarketDataProvider):
            raise RuntimeError("CSV provider is not configured correctly.")
        return provider
