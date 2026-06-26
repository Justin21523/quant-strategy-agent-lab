PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS symbols (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    market TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    exchange TEXT NOT NULL,
    currency TEXT NOT NULL,
    timezone TEXT NOT NULL,
    default_provider TEXT NOT NULL,
    supported_providers_json TEXT NOT NULL,
    is_demo INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ohlcv_bars (
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    adjusted_close REAL NOT NULL,
    volume INTEGER NOT NULL,
    provider TEXT NOT NULL,
    dataset TEXT NOT NULL,
    source_timezone TEXT NOT NULL,
    currency TEXT NOT NULL,
    is_adjusted INTEGER NOT NULL DEFAULT 0,
    is_fixture_data INTEGER NOT NULL DEFAULT 0,
    retrieved_at TEXT NOT NULL,
    PRIMARY KEY (symbol, interval, trade_date),
    FOREIGN KEY (symbol) REFERENCES symbols(symbol) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_interval_date
ON ohlcv_bars(symbol, interval, trade_date);

CREATE TABLE IF NOT EXISTS market_sync_runs (
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    requested_provider TEXT NOT NULL,
    provider_used TEXT,
    requested_start TEXT,
    requested_end TEXT,
    effective_start TEXT,
    effective_end TEXT,
    status TEXT NOT NULL,
    bars_received INTEGER NOT NULL DEFAULT 0,
    bars_stored INTEGER NOT NULL DEFAULT 0,
    fallback_used INTEGER NOT NULL DEFAULT 0,
    is_fixture_data INTEGER NOT NULL DEFAULT 0,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    attempts_json TEXT NOT NULL DEFAULT '[]',
    error TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, symbol),
    FOREIGN KEY (symbol) REFERENCES symbols(symbol) ON DELETE CASCADE
);
