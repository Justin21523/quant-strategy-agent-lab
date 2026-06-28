from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.domain.data_quality import SymbolQuality, UniverseQualityReport
from app.domain.errors import InvalidDateRangeError, UniverseNotFoundError
from app.repositories.market_data_repository import MarketDataRepository


class DataQualityService:
    def __init__(self, repository: MarketDataRepository) -> None:
        self.repository = repository

    def universe_report(
        self,
        universe_id: str,
        *,
        start: date,
        end: date,
        limit: int = 500,
    ) -> UniverseQualityReport:
        if start > end:
            raise InvalidDateRangeError("start must be on or before end")
        universe = self.repository.get_universe(universe_id)
        if universe is None:
            raise UniverseNotFoundError(
                f"Unknown universe: {universe_id}",
                details={"universe_id": universe_id},
            )
        expected_weekdays = _weekdays_between(start, end)
        symbols: list[SymbolQuality] = []
        for member in universe.members[:limit]:
            bars = self.repository.get_bars(member.symbol, start=start, end=end)
            dates = {bar.trade_date for bar in bars}
            providers = tuple(sorted({bar.provider for bar in bars}))
            contains_fixture = any(bar.is_fixture_data for bar in bars)
            warnings: list[str] = []
            if not bars:
                warnings.append("no_cached_bars")
            if len(bars) < 200:
                warnings.append("insufficient_sma_200")
            if len(bars) < 253:
                warnings.append("insufficient_return_252d")
            if contains_fixture:
                warnings.append("contains_fixture_data")
            symbols.append(
                SymbolQuality(
                    symbol=member.symbol,
                    name=member.name,
                    exchange=member.exchange,
                    cached_bar_count=len(bars),
                    first_cached_date=bars[0].trade_date if bars else None,
                    last_cached_date=bars[-1].trade_date if bars else None,
                    missing_weekday_count=max(0, len(expected_weekdays - dates)),
                    providers=providers,
                    contains_fixture_data=contains_fixture,
                    supports_sma_200=len(bars) >= 200,
                    supports_return_252d=len(bars) >= 253,
                    warnings=tuple(warnings),
                )
            )
        covered = sum(item.cached_bar_count > 0 for item in symbols)
        member_count = universe.summary.member_count
        coverage_pct = (covered / member_count * 100) if member_count else 0.0
        return UniverseQualityReport(
            universe_id=universe_id,
            member_count=member_count,
            refreshed_at=universe.summary.refreshed_at,
            requested_start=start,
            requested_end=end,
            covered_symbols=covered,
            coverage_pct=round(coverage_pct, 2),
            fixture_symbols=sum(item.contains_fixture_data for item in symbols),
            sma_200_ready_symbols=sum(item.supports_sma_200 for item in symbols),
            return_252d_ready_symbols=sum(item.supports_return_252d for item in symbols),
            generated_at=datetime.now(UTC).replace(microsecond=0),
            symbols=tuple(symbols),
        )


def _weekdays_between(start: date, end: date) -> set[date]:
    current = start
    days: set[date] = set()
    while current <= end:
        if current.weekday() < 5:
            days.add(current)
        current += timedelta(days=1)
    return days
