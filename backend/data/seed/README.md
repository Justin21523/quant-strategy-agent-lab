# Bundled synthetic market-data fixtures

Phase 1 ships deterministic synthetic daily OHLCV for `AAPL`, `SPY`, `QQQ`, and a 20-stock synthetic sample universe so the application can run and be tested without network access.

- Date range: `2023-01-03` through `2025-12-31`.
- Weekdays are generated; exchange holidays are not modeled.
- `adjusted_close` includes a deterministic synthetic adjustment factor.
- These rows are **not observed market prices** and are always exposed by the API with `contains_fixture_data: true` plus a data-quality warning.
- Use `POST /api/v1/market/sync` with `provider: "yfinance"` when network access is available to cache public historical data for personal research.

Regenerate the fixtures with `python scripts/generate_demo_market_data.py`.
