from __future__ import annotations

from typing import Any


class MarketDataError(Exception):
    code = "market_data_error"
    status_code = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidDateRangeError(MarketDataError):
    code = "invalid_date_range"
    status_code = 422


class SymbolNotFoundError(MarketDataError):
    code = "symbol_not_found"
    status_code = 404


class MarketDataNotFoundError(MarketDataError):
    code = "market_data_not_found"
    status_code = 404


class MarketDataLimitError(MarketDataError):
    code = "market_data_limit"
    status_code = 413


class UnsupportedProviderError(MarketDataError):
    code = "unsupported_provider"
    status_code = 422


class ProviderUnavailableError(MarketDataError):
    code = "provider_unavailable"
    status_code = 503


class ProviderNotImplementedError(MarketDataError):
    code = "provider_not_implemented"
    status_code = 501


class ProviderDataError(MarketDataError):
    code = "provider_data_error"
    status_code = 502


class StrategyTemplateNotFoundError(MarketDataError):
    code = "strategy_template_not_found"
    status_code = 404


class StrategyTemplateValidationError(MarketDataError):
    code = "strategy_template_validation_error"
    status_code = 422


class StrategyDslValidationError(MarketDataError):
    code = "strategy_dsl_validation_error"
    status_code = 422
