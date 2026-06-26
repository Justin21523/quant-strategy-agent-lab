#!/usr/bin/env python3
"""Generate deterministic synthetic OHLCV fixtures for offline development.

The generated files are intentionally synthetic. They exist so Phase 1 can be
run, tested, and demonstrated without network access. They must never be
presented as observed market prices.
"""

from __future__ import annotations

import csv
import math
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "backend" / "data" / "seed"
START = date(2023, 1, 3)
END = date(2025, 12, 31)

SYMBOLS: tuple[dict[str, object], ...] = (
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 132.0,
        "annual_drift": 0.16,
        "base_volume": 72_000_000,
        "phase": 0.7,
    },
    {
        "symbol": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "market": "US",
        "asset_type": "etf",
        "exchange": "NYSE Arca",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 382.0,
        "annual_drift": 0.11,
        "base_volume": 81_000_000,
        "phase": 1.9,
    },
    {
        "symbol": "QQQ",
        "name": "Invesco QQQ Trust",
        "market": "US",
        "asset_type": "etf",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 268.0,
        "annual_drift": 0.14,
        "base_volume": 52_000_000,
        "phase": 2.8,
    },
)

BAR_FIELDS = ("date", "open", "high", "low", "close", "adjusted_close", "volume")
MANIFEST_FIELDS = (
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
    "source_note",
)


def weekdays(start: date, end: date) -> list[date]:
    """Return weekdays only; exchange holidays are deliberately not modeled."""

    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def generate_rows(config: dict[str, object], dates: list[date]) -> list[dict[str, object]]:
    """Create a smooth but non-trivial deterministic OHLCV series."""

    base_price = float(config["base_price"])
    annual_drift = float(config["annual_drift"])
    base_volume = int(config["base_volume"])
    phase = float(config["phase"])
    rows: list[dict[str, object]] = []
    previous_close = base_price

    for index, trade_date in enumerate(dates):
        trend = math.exp(annual_drift * index / 252)
        cycle = 0.026 * math.sin(index / 18 + phase) + 0.014 * math.cos(index / 47 + phase)
        close = base_price * trend * (1 + cycle)
        overnight = 0.0045 * math.sin(index / 7 + phase) + 0.0015 * math.cos(index / 3.7)
        open_price = previous_close * (1 + overnight)
        spread = 0.006 + 0.003 * abs(math.sin(index / 11 + phase))
        high = max(open_price, close) * (1 + spread)
        low = min(open_price, close) * (1 - spread * 0.92)
        volume_factor = 1 + 0.24 * math.sin(index / 9 + phase) + 0.11 * math.cos(index / 23)
        volume = max(1_000_000, int(base_volume * volume_factor))
        adjustment_factor = 0.975 + 0.025 * index / max(1, len(dates) - 1)

        rows.append(
            {
                "date": trade_date.isoformat(),
                "open": round(open_price, 4),
                "high": round(high, 4),
                "low": round(low, 4),
                "close": round(close, 4),
                "adjusted_close": round(close * adjustment_factor, 4),
                "volume": volume,
            }
        )
        previous_close = close
    return rows


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    dates = weekdays(START, END)
    manifest_rows: list[dict[str, object]] = []

    for config in SYMBOLS:
        symbol = str(config["symbol"])
        filename = f"{symbol}.csv"
        write_csv(OUTPUT / filename, BAR_FIELDS, generate_rows(config, dates))
        manifest_rows.append(
            {
                "symbol": symbol,
                "name": config["name"],
                "market": config["market"],
                "asset_type": config["asset_type"],
                "exchange": config["exchange"],
                "currency": config["currency"],
                "timezone": config["timezone"],
                "filename": filename,
                "is_fixture_data": "true",
                "is_adjusted": "false",
                "dataset": "qsal-synthetic-offline-v1",
                "source_note": (
                    "Deterministic synthetic weekday OHLCV generated locally; "
                    "not observed market data."
                ),
            }
        )

    write_csv(OUTPUT / "symbols.csv", MANIFEST_FIELDS, manifest_rows)
    readme_lines = [
        "# Bundled synthetic market-data fixtures",
        "",
        (
            "Phase 1 ships deterministic synthetic daily OHLCV for `AAPL`, `SPY`, "
            "and `QQQ` so the application can run and be tested without network access."
        ),
        "",
        f"- Date range: `{START.isoformat()}` through `{END.isoformat()}`.",
        "- Weekdays are generated; exchange holidays are not modeled.",
        "- `adjusted_close` includes a deterministic synthetic adjustment factor.",
        (
            "- These rows are **not observed market prices** and are always exposed by "
            "the API with `contains_fixture_data: true` plus a data-quality warning."
        ),
        (
            '- Use `POST /api/v1/market/sync` with `provider: "yfinance"` when network '
            "access is available to cache public historical data for personal research."
        ),
        "",
        "Regenerate the fixtures with `python scripts/generate_demo_market_data.py`.",
        "",
    ]
    readme = "\n".join(readme_lines)
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8")
    print(f"Generated {len(dates)} rows for {len(SYMBOLS)} symbols in {OUTPUT}")


if __name__ == "__main__":
    main()
