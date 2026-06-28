from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

from app.domain.errors import SymbolNotFoundError
from app.domain.jobs import JobEvent, JobKind, JobRun, JobStatus
from app.domain.market import (
    CachedSymbolSummary,
    MarketBar,
    MarketCacheStats,
    MarketSymbol,
    SymbolSyncOutcome,
)
from app.domain.multi_backtest import (
    MultiBacktestResult,
    MultiBacktestRun,
    MultiBacktestStatus,
)
from app.domain.portfolio import (
    PortfolioEquityPoint,
    PortfolioHolding,
    PortfolioPreset,
    PortfolioRun,
    PortfolioRunStatus,
    PortfolioSelectionMode,
    RebalanceEvent,
    RebalanceFrequency,
    SkippedPeriod,
)
from app.domain.research import ResearchPreset
from app.domain.scanner import (
    ScannerRules,
    ScanResult,
    ScanRun,
    ScanStatus,
    SkippedSymbol,
    SortDirection,
)
from app.domain.universe import UniverseDetail, UniverseMember, UniverseSummary


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

    def upsert_universe(
        self,
        summary: UniverseSummary,
        members: Iterable[UniverseMember],
    ) -> int:
        member_rows = [
            (
                summary.universe_id,
                member.symbol,
                member.name,
                member.exchange,
                member.asset_type,
                member.currency,
                member.provider_symbol,
                int(member.is_active),
                json.dumps(member.metadata),
                summary.refreshed_at.isoformat(),
            )
            for member in members
        ]
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO universes (
                    universe_id, name, description, market, asset_type, source,
                    source_url, member_count, refreshed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(universe_id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    market = excluded.market,
                    asset_type = excluded.asset_type,
                    source = excluded.source,
                    source_url = excluded.source_url,
                    member_count = excluded.member_count,
                    refreshed_at = excluded.refreshed_at
                """,
                (
                    summary.universe_id,
                    summary.name,
                    summary.description,
                    summary.market,
                    summary.asset_type,
                    summary.source,
                    summary.source_url,
                    len(member_rows),
                    summary.refreshed_at.isoformat(),
                ),
            )
            connection.execute(
                "DELETE FROM universe_members WHERE universe_id = ?",
                (summary.universe_id,),
            )
            if member_rows:
                connection.executemany(
                    """
                    INSERT INTO universe_members (
                        universe_id, symbol, name, exchange, asset_type, currency,
                        provider_symbol, is_active, metadata_json, added_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    member_rows,
                )
        return len(member_rows)

    def list_universes(self) -> tuple[UniverseSummary, ...]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM universes ORDER BY universe_id").fetchall()
        return tuple(self._universe_summary_from_row(row) for row in rows)

    def get_universe(self, universe_id: str) -> UniverseDetail | None:
        with self._connect() as connection:
            summary_row = connection.execute(
                "SELECT * FROM universes WHERE universe_id = ?",
                (universe_id,),
            ).fetchone()
            if summary_row is None:
                return None
            member_rows = connection.execute(
                """
                SELECT * FROM universe_members
                WHERE universe_id = ? AND is_active = 1
                ORDER BY symbol
                """,
                (universe_id,),
            ).fetchall()
        return UniverseDetail(
            summary=self._universe_summary_from_row(summary_row),
            members=tuple(self._universe_member_from_row(row) for row in member_rows),
        )

    def record_batch_sync(
        self,
        *,
        run_id: str,
        universe_id: str,
        requested_provider: str,
        requested_start: date,
        requested_end: date,
        chunk_size: int,
        cursor_start: int,
        cursor_end: int,
        next_cursor: int | None,
        complete: bool,
        processed: int,
        successful: int,
        failed: int,
        child_sync_run_id: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO market_batch_sync_runs (
                    run_id, universe_id, requested_provider, requested_start,
                    requested_end, chunk_size, cursor_start, cursor_end,
                    next_cursor, complete, processed, successful, failed,
                    child_sync_run_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    universe_id,
                    requested_provider,
                    requested_start.isoformat(),
                    requested_end.isoformat(),
                    chunk_size,
                    cursor_start,
                    cursor_end,
                    next_cursor,
                    int(complete),
                    processed,
                    successful,
                    failed,
                    child_sync_run_id,
                    datetime.now(UTC).isoformat(),
                ),
            )

    def save_scan_run(self, run: ScanRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scan_runs (
                    run_id, universe_id, start_date, end_date, rules_json,
                    sort_key, sort_direction, result_limit, status,
                    total_symbols, analyzed_symbols, matched_symbols,
                    skipped_symbols, warnings_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.universe_id,
                    run.start_date.isoformat(),
                    run.end_date.isoformat(),
                    json.dumps(asdict(run.rules)),
                    run.sort_key,
                    run.sort_direction.value,
                    run.result_limit,
                    run.status.value,
                    run.total_symbols,
                    run.analyzed_symbols,
                    run.matched_symbols,
                    run.skipped_symbols,
                    json.dumps(run.warnings),
                    run.created_at.isoformat(),
                ),
            )
            if run.results:
                connection.executemany(
                    """
                    INSERT INTO scan_results (
                        run_id, rank, symbol, name, exchange, metrics_json,
                        matched_rules_json, failed_rules_json, warnings_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run.run_id,
                            result.rank,
                            result.symbol,
                            result.name,
                            result.exchange,
                            json.dumps(result.metrics),
                            json.dumps(result.matched_rules),
                            json.dumps(result.failed_rules),
                            json.dumps(result.warnings),
                        )
                        for result in run.results
                    ],
                )
            if run.skipped:
                connection.executemany(
                    """
                    INSERT INTO scan_skipped_symbols (
                        run_id, symbol, name, reason, cached_rows, required_rows, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run.run_id,
                            item.symbol,
                            item.name,
                            item.reason,
                            item.cached_rows,
                            item.required_rows,
                            json.dumps(item.details),
                        )
                        for item in run.skipped
                    ],
                )

    def get_scan_run(self, run_id: str) -> ScanRun | None:
        with self._connect() as connection:
            run_row = connection.execute(
                "SELECT * FROM scan_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if run_row is None:
                return None
            result_rows = connection.execute(
                "SELECT * FROM scan_results WHERE run_id = ? ORDER BY rank",
                (run_id,),
            ).fetchall()
            skipped_rows = connection.execute(
                "SELECT * FROM scan_skipped_symbols WHERE run_id = ? ORDER BY symbol",
                (run_id,),
            ).fetchall()
        rules = ScannerRules(**json.loads(run_row["rules_json"]))
        return ScanRun(
            run_id=run_row["run_id"],
            universe_id=run_row["universe_id"],
            start_date=date.fromisoformat(run_row["start_date"]),
            end_date=date.fromisoformat(run_row["end_date"]),
            rules=rules,
            sort_key=run_row["sort_key"],
            sort_direction=SortDirection(run_row["sort_direction"]),
            result_limit=int(run_row["result_limit"]),
            status=ScanStatus(run_row["status"]),
            total_symbols=int(run_row["total_symbols"]),
            analyzed_symbols=int(run_row["analyzed_symbols"]),
            matched_symbols=int(run_row["matched_symbols"]),
            skipped_symbols=int(run_row["skipped_symbols"]),
            warnings=tuple(json.loads(run_row["warnings_json"])),
            created_at=datetime.fromisoformat(run_row["created_at"]),
            results=tuple(self._scan_result_from_row(row) for row in result_rows),
            skipped=tuple(self._skipped_symbol_from_row(row) for row in skipped_rows),
        )

    def list_scan_runs(self, limit: int = 20) -> tuple[ScanRun, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM scan_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(self._scan_run_summary_from_row(row) for row in rows)

    def list_batch_sync_runs(
        self, *, universe_id: str | None = None, limit: int = 20
    ) -> tuple[dict[str, object], ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if universe_id:
            clauses.append("universe_id = ?")
            parameters.append(universe_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM market_batch_sync_runs
                {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                parameters,
            ).fetchall()
        return tuple(dict(row) for row in rows)

    def list_sync_runs(
        self, *, run_id: str | None = None, limit: int = 100
    ) -> tuple[dict[str, object], ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if run_id:
            clauses.append("run_id = ?")
            parameters.append(run_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM market_sync_runs
                {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                parameters,
            ).fetchall()
        return tuple(dict(row) for row in rows)

    def save_multi_backtest_run(self, run: MultiBacktestRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO multi_backtest_runs (
                    run_id, scan_run_id, template_id, top_n, start_date, end_date,
                    parameters_json, initial_cash, commission, slippage, status,
                    requested_symbols, successful_symbols, failed_symbols,
                    aggregate_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.scan_run_id,
                    run.template_id,
                    run.top_n,
                    run.start_date.isoformat(),
                    run.end_date.isoformat(),
                    json.dumps(run.parameters),
                    run.initial_cash,
                    run.commission,
                    run.slippage,
                    run.status.value,
                    run.requested_symbols,
                    run.successful_symbols,
                    run.failed_symbols,
                    json.dumps(run.aggregate),
                    run.created_at.isoformat(),
                ),
            )
            if run.results:
                connection.executemany(
                    """
                    INSERT INTO multi_backtest_results (
                        run_id, rank, symbol, status, strategy_name, metrics_json,
                        warnings_json, error
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run.run_id,
                            result.rank,
                            result.symbol,
                            result.status.value,
                            result.strategy_name,
                            json.dumps(result.metrics),
                            json.dumps(result.warnings),
                            result.error,
                        )
                        for result in run.results
                    ],
                )

    def get_multi_backtest_run(self, run_id: str) -> MultiBacktestRun | None:
        with self._connect() as connection:
            run_row = connection.execute(
                "SELECT * FROM multi_backtest_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if run_row is None:
                return None
            result_rows = connection.execute(
                """
                SELECT * FROM multi_backtest_results
                WHERE run_id = ?
                ORDER BY rank
                """,
                (run_id,),
            ).fetchall()
        return self._multi_backtest_run_from_rows(run_row, result_rows)

    def list_multi_backtest_runs(self, limit: int = 20) -> tuple[MultiBacktestRun, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM multi_backtest_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(self._multi_backtest_run_from_rows(row, ()) for row in rows)

    def create_job(self, job: JobRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO job_runs (
                    job_id, kind, status, payload_json, processed, total, message,
                    result_type, result_id, error, created_at, started_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.kind.value,
                    job.status.value,
                    json.dumps(job.payload),
                    job.processed,
                    job.total,
                    job.message,
                    job.result_type,
                    job.result_id,
                    job.error,
                    job.created_at.isoformat(),
                    job.started_at.isoformat() if job.started_at else None,
                    job.finished_at.isoformat() if job.finished_at else None,
                ),
            )

    def get_job(self, job_id: str) -> JobRun | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM job_runs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return self._job_from_row(row) if row else None

    def list_jobs(self, *, limit: int = 50) -> tuple[JobRun, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM job_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(self._job_from_row(row) for row in rows)

    def claim_next_job(self) -> JobRun | None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM job_runs
                WHERE status = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (JobStatus.PENDING.value,),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                """
                UPDATE job_runs
                SET status = ?, started_at = ?, message = ?
                WHERE job_id = ? AND status = ?
                """,
                (
                    JobStatus.RUNNING.value,
                    now,
                    "Job is running.",
                    row["job_id"],
                    JobStatus.PENDING.value,
                ),
            )
        job = self.get_job(row["job_id"])
        return job

    def update_job(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        processed: int | None = None,
        total: int | None = None,
        message: str | None = None,
        result_type: str | None = None,
        result_id: str | None = None,
        error: str | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        assignments: list[str] = []
        values: list[object] = []
        mapping = {
            "status": status.value if status else None,
            "processed": processed,
            "total": total,
            "message": message,
            "result_type": result_type,
            "result_id": result_id,
            "error": error,
            "finished_at": finished_at.isoformat() if finished_at else None,
        }
        for key, value in mapping.items():
            if value is not None:
                assignments.append(f"{key} = ?")
                values.append(value)
        if not assignments:
            return
        values.append(job_id)
        with self._connect() as connection:
            connection.execute(
                f"UPDATE job_runs SET {', '.join(assignments)} WHERE job_id = ?",
                values,
            )

    def add_job_event(
        self,
        job_id: str,
        *,
        status: JobStatus,
        message: str,
        processed: int = 0,
        total: int = 0,
        details: dict[str, object] | None = None,
    ) -> None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(MAX(sequence), 0) + 1 AS sequence
                FROM job_events
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO job_events (
                    job_id, sequence, status, message, processed, total, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    int(row["sequence"]),
                    status.value,
                    message,
                    processed,
                    total,
                    json.dumps(details or {}),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def list_job_events(self, job_id: str) -> tuple[JobEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM job_events
                WHERE job_id = ?
                ORDER BY sequence
                """,
                (job_id,),
            ).fetchall()
        return tuple(self._job_event_from_row(row) for row in rows)

    def fail_interrupted_jobs(self) -> None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE job_runs
                SET status = ?, error = ?, message = ?, finished_at = ?
                WHERE status = ?
                """,
                (
                    JobStatus.FAILED.value,
                    "Worker restarted before the job completed.",
                    "Job failed because the worker restarted.",
                    now,
                    JobStatus.RUNNING.value,
                ),
            )

    def save_portfolio_run(self, run: PortfolioRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO portfolio_rebalance_runs (
                    run_id, status, selection_mode, universe_id, scanner_preset_id,
                    fixed_scan_run_id, top_n, frequency, start_date, end_date,
                    lookback_days, initial_cash, commission, slippage, benchmark_symbol,
                    scanner_rules_json, quality_gate_json, performance_json, benchmark_json,
                    aggregate_json, warnings_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.status.value,
                    run.selection_mode.value,
                    run.universe_id,
                    run.scanner_preset_id,
                    run.fixed_scan_run_id,
                    run.top_n,
                    run.frequency.value,
                    run.start_date.isoformat(),
                    run.end_date.isoformat(),
                    run.lookback_days,
                    run.initial_cash,
                    run.commission,
                    run.slippage,
                    run.benchmark_symbol,
                    json.dumps(run.scanner_rules),
                    json.dumps(run.quality_gate),
                    json.dumps(run.performance),
                    json.dumps(run.benchmark),
                    json.dumps(run.aggregate),
                    json.dumps(run.warnings),
                    run.created_at.isoformat(),
                ),
            )
            if run.equity_curve:
                connection.executemany(
                    """
                    INSERT INTO portfolio_equity_points (
                        run_id, trade_date, equity, cash, position_value, drawdown_pct
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run.run_id,
                            point.date.isoformat(),
                            point.equity,
                            point.cash,
                            point.position_value,
                            point.drawdown_pct,
                        )
                        for point in run.equity_curve
                    ],
                )
            if run.holdings:
                connection.executemany(
                    """
                    INSERT INTO portfolio_holdings (
                        run_id, trade_date, symbol, weight, shares, price, value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run.run_id,
                            item.date.isoformat(),
                            item.symbol,
                            item.weight,
                            item.shares,
                            item.price,
                            item.value,
                        )
                        for item in run.holdings
                    ],
                )
            if run.rebalance_events:
                connection.executemany(
                    """
                    INSERT INTO portfolio_rebalance_events (
                        run_id, trade_date, selected_symbols_json, excluded_symbols_json,
                        turnover_pct, traded_notional, cost, scan_run_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run.run_id,
                            item.date.isoformat(),
                            json.dumps(item.selected_symbols),
                            json.dumps(item.excluded_symbols),
                            item.turnover_pct,
                            item.traded_notional,
                            item.cost,
                            item.scan_run_id,
                        )
                        for item in run.rebalance_events
                    ],
                )
            if run.skipped_periods:
                connection.executemany(
                    """
                    INSERT INTO portfolio_skipped_periods (
                        run_id, trade_date, reason, details_json
                    ) VALUES (?, ?, ?, ?)
                    """,
                    [
                        (
                            run.run_id,
                            item.date.isoformat(),
                            item.reason,
                            json.dumps(item.details),
                        )
                        for item in run.skipped_periods
                    ],
                )

    def get_portfolio_run(self, run_id: str) -> PortfolioRun | None:
        with self._connect() as connection:
            run_row = connection.execute(
                "SELECT * FROM portfolio_rebalance_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if run_row is None:
                return None
            equity_rows = connection.execute(
                "SELECT * FROM portfolio_equity_points WHERE run_id = ? ORDER BY trade_date",
                (run_id,),
            ).fetchall()
            holding_rows = connection.execute(
                "SELECT * FROM portfolio_holdings WHERE run_id = ? ORDER BY trade_date, symbol",
                (run_id,),
            ).fetchall()
            event_rows = connection.execute(
                "SELECT * FROM portfolio_rebalance_events WHERE run_id = ? ORDER BY trade_date",
                (run_id,),
            ).fetchall()
            skipped_rows = connection.execute(
                "SELECT * FROM portfolio_skipped_periods WHERE run_id = ? ORDER BY trade_date",
                (run_id,),
            ).fetchall()
        return self._portfolio_run_from_rows(
            run_row, equity_rows, holding_rows, event_rows, skipped_rows
        )

    def list_portfolio_runs(self, limit: int = 20) -> tuple[PortfolioRun, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM portfolio_rebalance_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(self._portfolio_run_from_rows(row, (), (), (), ()) for row in rows)

    def upsert_portfolio_preset(self, preset: PortfolioPreset) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO portfolio_presets (
                    preset_id, name, description, config_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(preset_id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    config_json = excluded.config_json
                """,
                (
                    preset.preset_id,
                    preset.name,
                    preset.description,
                    json.dumps(preset.config),
                    preset.created_at.isoformat(),
                ),
            )

    def list_portfolio_presets(self) -> tuple[PortfolioPreset, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM portfolio_presets ORDER BY preset_id"
            ).fetchall()
        return tuple(self._portfolio_preset_from_row(row) for row in rows)

    def get_portfolio_preset(self, preset_id: str) -> PortfolioPreset | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM portfolio_presets WHERE preset_id = ?",
                (preset_id,),
            ).fetchone()
        return self._portfolio_preset_from_row(row) if row else None

    def upsert_research_preset(self, preset: ResearchPreset) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO research_presets (
                    preset_id, name, description, config_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(preset_id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    config_json = excluded.config_json
                """,
                (
                    preset.preset_id,
                    preset.name,
                    preset.description,
                    json.dumps(preset.config),
                    preset.created_at.isoformat(),
                ),
            )

    def list_research_presets(self) -> tuple[ResearchPreset, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM research_presets ORDER BY preset_id"
            ).fetchall()
        return tuple(self._research_preset_from_row(row) for row in rows)

    def get_research_preset(self, preset_id: str) -> ResearchPreset | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM research_presets WHERE preset_id = ?",
                (preset_id,),
            ).fetchone()
        return self._research_preset_from_row(row) if row else None

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

    @staticmethod
    def _universe_summary_from_row(row: sqlite3.Row) -> UniverseSummary:
        return UniverseSummary(
            universe_id=row["universe_id"],
            name=row["name"],
            description=row["description"],
            market=row["market"],
            asset_type=row["asset_type"],
            source=row["source"],
            source_url=row["source_url"],
            member_count=int(row["member_count"]),
            refreshed_at=datetime.fromisoformat(row["refreshed_at"]),
        )

    @staticmethod
    def _universe_member_from_row(row: sqlite3.Row) -> UniverseMember:
        return UniverseMember(
            symbol=row["symbol"],
            name=row["name"],
            exchange=row["exchange"],
            asset_type=row["asset_type"],
            currency=row["currency"],
            provider_symbol=row["provider_symbol"],
            is_active=bool(row["is_active"]),
            metadata=json.loads(row["metadata_json"]),
        )

    @staticmethod
    def _scan_result_from_row(row: sqlite3.Row) -> ScanResult:
        return ScanResult(
            rank=int(row["rank"]),
            symbol=row["symbol"],
            name=row["name"],
            exchange=row["exchange"],
            metrics=json.loads(row["metrics_json"]),
            matched_rules=tuple(json.loads(row["matched_rules_json"])),
            failed_rules=tuple(json.loads(row["failed_rules_json"])),
            warnings=tuple(json.loads(row["warnings_json"])),
        )

    @staticmethod
    def _skipped_symbol_from_row(row: sqlite3.Row) -> SkippedSymbol:
        return SkippedSymbol(
            symbol=row["symbol"],
            name=row["name"],
            reason=row["reason"],
            cached_rows=int(row["cached_rows"]),
            required_rows=int(row["required_rows"]),
            details=json.loads(row["details_json"]),
        )

    @staticmethod
    def _scan_run_summary_from_row(row: sqlite3.Row) -> ScanRun:
        return ScanRun(
            run_id=row["run_id"],
            universe_id=row["universe_id"],
            start_date=date.fromisoformat(row["start_date"]),
            end_date=date.fromisoformat(row["end_date"]),
            rules=ScannerRules(**json.loads(row["rules_json"])),
            sort_key=row["sort_key"],
            sort_direction=SortDirection(row["sort_direction"]),
            result_limit=int(row["result_limit"]),
            status=ScanStatus(row["status"]),
            total_symbols=int(row["total_symbols"]),
            analyzed_symbols=int(row["analyzed_symbols"]),
            matched_symbols=int(row["matched_symbols"]),
            skipped_symbols=int(row["skipped_symbols"]),
            warnings=tuple(json.loads(row["warnings_json"])),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @classmethod
    def _multi_backtest_run_from_rows(
        cls,
        row: sqlite3.Row,
        result_rows: Iterable[sqlite3.Row],
    ) -> MultiBacktestRun:
        return MultiBacktestRun(
            run_id=row["run_id"],
            scan_run_id=row["scan_run_id"],
            template_id=row["template_id"],
            top_n=int(row["top_n"]),
            start_date=date.fromisoformat(row["start_date"]),
            end_date=date.fromisoformat(row["end_date"]),
            parameters=json.loads(row["parameters_json"]),
            initial_cash=float(row["initial_cash"]),
            commission=float(row["commission"]),
            slippage=float(row["slippage"]),
            status=MultiBacktestStatus(row["status"]),
            requested_symbols=int(row["requested_symbols"]),
            successful_symbols=int(row["successful_symbols"]),
            failed_symbols=int(row["failed_symbols"]),
            aggregate=json.loads(row["aggregate_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            results=tuple(cls._multi_backtest_result_from_row(item) for item in result_rows),
        )

    @staticmethod
    def _multi_backtest_result_from_row(row: sqlite3.Row) -> MultiBacktestResult:
        return MultiBacktestResult(
            rank=int(row["rank"]),
            symbol=row["symbol"],
            status=MultiBacktestStatus(row["status"]),
            strategy_name=row["strategy_name"],
            metrics=json.loads(row["metrics_json"]),
            warnings=tuple(json.loads(row["warnings_json"])),
            error=row["error"],
        )

    @staticmethod
    def _job_from_row(row: sqlite3.Row) -> JobRun:
        return JobRun(
            job_id=row["job_id"],
            kind=JobKind(row["kind"]),
            status=JobStatus(row["status"]),
            payload=json.loads(row["payload_json"]),
            processed=int(row["processed"]),
            total=int(row["total"]),
            message=row["message"],
            result_type=row["result_type"],
            result_id=row["result_id"],
            error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
        )

    @staticmethod
    def _job_event_from_row(row: sqlite3.Row) -> JobEvent:
        return JobEvent(
            event_id=int(row["event_id"]),
            job_id=row["job_id"],
            sequence=int(row["sequence"]),
            status=JobStatus(row["status"]),
            message=row["message"],
            processed=int(row["processed"]),
            total=int(row["total"]),
            details=json.loads(row["details_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @classmethod
    def _portfolio_run_from_rows(
        cls,
        row: sqlite3.Row,
        equity_rows: Iterable[sqlite3.Row],
        holding_rows: Iterable[sqlite3.Row],
        event_rows: Iterable[sqlite3.Row],
        skipped_rows: Iterable[sqlite3.Row],
    ) -> PortfolioRun:
        return PortfolioRun(
            run_id=row["run_id"],
            status=PortfolioRunStatus(row["status"]),
            selection_mode=PortfolioSelectionMode(row["selection_mode"]),
            universe_id=row["universe_id"],
            scanner_preset_id=row["scanner_preset_id"],
            fixed_scan_run_id=row["fixed_scan_run_id"],
            top_n=int(row["top_n"]),
            frequency=RebalanceFrequency(row["frequency"]),
            start_date=date.fromisoformat(row["start_date"]),
            end_date=date.fromisoformat(row["end_date"]),
            lookback_days=int(row["lookback_days"]),
            initial_cash=float(row["initial_cash"]),
            commission=float(row["commission"]),
            slippage=float(row["slippage"]),
            benchmark_symbol=row["benchmark_symbol"],
            scanner_rules=json.loads(row["scanner_rules_json"]),
            quality_gate=json.loads(row["quality_gate_json"]),
            performance=json.loads(row["performance_json"]),
            benchmark=json.loads(row["benchmark_json"]),
            aggregate=json.loads(row["aggregate_json"]),
            warnings=tuple(json.loads(row["warnings_json"])),
            created_at=datetime.fromisoformat(row["created_at"]),
            equity_curve=tuple(cls._portfolio_equity_from_row(item) for item in equity_rows),
            holdings=tuple(cls._portfolio_holding_from_row(item) for item in holding_rows),
            rebalance_events=tuple(cls._rebalance_event_from_row(item) for item in event_rows),
            skipped_periods=tuple(cls._skipped_period_from_row(item) for item in skipped_rows),
        )

    @staticmethod
    def _portfolio_equity_from_row(row: sqlite3.Row) -> PortfolioEquityPoint:
        return PortfolioEquityPoint(
            date=date.fromisoformat(row["trade_date"]),
            equity=float(row["equity"]),
            cash=float(row["cash"]),
            position_value=float(row["position_value"]),
            drawdown_pct=float(row["drawdown_pct"]),
        )

    @staticmethod
    def _portfolio_holding_from_row(row: sqlite3.Row) -> PortfolioHolding:
        return PortfolioHolding(
            date=date.fromisoformat(row["trade_date"]),
            symbol=row["symbol"],
            weight=float(row["weight"]),
            shares=float(row["shares"]),
            price=float(row["price"]),
            value=float(row["value"]),
        )

    @staticmethod
    def _rebalance_event_from_row(row: sqlite3.Row) -> RebalanceEvent:
        return RebalanceEvent(
            date=date.fromisoformat(row["trade_date"]),
            selected_symbols=tuple(json.loads(row["selected_symbols_json"])),
            excluded_symbols=tuple(json.loads(row["excluded_symbols_json"])),
            turnover_pct=float(row["turnover_pct"]),
            traded_notional=float(row["traded_notional"]),
            cost=float(row["cost"]),
            scan_run_id=row["scan_run_id"],
        )

    @staticmethod
    def _skipped_period_from_row(row: sqlite3.Row) -> SkippedPeriod:
        return SkippedPeriod(
            date=date.fromisoformat(row["trade_date"]),
            reason=row["reason"],
            details=json.loads(row["details_json"]),
        )

    @staticmethod
    def _portfolio_preset_from_row(row: sqlite3.Row) -> PortfolioPreset:
        return PortfolioPreset(
            preset_id=row["preset_id"],
            name=row["name"],
            description=row["description"],
            config=json.loads(row["config_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _research_preset_from_row(row: sqlite3.Row) -> ResearchPreset:
        return ResearchPreset(
            preset_id=row["preset_id"],
            name=row["name"],
            description=row["description"],
            config=json.loads(row["config_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
