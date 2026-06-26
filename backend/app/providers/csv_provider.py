from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from app.domain.errors import ProviderDataError, SymbolNotFoundError
from app.domain.market import MarketSymbol, ProviderFetchResult, ProviderName, SourceBar

_REQUIRED_BAR_COLUMNS = {
    "date",
    "open",
    "high",
    "low",
    "close",
    "adjusted_close",
    "volume",
}
_REQUIRED_MANIFEST_COLUMNS = {
    "symbol",
    "name",
    "market",
    "asset_type",
    "exchange",
    "currency",
    "timezone",
    "filename",
    "is_fixture_data",
    "is_adjusted",
    "dataset",
}


class CsvMarketDataProvider:
    name = ProviderName.CSV

    def __init__(self, seed_dir: Path) -> None:
        self.seed_dir = seed_dir.resolve()
        self._manifest = self._load_manifest()

    def _load_manifest(self) -> dict[str, dict[str, str]]:
        manifest_path = self.seed_dir / "symbols.csv"
        if not manifest_path.exists():
            raise ProviderDataError(
                "CSV symbol manifest is missing.", details={"path": str(manifest_path)}
            )
        with manifest_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            missing = _REQUIRED_MANIFEST_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise ProviderDataError(
                    "CSV symbol manifest has missing columns.",
                    details={"missing_columns": sorted(missing)},
                )
            return {row["symbol"].strip().upper(): row for row in reader}

    def list_symbols(self) -> tuple[MarketSymbol, ...]:
        return tuple(
            self._symbol_from_row(row)
            for _, row in sorted(self._manifest.items(), key=lambda item: item[0])
        )

    def fetch_ohlcv(
        self,
        symbol: MarketSymbol,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderFetchResult:
        normalized = symbol.symbol.strip().upper()
        row = self._manifest.get(normalized)
        if row is None:
            raise SymbolNotFoundError(
                f"Symbol {normalized} is not present in the bundled CSV catalog.",
                details={"symbol": normalized, "provider": self.name.value},
            )

        file_path = (self.seed_dir / row["filename"]).resolve()
        if self.seed_dir not in file_path.parents:
            raise ProviderDataError("CSV manifest references a path outside the seed directory.")
        if not file_path.exists():
            raise ProviderDataError(
                "CSV market data file is missing.", details={"path": str(file_path)}
            )

        bars: list[SourceBar] = []
        with file_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            missing = _REQUIRED_BAR_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise ProviderDataError(
                    "CSV market data file has missing columns.",
                    details={"path": str(file_path), "missing_columns": sorted(missing)},
                )
            for line_number, raw in enumerate(reader, start=2):
                try:
                    trade_date = date.fromisoformat(raw["date"])
                    if start and trade_date < start:
                        continue
                    if end and trade_date > end:
                        continue
                    bars.append(
                        SourceBar(
                            trade_date=trade_date,
                            open=float(raw["open"]),
                            high=float(raw["high"]),
                            low=float(raw["low"]),
                            close=float(raw["close"]),
                            adjusted_close=float(raw["adjusted_close"]),
                            volume=float(raw["volume"]),
                        )
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise ProviderDataError(
                        "CSV market data contains an invalid row.",
                        details={
                            "path": str(file_path),
                            "line": line_number,
                            "reason": str(exc),
                        },
                    ) from exc

        is_fixture = row["is_fixture_data"].strip().lower() in {"1", "true", "yes"}
        is_adjusted = row["is_adjusted"].strip().lower() in {"1", "true", "yes"}
        warnings = (
            (
                "Bundled CSV data is a deterministic synthetic fixture for offline development; "
                "it is not observed, live, or current market data.",
            )
            if is_fixture
            else ()
        )
        return ProviderFetchResult(
            symbol=self._symbol_from_row(row),
            provider=self.name,
            dataset=row["dataset"].strip(),
            bars=tuple(bars),
            is_adjusted=is_adjusted,
            is_fixture_data=is_fixture,
            warnings=warnings,
            metadata={"file": row["filename"], "source_note": row.get("source_note", "")},
        )

    @staticmethod
    def _symbol_from_row(row: dict[str, str]) -> MarketSymbol:
        return MarketSymbol(
            symbol=row["symbol"].strip().upper(),
            name=row["name"].strip(),
            market=row["market"].strip().upper(),
            asset_type=row["asset_type"].strip().lower(),
            exchange=row["exchange"].strip(),
            currency=row["currency"].strip().upper(),
            timezone=row["timezone"].strip(),
            default_provider=ProviderName.YFINANCE.value,
            supported_providers=(ProviderName.YFINANCE.value, ProviderName.CSV.value),
            is_demo=True,
        )
