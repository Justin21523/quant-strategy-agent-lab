from __future__ import annotations

from datetime import date
from typing import Protocol

from app.domain.market import MarketSymbol, ProviderFetchResult, ProviderName


class MarketDataProvider(Protocol):
    name: ProviderName

    def list_symbols(self) -> tuple[MarketSymbol, ...]: ...

    def fetch_ohlcv(
        self,
        symbol: MarketSymbol,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderFetchResult: ...
