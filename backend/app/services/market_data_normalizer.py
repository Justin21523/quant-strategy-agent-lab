from __future__ import annotations

import math
from datetime import UTC, date, datetime

from app.domain.errors import ProviderDataError
from app.domain.market import (
    DataQualityWarning,
    MarketBar,
    NormalizationResult,
    ProviderFetchResult,
    WarningSeverity,
)


class MarketDataNormalizer:
    """Validate, sort, de-duplicate, and enrich provider rows before persistence."""

    def normalize(
        self,
        result: ProviderFetchResult,
        *,
        start: date | None = None,
        end: date | None = None,
        retrieved_at: datetime | None = None,
    ) -> NormalizationResult:
        timestamp = retrieved_at or datetime.now(UTC)
        warnings: list[DataQualityWarning] = []
        by_date = {}
        duplicate_count = 0
        invalid_count = 0

        for raw in result.bars:
            if start and raw.trade_date < start:
                continue
            if end and raw.trade_date > end:
                continue
            values = (raw.open, raw.high, raw.low, raw.close, raw.adjusted_close)
            if any(value is None or not math.isfinite(float(value)) for value in values):
                invalid_count += 1
                continue
            open_price, high, low, close, adjusted_close = (float(value) for value in values)
            volume_value = 0 if raw.volume is None else float(raw.volume)
            if (
                min(open_price, high, low, close, adjusted_close) <= 0
                or high < max(open_price, low, close)
                or low > min(open_price, high, close)
                or not math.isfinite(volume_value)
                or volume_value < 0
            ):
                invalid_count += 1
                continue
            if raw.trade_date in by_date:
                duplicate_count += 1
            by_date[raw.trade_date] = MarketBar(
                symbol=result.symbol.symbol,
                interval="1d",
                trade_date=raw.trade_date,
                open=open_price,
                high=high,
                low=low,
                close=close,
                adjusted_close=adjusted_close,
                volume=int(volume_value),
                provider=result.provider.value,
                dataset=result.dataset,
                source_timezone=result.symbol.timezone,
                currency=result.symbol.currency,
                is_adjusted=result.is_adjusted,
                is_fixture_data=result.is_fixture_data,
                retrieved_at=timestamp,
            )

        if duplicate_count:
            warnings.append(
                DataQualityWarning(
                    code="duplicate_dates_removed",
                    severity=WarningSeverity.WARNING,
                    message="Duplicate trading dates were de-duplicated; the last row was kept.",
                    affected_rows=duplicate_count,
                )
            )
        if invalid_count:
            warnings.append(
                DataQualityWarning(
                    code="invalid_rows_removed",
                    severity=WarningSeverity.WARNING,
                    message="Rows with invalid OHLCV values were excluded.",
                    affected_rows=invalid_count,
                )
            )
        for message in result.warnings:
            warnings.append(
                DataQualityWarning(
                    code="provider_notice",
                    severity=WarningSeverity.INFO,
                    message=message,
                )
            )

        bars = tuple(by_date[key] for key in sorted(by_date))
        if not bars:
            raise ProviderDataError(
                "No valid OHLCV rows remained after normalization.",
                details={"symbol": result.symbol.symbol, "provider": result.provider.value},
            )
        return NormalizationResult(bars=bars, warnings=tuple(warnings))
