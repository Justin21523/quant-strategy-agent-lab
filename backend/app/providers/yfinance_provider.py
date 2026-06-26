from __future__ import annotations

import inspect
import math
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from app.domain.errors import ProviderDataError, ProviderUnavailableError
from app.domain.market import MarketSymbol, ProviderFetchResult, ProviderName, SourceBar

DownloadFunction = Callable[..., pd.DataFrame | None]


class YFinanceMarketDataProvider:
    name = ProviderName.YFINANCE

    def __init__(
        self,
        *,
        enabled: bool = True,
        timeout_seconds: float = 10.0,
        download_function: DownloadFunction | None = None,
    ) -> None:
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self._download = download_function or yf.download

    def list_symbols(self) -> tuple[MarketSymbol, ...]:
        return ()

    def fetch_ohlcv(
        self,
        symbol: MarketSymbol,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderFetchResult:
        if not self.enabled:
            raise ProviderUnavailableError("The yfinance provider is disabled by configuration.")
        if not start or not end:
            raise ProviderDataError(
                "yfinance synchronization requires explicit start and end dates."
            )

        kwargs: dict[str, Any] = {
            "tickers": symbol.symbol,
            "start": start.isoformat(),
            # yfinance treats end as exclusive.
            "end": (end + timedelta(days=1)).isoformat(),
            "interval": "1d",
            "actions": False,
            "auto_adjust": False,
            "progress": False,
            "threads": False,
            "timeout": self.timeout_seconds,
        }
        try:
            if "multi_level_index" in inspect.signature(self._download).parameters:
                kwargs["multi_level_index"] = False
        except (TypeError, ValueError):
            # Some test doubles and wrappers do not expose a Python signature.
            pass

        try:
            frame = self._download(**kwargs)
        except Exception as exc:
            raise ProviderUnavailableError(
                "yfinance could not retrieve market data.",
                details={"symbol": symbol.symbol, "reason": str(exc)},
            ) from exc
        if frame is None or frame.empty:
            raise ProviderDataError(
                "yfinance returned no rows for the requested range.",
                details={
                    "symbol": symbol.symbol,
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                },
            )

        normalized_frame = self._flatten_columns(frame, symbol.symbol)
        columns = {
            str(column).strip().lower().replace(" ", "_"): column
            for column in normalized_frame.columns
        }
        required = {"open", "high", "low", "close", "volume"}
        missing = required - columns.keys()
        if missing:
            raise ProviderDataError(
                "yfinance response is missing required OHLCV columns.",
                details={"symbol": symbol.symbol, "missing_columns": sorted(missing)},
            )

        bars: list[SourceBar] = []
        for timestamp, row in normalized_frame.iterrows():
            values = {
                key: self._to_float(row[column])
                for key, column in columns.items()
                if key in required | {"adj_close", "adjusted_close"}
            }
            adjusted = values.get("adj_close", values.get("adjusted_close", values.get("close")))
            bars.append(
                SourceBar(
                    trade_date=pd.Timestamp(timestamp).date(),
                    open=values.get("open"),
                    high=values.get("high"),
                    low=values.get("low"),
                    close=values.get("close"),
                    adjusted_close=adjusted,
                    volume=values.get("volume"),
                )
            )

        return ProviderFetchResult(
            symbol=symbol,
            provider=self.name,
            dataset="Yahoo Finance daily history via yfinance",
            bars=tuple(bars),
            is_adjusted=False,
            is_fixture_data=False,
            warnings=(
                "yfinance is an independent wrapper around Yahoo Finance public endpoints; "
                "use downloaded data for personal research under the provider terms.",
            ),
            metadata={"auto_adjust": False, "interval": "1d"},
        )

    @staticmethod
    def _flatten_columns(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
        if not isinstance(frame.columns, pd.MultiIndex):
            return frame
        if symbol in frame.columns.get_level_values(-1):
            return frame.xs(symbol, axis=1, level=-1)
        copy = frame.copy()
        copy.columns = copy.columns.get_level_values(0)
        return copy

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            converted = float(value)
        except (TypeError, ValueError):
            return None
        return converted if math.isfinite(converted) else None
