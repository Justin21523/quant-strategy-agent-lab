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
        "symbol": "ALFA",
        "name": "Alfa Systems Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 42.0,
        "annual_drift": 0.22,
        "base_volume": 8_200_000,
        "phase": 0.2,
    },
    {
        "symbol": "BRAV",
        "name": "Bravo Industrials Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NYSE",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 58.0,
        "annual_drift": 0.08,
        "base_volume": 4_600_000,
        "phase": 0.9,
    },
    {
        "symbol": "CHAR",
        "name": "Charlie Health Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 24.0,
        "annual_drift": -0.03,
        "base_volume": 6_100_000,
        "phase": 1.3,
    },
    {
        "symbol": "DELT",
        "name": "Delta Robotics Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 86.0,
        "annual_drift": 0.28,
        "base_volume": 9_500_000,
        "phase": 1.7,
    },
    {
        "symbol": "ECHO",
        "name": "Echo Retail Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NYSE",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 31.0,
        "annual_drift": 0.02,
        "base_volume": 3_800_000,
        "phase": 2.1,
    },
    {
        "symbol": "FOXT",
        "name": "Foxtrot Software Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 115.0,
        "annual_drift": 0.18,
        "base_volume": 11_200_000,
        "phase": 2.4,
    },
    {
        "symbol": "GOLF",
        "name": "Golf Energy Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NYSE",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 64.0,
        "annual_drift": 0.05,
        "base_volume": 7_400_000,
        "phase": 2.9,
    },
    {
        "symbol": "HOTL",
        "name": "Hotel Cloud Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 18.0,
        "annual_drift": 0.34,
        "base_volume": 12_800_000,
        "phase": 3.2,
    },
    {
        "symbol": "INDI",
        "name": "India Payments Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NYSE",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 73.0,
        "annual_drift": 0.12,
        "base_volume": 5_300_000,
        "phase": 3.6,
    },
    {
        "symbol": "JULI",
        "name": "Juliet Biotech Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 39.0,
        "annual_drift": -0.08,
        "base_volume": 4_100_000,
        "phase": 4.0,
    },
    {
        "symbol": "KILO",
        "name": "Kilo Semiconductor Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 97.0,
        "annual_drift": 0.31,
        "base_volume": 10_700_000,
        "phase": 4.5,
    },
    {
        "symbol": "LIMA",
        "name": "Lima Logistics Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NYSE",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 52.0,
        "annual_drift": 0.09,
        "base_volume": 6_900_000,
        "phase": 4.8,
    },
    {
        "symbol": "MIKE",
        "name": "Mike Materials Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NYSE",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 44.0,
        "annual_drift": 0.01,
        "base_volume": 3_600_000,
        "phase": 5.1,
    },
    {
        "symbol": "NOVA",
        "name": "Nova Networks Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 29.0,
        "annual_drift": 0.24,
        "base_volume": 9_900_000,
        "phase": 5.5,
    },
    {
        "symbol": "OSCR",
        "name": "Oscar Aerospace Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NYSE",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 121.0,
        "annual_drift": 0.06,
        "base_volume": 4_800_000,
        "phase": 5.9,
    },
    {
        "symbol": "PAPA",
        "name": "Papa Devices Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 15.0,
        "annual_drift": 0.42,
        "base_volume": 14_400_000,
        "phase": 6.3,
    },
    {
        "symbol": "QUEB",
        "name": "Quebec Finance Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NYSE",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 67.0,
        "annual_drift": 0.07,
        "base_volume": 5_800_000,
        "phase": 6.7,
        "skip_every": 17,
    },
    {
        "symbol": "ROMO",
        "name": "Romeo Platforms Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 22.0,
        "annual_drift": 0.15,
        "base_volume": 7_700_000,
        "phase": 7.1,
        "start_offset": 620,
    },
    {
        "symbol": "SIER",
        "name": "Sierra Consumer Synthetic Common Stock",
        "market": "US",
        "asset_type": "equity",
        "exchange": "NYSE",
        "currency": "USD",
        "timezone": "America/New_York",
        "base_price": 48.0,
        "annual_drift": 0.04,
        "base_volume": 3_200_000,
        "phase": 7.6,
        "end_offset": 130,
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

    start_offset = int(config.get("start_offset", 0))
    end_offset = int(config.get("end_offset", 0))
    skip_every = int(config.get("skip_every", 0))
    selected_dates = dates[start_offset : len(dates) - end_offset if end_offset else len(dates)]
    if skip_every > 0:
        selected_dates = [
            trade_date
            for index, trade_date in enumerate(selected_dates)
            if (index + 1) % skip_every
        ]

    base_price = float(config["base_price"])
    annual_drift = float(config["annual_drift"])
    base_volume = int(config["base_volume"])
    phase = float(config["phase"])
    rows: list[dict[str, object]] = []
    previous_close = base_price

    for index, trade_date in enumerate(selected_dates):
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
        adjustment_factor = 0.975 + 0.025 * index / max(1, len(selected_dates) - 1)

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
            "`QQQ`, and a 20-stock synthetic sample universe so the application can "
            "run and be tested without network access."
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
