from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path

from app.domain.errors import SymbolNotFoundError
from app.domain.market import (
    CachedSymbolSummary,
    MarketBar,
    MarketCacheStats,
    MarketSymbol,
    SymbolSyncOutcome,
)


class MarketDataRepository:
    def __init__(self, database_path: Path, schema_path: Path) -> None:
        self._database_path = database_path.resolve()
        self._schema_path = schema_path.resolve()

    @property
    def database_path(self) -> Path:
        return self._database_path

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        schema = self._schema_path.read_text(encoding="utf-8")
        with self._connect() as connection:
            connection.executescript(schema)

    def ping(self) -> bool:
        try:
            with self._connect() as connection:
                return connection.execute("SELECT 1").fetchone()[0] == 1
        except sqlite3.Error:
            return False

    def upsert_symbols(self, symbols: Iterable[MarketSymbol]) -> int:
        now = datetime.now(UTC).isoformat()
        rows = [
            (
                item.symbol,
                item.name,
                item.market,
                item.asset_type,
                item.exchange,
                item.currency,
                item.timezone,
                item.default_provider,
                json.dumps(item.supported_providers),
                int(item.is_demo),
                now,
            )
            for item in symbols
        ]
        if not rows:
            return 0
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO symbols (
                    symbol, name, market, asset_type, exchange, currency, timezone,
                    default_provider, supported_providers_json, is_demo, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    name = excluded.name,
                    market = excluded.market,
                    asset_type = excluded.asset_type,
                    exchange = excluded.exchange,
                    currency = excluded.currency,
                    timezone = excluded.timezone,
                    default_provider = excluded.default_provider,
                    supported_providers_json = excluded.supported_providers_json,
                    is_demo = excluded.is_demo,
                    updated_at = excluded.updated_at
                """,
                rows,
            )
        return len(rows)

    def get_symbol(self, symbol: str) -> MarketSymbol:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM symbols WHERE symbol = ?", (symbol.strip().upper(),)
            ).fetchone()
        if row is None:
            raise SymbolNotFoundError(
                f"Unsupported symbol: {symbol.strip().upper()}",
                details={"symbol": symbol.strip().upper()},
            )
        return self._symbol_from_row(row)

    def list_symbol_summaries(
        self, *, market: str | None = None, asset_type: str | None = None
    ) -> tuple[CachedSymbolSummary, ...]:
        clauses: list[str] = []
        parameters: list[str] = []
        if market:
            clauses.append("s.market = ?")
            parameters.append(market.upper())
        if asset_type:
            clauses.append("s.asset_type = ?")
            parameters.append(asset_type.lower())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT
                s.*,
                COUNT(b.trade_date) AS cached_bar_count,
                MIN(b.trade_date) AS first_cached_date,
                MAX(b.trade_date) AS last_cached_date,
                GROUP_CONCAT(DISTINCT b.provider) AS cached_providers
            FROM symbols s
            LEFT JOIN ohlcv_bars b
              ON b.symbol = s.symbol AND b.interval = '1d'
            {where}
            GROUP BY s.symbol
            ORDER BY s.symbol
        """
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return tuple(self._summary_from_row(row) for row in rows)

    def get_symbol_summary(self, symbol: str) -> CachedSymbolSummary:
        normalized_symbol = symbol.strip().upper()
        query = """
            SELECT
                s.*,
                COUNT(b.trade_date) AS cached_bar_count,
                MIN(b.trade_date) AS first_cached_date,
                MAX(b.trade_date) AS last_cached_date,
                GROUP_CONCAT(DISTINCT b.provider) AS cached_providers
            FROM symbols s
            LEFT JOIN ohlcv_bars b
              ON b.symbol = s.symbol AND b.interval = '1d'
            WHERE s.symbol = ?
            GROUP BY s.symbol
        """
        with self._connect() as connection:
            row = connection.execute(query, (normalized_symbol,)).fetchone()
        if row is None:
            raise SymbolNotFoundError(
                f"Unsupported symbol: {normalized_symbol}",
                details={"symbol": normalized_symbol},
            )
        return self._summary_from_row(row)

    def count_bars(self, symbol: str, interval: str = "1d") -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM ohlcv_bars WHERE symbol = ? AND interval = ?",
                (symbol.upper(), interval),
            ).fetchone()
        return int(row["count"])

    def upsert_bars(self, bars: Iterable[MarketBar]) -> int:
        rows = [
            (
                bar.symbol,
                bar.interval,
                bar.trade_date.isoformat(),
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.adjusted_close,
                bar.volume,
                bar.provider,
                bar.dataset,
                bar.source_timezone,
                bar.currency,
                int(bar.is_adjusted),
                int(bar.is_fixture_data),
                bar.retrieved_at.isoformat(),
            )
            for bar in bars
        ]
        if not rows:
            return 0
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO ohlcv_bars (
                    symbol, interval, trade_date, open, high, low, close,
                    adjusted_close, volume, provider, dataset, source_timezone,
                    currency, is_adjusted, is_fixture_data, retrieved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, interval, trade_date) DO UPDATE SET
                    open = excluded.open,
                    high = excluded.high,
                    low = excluded.low,
                    close = excluded.close,
                    adjusted_close = excluded.adjusted_close,
                    volume = excluded.volume,
                    provider = excluded.provider,
                    dataset = excluded.dataset,
                    source_timezone = excluded.source_timezone,
                    currency = excluded.currency,
                    is_adjusted = excluded.is_adjusted,
                    is_fixture_data = excluded.is_fixture_data,
                    retrieved_at = excluded.retrieved_at
                """,
                rows,
            )
        return len(rows)

    def insert_bars_if_missing(self, bars: Iterable[MarketBar]) -> int:
        rows = [
            (
                bar.symbol,
                bar.interval,
                bar.trade_date.isoformat(),
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.adjusted_close,
                bar.volume,
                bar.provider,
                bar.dataset,
                bar.source_timezone,
                bar.currency,
                int(bar.is_adjusted),
                int(bar.is_fixture_data),
                bar.retrieved_at.isoformat(),
            )
            for bar in bars
        ]
        if not rows:
            return 0
        with self._connect() as connection:
            before = connection.total_changes
            connection.executemany(
                """
                INSERT INTO ohlcv_bars (
                    symbol, interval, trade_date, open, high, low, close,
                    adjusted_close, volume, provider, dataset, source_timezone,
                    currency, is_adjusted, is_fixture_data, retrieved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, interval, trade_date) DO NOTHING
                """,
                rows,
            )
            return connection.total_changes - before

    def stats(self) -> MarketCacheStats:
        with self._connect() as connection:
            symbols = connection.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
            bars = connection.execute("SELECT COUNT(*) FROM ohlcv_bars").fetchone()[0]
            sync_records = connection.execute("SELECT COUNT(*) FROM market_sync_runs").fetchone()[0]
        return MarketCacheStats(
            symbols=int(symbols),
            bars=int(bars),
            sync_records=int(sync_records),
        )

    def get_bars(
        self,
        symbol: str,
        *,
        interval: str = "1d",
        start: date | None = None,
        end: date | None = None,
    ) -> tuple[MarketBar, ...]:
        clauses = ["symbol = ?", "interval = ?"]
        parameters: list[object] = [symbol.upper(), interval]
        if start:
            clauses.append("trade_date >= ?")
            parameters.append(start.isoformat())
        if end:
            clauses.append("trade_date <= ?")
            parameters.append(end.isoformat())
        query = f"""
            SELECT * FROM ohlcv_bars
            WHERE {" AND ".join(clauses)}
            ORDER BY trade_date ASC
        """
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return tuple(self._bar_from_row(row) for row in rows)

    def record_sync(
        self,
        run_id: str,
        outcome: SymbolSyncOutcome,
        *,
        requested_start: date | None,
        requested_end: date | None,
    ) -> None:
        warnings = [
            {
                "code": item.code,
                "severity": item.severity.value,
                "message": item.message,
                "affected_rows": item.affected_rows,
                "context": item.context,
            }
            for item in outcome.warnings
        ]
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO market_sync_runs (
                    run_id, symbol, requested_provider, provider_used,
                    requested_start, requested_end, effective_start, effective_end,
                    status, bars_received, bars_stored, fallback_used,
                    is_fixture_data, warnings_json, attempts_json, error, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    outcome.symbol,
                    outcome.requested_provider,
                    outcome.provider_used,
                    requested_start.isoformat() if requested_start else None,
                    requested_end.isoformat() if requested_end else None,
                    outcome.effective_start.isoformat() if outcome.effective_start else None,
                    outcome.effective_end.isoformat() if outcome.effective_end else None,
                    outcome.status.value,
                    outcome.bars_received,
                    outcome.bars_stored,
                    int(outcome.fallback_used),
                    int(outcome.is_fixture_data),
                    json.dumps(warnings),
                    json.dumps(outcome.attempts),
                    outcome.error,
                    datetime.now(UTC).isoformat(),
                ),
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _symbol_from_row(row: sqlite3.Row) -> MarketSymbol:
        return MarketSymbol(
            symbol=row["symbol"],
            name=row["name"],
            market=row["market"],
            asset_type=row["asset_type"],
            exchange=row["exchange"],
            currency=row["currency"],
            timezone=row["timezone"],
            default_provider=row["default_provider"],
            supported_providers=tuple(json.loads(row["supported_providers_json"])),
            is_demo=bool(row["is_demo"]),
        )

    @staticmethod
    def _bar_from_row(row: sqlite3.Row) -> MarketBar:
        return MarketBar(
            symbol=row["symbol"],
            interval=row["interval"],
            trade_date=date.fromisoformat(row["trade_date"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            adjusted_close=float(row["adjusted_close"]),
            volume=int(row["volume"]),
            provider=row["provider"],
            dataset=row["dataset"],
            source_timezone=row["source_timezone"],
            currency=row["currency"],
            is_adjusted=bool(row["is_adjusted"]),
            is_fixture_data=bool(row["is_fixture_data"]),
            retrieved_at=datetime.fromisoformat(row["retrieved_at"]),
        )

    @classmethod
    def _summary_from_row(cls, row: sqlite3.Row) -> CachedSymbolSummary:
        return CachedSymbolSummary(
            symbol=cls._symbol_from_row(row),
            cached_bar_count=int(row["cached_bar_count"]),
            first_cached_date=cls._parse_date(row["first_cached_date"]),
            last_cached_date=cls._parse_date(row["last_cached_date"]),
            cached_providers=tuple(
                sorted(filter(None, (row["cached_providers"] or "").split(",")))
            ),
        )

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        return date.fromisoformat(value) if value else None
