from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any, TypeAlias

StrategyParameterValue: TypeAlias = int | float | str | bool


class StrategyTemplateCategory(StrEnum):
    BASELINE = "baseline"
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"


class StrategyParameterKind(StrEnum):
    INTEGER = "integer"
    FLOAT = "float"
    SELECT = "select"
    BOOLEAN = "boolean"


class StrategyIssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class StrategyParameterOption:
    value: StrategyParameterValue
    label: str


@dataclass(frozen=True, slots=True)
class StrategyParameterDefinition:
    key: str
    label: str
    kind: StrategyParameterKind
    default: StrategyParameterValue
    description: str
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    unit: str | None = None
    options: tuple[StrategyParameterOption, ...] = ()


@dataclass(frozen=True, slots=True)
class StrategyTemplate:
    id: str
    name: str
    description: str
    category: StrategyTemplateCategory
    summary: str
    parameters: tuple[StrategyParameterDefinition, ...]
    tags: tuple[str, ...]
    indicator_kinds: tuple[str, ...]
    risk_notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StrategyRenderContext:
    symbol: str = "AAPL"
    market: str = "US"
    timeframe: str = "1d"
    start: date | None = None
    end: date | None = None
    initial_cash: float = 100_000.0
    commission: float = 0.001
    slippage: float = 0.0005


@dataclass(frozen=True, slots=True)
class StrategyValidationIssue:
    code: str
    severity: StrategyIssueSeverity
    message: str
    path: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StrategyValidationReport:
    is_valid: bool
    issues: tuple[StrategyValidationIssue, ...]

    def __iter__(self):
        return iter(self.issues)

    def __len__(self) -> int:
        return len(self.issues)


@dataclass(frozen=True, slots=True)
class StrategyRenderResult:
    template: StrategyTemplate
    parameters: dict[str, StrategyParameterValue]
    strategy_json: dict[str, Any]
    validation: StrategyValidationReport
    required_indicators: tuple[str, ...]

    @property
    def validation_issues(self) -> tuple[StrategyValidationIssue, ...]:
        return self.validation.issues
