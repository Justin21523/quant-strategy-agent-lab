from __future__ import annotations

from datetime import date

from app.domain.errors import ProviderNotImplementedError
from app.domain.market import MarketSymbol, ProviderFetchResult, ProviderName


class FinMindMarketDataProvider:
    """Reserved provider boundary for Taiwan-market data in a later phase."""

    name = ProviderName.FINMIND

    def __init__(self, token: str | None = None) -> None:
        self.configured = bool(token)

    def list_symbols(self) -> tuple[MarketSymbol, ...]:
        return ()

    def fetch_ohlcv(
        self,
        symbol: MarketSymbol,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderFetchResult:
        raise ProviderNotImplementedError(
            "The FinMind adapter is reserved, but synchronization is not enabled in Phase 1.",
            details={
                "symbol": symbol.symbol,
                "configured": self.configured,
                "planned_dataset": "TaiwanStockPrice",
            },
        )
