from __future__ import annotations

from datetime import UTC, datetime
from urllib.error import URLError
from urllib.request import urlopen

from app.domain.errors import UniverseNotFoundError, UniverseRefreshError
from app.domain.market import MarketSymbol, ProviderName
from app.domain.universe import (
    UniverseDetail,
    UniverseMember,
    UniverseRefreshResult,
    UniverseSummary,
)
from app.repositories.market_data_repository import MarketDataRepository

US_COMMON_STOCKS_ID = "us_common_stocks"
NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


class UniverseService:
    def __init__(self, repository: MarketDataRepository) -> None:
        self.repository = repository

    def list_universes(self) -> tuple[UniverseSummary, ...]:
        return self.repository.list_universes()

    def get_universe(self, universe_id: str) -> UniverseDetail:
        universe = self.repository.get_universe(universe_id)
        if universe is None:
            raise UniverseNotFoundError(
                f"Unknown universe: {universe_id}",
                details={"universe_id": universe_id},
            )
        return universe

    def refresh_us_common_stocks(
        self,
        *,
        nasdaq_text: str | None = None,
        other_text: str | None = None,
    ) -> UniverseRefreshResult:
        nasdaq_text = nasdaq_text if nasdaq_text is not None else self._download(NASDAQ_LISTED_URL)
        other_text = other_text if other_text is not None else self._download(OTHER_LISTED_URL)
        members = tuple(
            sorted(
                {
                    member.symbol: member
                    for member in (
                        *parse_nasdaq_listed(nasdaq_text),
                        *parse_other_listed(other_text),
                    )
                }.values(),
                key=lambda item: item.symbol,
            )
        )
        refreshed_at = datetime.now(UTC).replace(microsecond=0)
        summary = UniverseSummary(
            universe_id=US_COMMON_STOCKS_ID,
            name="US Common Stocks",
            description="US listed common stocks parsed from Nasdaq Trader symbol directory files.",
            market="US",
            asset_type="equity",
            source="nasdaq_trader_symbol_directory",
            source_url=f"{NASDAQ_LISTED_URL} + {OTHER_LISTED_URL}",
            member_count=len(members),
            refreshed_at=refreshed_at,
        )
        symbols = [
            MarketSymbol(
                symbol=member.symbol,
                name=member.name,
                market="US",
                asset_type="equity",
                exchange=member.exchange,
                currency=member.currency,
                timezone="America/New_York",
                default_provider=ProviderName.YFINANCE.value,
                supported_providers=(ProviderName.YFINANCE.value,),
                is_demo=False,
            )
            for member in members
        ]
        inserted = self.repository.upsert_symbols(symbols)
        self.repository.upsert_universe(summary, members)
        return UniverseRefreshResult(summary=summary, inserted_symbols=inserted, members=members)

    @staticmethod
    def _download(url: str) -> str:
        try:
            with urlopen(url, timeout=20) as response:  # noqa: S310 - fixed official URL.
                return response.read().decode("utf-8")
        except (OSError, URLError) as exc:
            raise UniverseRefreshError(
                "Unable to refresh the US common-stock universe from Nasdaq Trader.",
                details={"url": url, "error": str(exc)},
            ) from exc


def parse_nasdaq_listed(text: str) -> tuple[UniverseMember, ...]:
    rows = _pipe_rows(text)
    members: list[UniverseMember] = []
    for row in rows:
        symbol = row.get("Symbol", "").strip().upper()
        name = row.get("Security Name", "").strip()
        if not _is_common_stock(symbol, name, row.get("ETF"), row.get("Test Issue")):
            continue
        members.append(
            UniverseMember(
                symbol=symbol,
                name=name,
                exchange="NASDAQ",
                asset_type="equity",
                currency="USD",
                provider_symbol=symbol,
                metadata={
                    "market_category": row.get("Market Category", ""),
                    "financial_status": row.get("Financial Status", ""),
                },
            )
        )
    return tuple(members)


def parse_other_listed(text: str) -> tuple[UniverseMember, ...]:
    rows = _pipe_rows(text)
    members: list[UniverseMember] = []
    exchange_names = {"A": "NYSE American", "N": "NYSE", "P": "NYSE Arca", "Z": "BATS"}
    for row in rows:
        symbol = row.get("ACT Symbol", "").strip().upper()
        name = row.get("Security Name", "").strip()
        if not _is_common_stock(symbol, name, row.get("ETF"), row.get("Test Issue")):
            continue
        exchange_code = row.get("Exchange", "").strip()
        members.append(
            UniverseMember(
                symbol=symbol,
                name=name,
                exchange=exchange_names.get(exchange_code, exchange_code or "OTHER"),
                asset_type="equity",
                currency="USD",
                provider_symbol=symbol,
                metadata={"exchange_code": exchange_code, "cqs_symbol": row.get("CQS Symbol", "")},
            )
        )
    return tuple(members)


def _pipe_rows(text: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    header = lines[0].split("|")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if line.startswith("File Creation Time"):
            continue
        values = line.split("|")
        if len(values) != len(header):
            continue
        rows.append(dict(zip(header, values, strict=True)))
    return rows


def _is_common_stock(symbol: str, name: str, etf: str | None, test_issue: str | None) -> bool:
    if not symbol or etf == "Y" or test_issue == "Y":
        return False
    if any(token in symbol for token in ("$", "^", "/", "=")):
        return False
    lowered = name.lower()
    excluded_terms = (
        " warrant",
        " right",
        " unit",
        " preferred",
        " preference",
        " note",
        " bond",
        " debenture",
        " etf",
        " fund",
        " trust",
        " etn",
        " nextshares",
    )
    return not any(term in lowered for term in excluded_terms)
