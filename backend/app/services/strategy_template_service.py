from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.domain.errors import StrategyTemplateNotFoundError, StrategyTemplateValidationError
from app.domain.strategy import (
    StrategyIssueSeverity,
    StrategyParameterDefinition,
    StrategyParameterKind,
    StrategyParameterOption,
    StrategyParameterValue,
    StrategyRenderContext,
    StrategyRenderResult,
    StrategyTemplate,
    StrategyTemplateCategory,
    StrategyValidationIssue,
    StrategyValidationReport,
)


class StrategyTemplateService:
    """Render safe strategy templates into deterministic Strategy JSON DSL."""

    dsl_version = "1.0"

    def __init__(self) -> None:
        self._templates = {template.id: template for template in _build_templates()}

    def list_templates(self) -> tuple[StrategyTemplate, ...]:
        return tuple(sorted(self._templates.values(), key=lambda item: item.id))

    def get_template(self, template_id: str) -> StrategyTemplate:
        normalized = _normalize_template_id(template_id)
        try:
            return self._templates[normalized]
        except KeyError as exc:
            raise StrategyTemplateNotFoundError(
                f"Unsupported strategy template: {template_id}",
                details={"template_id": template_id},
            ) from exc

    def render_template(
        self,
        template_id: str,
        *,
        parameters: dict[str, Any] | None = None,
        context: StrategyRenderContext | None = None,
    ) -> StrategyRenderResult:
        template = self.get_template(template_id)
        normalized_parameters = self._normalize_parameters(template, parameters or {})
        ctx = context or StrategyRenderContext()
        strategy = self._render_strategy(template, normalized_parameters, ctx)
        validation = self.validate_strategy(strategy)
        return StrategyRenderResult(
            template=template,
            parameters=normalized_parameters,
            strategy_json=strategy,
            validation=validation,
            required_indicators=tuple(indicator["id"] for indicator in strategy["indicators"]),
        )

    def validate_strategy(self, strategy: dict[str, Any]) -> StrategyValidationReport:
        issues = list(self._validate_strategy(strategy))
        return StrategyValidationReport(
            is_valid=not any(issue.severity is StrategyIssueSeverity.ERROR for issue in issues),
            issues=tuple(issues),
        )

    def _normalize_parameters(
        self,
        template: StrategyTemplate,
        provided: dict[str, Any],
    ) -> dict[str, StrategyParameterValue]:
        definitions = {definition.key: definition for definition in template.parameters}
        unknown = sorted(set(provided) - set(definitions))
        if unknown:
            raise StrategyTemplateValidationError(
                "Request contains parameters that are not defined by this template.",
                details={"template_id": template.id, "unknown_parameters": unknown},
            )

        normalized: dict[str, StrategyParameterValue] = {}
        for key, definition in definitions.items():
            normalized[key] = self._coerce_parameter(
                definition, provided.get(key, definition.default)
            )
        self._validate_cross_parameter_constraints(template, normalized)
        return normalized

    def _coerce_parameter(
        self,
        definition: StrategyParameterDefinition,
        value: Any,
    ) -> StrategyParameterValue:
        try:
            if definition.kind is StrategyParameterKind.INTEGER:
                if isinstance(value, bool):
                    raise ValueError
                coerced: StrategyParameterValue = int(value)
                if float(coerced) != float(value):
                    raise ValueError
            elif definition.kind is StrategyParameterKind.FLOAT:
                if isinstance(value, bool):
                    raise ValueError
                coerced = float(value)
            elif definition.kind is StrategyParameterKind.SELECT:
                coerced = str(value)
            else:  # pragma: no cover
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise StrategyTemplateValidationError(
                f"Parameter '{definition.key}' has an invalid value.",
                details={"parameter": definition.key, "value": value},
            ) from exc

        if definition.minimum is not None and float(coerced) < definition.minimum:
            raise StrategyTemplateValidationError(
                f"Parameter '{definition.key}' is below the allowed minimum.",
                details={
                    "parameter": definition.key,
                    "minimum": definition.minimum,
                    "value": coerced,
                },
            )
        if definition.maximum is not None and float(coerced) > definition.maximum:
            raise StrategyTemplateValidationError(
                f"Parameter '{definition.key}' is above the allowed maximum.",
                details={
                    "parameter": definition.key,
                    "maximum": definition.maximum,
                    "value": coerced,
                },
            )
        if definition.kind is StrategyParameterKind.SELECT:
            allowed = {str(option.value) for option in definition.options}
            if str(coerced) not in allowed:
                raise StrategyTemplateValidationError(
                    f"Parameter '{definition.key}' is not one of the allowed choices.",
                    details={
                        "parameter": definition.key,
                        "allowed": sorted(allowed),
                        "value": coerced,
                    },
                )
        return coerced

    def _validate_cross_parameter_constraints(
        self,
        template: StrategyTemplate,
        parameters: dict[str, StrategyParameterValue],
    ) -> None:
        if template.id in {"ma_crossover", "ma_crossover_rsi", "macd_trend_following"}:
            fast = int(parameters["fast_window"])
            slow = int(parameters["slow_window"])
            if fast >= slow:
                raise StrategyTemplateValidationError(
                    "Fast window must be smaller than slow window.",
                    details={"fast_window": fast, "slow_window": slow},
                )
        if template.id == "rsi_mean_reversion":
            entry = float(parameters["entry_below"])
            exit_above = float(parameters["exit_above"])
            if entry >= exit_above:
                raise StrategyTemplateValidationError(
                    "RSI entry threshold must be lower than the exit threshold.",
                    details={"entry_below": entry, "exit_above": exit_above},
                )
        if template.id == "ma_crossover_rsi":
            entry_max = float(parameters["rsi_entry_max"])
            exit_min = float(parameters["rsi_exit_min"])
            if entry_max >= exit_min:
                raise StrategyTemplateValidationError(
                    "RSI entry maximum must be lower than RSI exit minimum.",
                    details={"rsi_entry_max": entry_max, "rsi_exit_min": exit_min},
                )

    def _render_strategy(
        self,
        template: StrategyTemplate,
        parameters: dict[str, StrategyParameterValue],
        context: StrategyRenderContext,
    ) -> dict[str, Any]:
        if template.id == "buy_and_hold":
            indicators: list[dict[str, Any]] = []
            entry = _rule("AND", [{"type": "ENTER_ON_FIRST_BAR"}])
            exit_rules = _rule("OR", [{"type": "EXIT_ON_LAST_BAR"}])
            notes = ["Baseline strategy. It is not a market-timing model."]
            name = "Buy and Hold"
        elif template.id == "ma_crossover":
            fast = int(parameters["fast_window"])
            slow = int(parameters["slow_window"])
            source = str(parameters["source"])
            indicators = [
                _indicator("sma_fast", "SMA", source, window=fast),
                _indicator("sma_slow", "SMA", source, window=slow),
            ]
            entry = _rule("AND", [{"type": "CROSSOVER", "left": "sma_fast", "right": "sma_slow"}])
            exit_rules = _rule(
                "OR", [{"type": "CROSSUNDER", "left": "sma_fast", "right": "sma_slow"}]
            )
            notes = ["Trend-following crossover; whipsaw risk can increase in sideways markets."]
            name = f"SMA {fast}/{slow} Crossover"
        elif template.id == "ma_crossover_rsi":
            fast = int(parameters["fast_window"])
            slow = int(parameters["slow_window"])
            rsi_window = int(parameters["rsi_window"])
            source = str(parameters["source"])
            indicators = [
                _indicator("sma_fast", "SMA", source, window=fast),
                _indicator("sma_slow", "SMA", source, window=slow),
                _indicator("rsi", "RSI", source, window=rsi_window),
            ]
            entry = _rule(
                "AND",
                [
                    {"type": "CROSSOVER", "left": "sma_fast", "right": "sma_slow"},
                    {
                        "type": "LESS_THAN",
                        "left": "rsi",
                        "right": float(parameters["rsi_entry_max"]),
                    },
                ],
            )
            exit_rules = _rule(
                "OR",
                [
                    {"type": "CROSSUNDER", "left": "sma_fast", "right": "sma_slow"},
                    {
                        "type": "GREATER_THAN",
                        "left": "rsi",
                        "right": float(parameters["rsi_exit_min"]),
                    },
                ],
            )
            notes = ["Adds RSI to avoid entries when the trend signal is already overextended."]
            name = f"SMA {fast}/{slow} Crossover + RSI Filter"
        elif template.id == "rsi_mean_reversion":
            window = int(parameters["rsi_window"])
            source = str(parameters["source"])
            indicators = [_indicator("rsi", "RSI", source, window=window)]
            entry = _rule(
                "AND",
                [{"type": "LESS_THAN", "left": "rsi", "right": float(parameters["entry_below"])}],
            )
            exit_rules = _rule(
                "OR",
                [{"type": "GREATER_THAN", "left": "rsi", "right": float(parameters["exit_above"])}],
            )
            notes = [
                (
                    "Mean-reversion logic can fail when oversold conditions become a "
                    "persistent downtrend."
                )
            ]
            name = f"RSI {window} Mean Reversion"
        elif template.id == "macd_trend_following":
            fast = int(parameters["fast_window"])
            slow = int(parameters["slow_window"])
            signal = int(parameters["signal_window"])
            source = str(parameters["source"])
            indicators = [
                {
                    "id": "macd",
                    "type": "MACD",
                    "source": source,
                    "fast": fast,
                    "slow": slow,
                    "signal": signal,
                    "outputs": {
                        "line": "macd.line",
                        "signal": "macd.signal",
                        "histogram": "macd.histogram",
                    },
                }
            ]
            entry = _rule(
                "AND", [{"type": "CROSSOVER", "left": "macd.line", "right": "macd.signal"}]
            )
            exit_rules = _rule(
                "OR", [{"type": "CROSSUNDER", "left": "macd.line", "right": "macd.signal"}]
            )
            notes = ["MACD can lag fast reversals because it is built from moving averages."]
            name = f"MACD {fast}/{slow}/{signal} Trend Following"
        else:  # pragma: no cover
            raise StrategyTemplateNotFoundError(f"Unsupported strategy template: {template.id}")

        return {
            "dsl_version": self.dsl_version,
            "strategy_id": template.id,
            "strategy_name": name,
            "template_id": template.id,
            "market": context.market.upper(),
            "symbol": context.symbol.upper(),
            "timeframe": context.timeframe,
            "date_range": {"start": _date(context.start), "end": _date(context.end)},
            "capital": {
                "initial_cash": context.initial_cash,
                "commission": context.commission,
                "slippage": context.slippage,
            },
            "indicators": indicators,
            "entry_rules": entry,
            "exit_rules": exit_rules,
            "risk_rules": {
                "stop_loss_pct": float(parameters.get("stop_loss_pct", 0.0)),
                "take_profit_pct": float(parameters.get("take_profit_pct", 0.0)),
                "max_position_pct": float(parameters.get("max_position_pct", 1.0)),
            },
            "metadata": {
                "created_at": datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
                "source": "strategy_template_system",
                "template_parameters": parameters,
                "notes": notes,
                "execution_assumption": (
                    "Signals are generated from completed daily bars; Phase 4 fills regular "
                    "entries and exits at next bar open."
                ),
                "disclaimer": (
                    "Educational research output only. Historical backtests do not guarantee "
                    "future performance."
                ),
            },
        }

    def _validate_strategy(self, strategy: dict[str, Any]) -> tuple[StrategyValidationIssue, ...]:
        issues: list[StrategyValidationIssue] = []
        required = {
            "dsl_version",
            "strategy_id",
            "symbol",
            "timeframe",
            "capital",
            "indicators",
            "entry_rules",
            "exit_rules",
            "risk_rules",
        }
        for key in sorted(required - set(strategy)):
            issues.append(
                _issue(
                    "missing_top_level_field",
                    StrategyIssueSeverity.ERROR,
                    f"Strategy DSL is missing top-level field '{key}'.",
                    f"$.{key}",
                )
            )
        if issues:
            return tuple(issues)

        if strategy.get("dsl_version") != self.dsl_version:
            issues.append(
                _issue(
                    "unsupported_dsl_version",
                    StrategyIssueSeverity.ERROR,
                    "Strategy DSL version is not supported.",
                    "$.dsl_version",
                )
            )
        if strategy.get("timeframe") != "1d":
            issues.append(
                _issue(
                    "unsupported_timeframe",
                    StrategyIssueSeverity.ERROR,
                    "Strategy templates currently support daily bars only.",
                    "$.timeframe",
                )
            )

        indicator_ids: set[str] = set()
        for index, indicator in enumerate(strategy.get("indicators", [])):
            indicator_id = indicator.get("id") if isinstance(indicator, dict) else None
            if not indicator_id:
                issues.append(
                    _issue(
                        "missing_indicator_id",
                        StrategyIssueSeverity.ERROR,
                        "Each indicator requires a stable id.",
                        f"$.indicators[{index}].id",
                    )
                )
                continue
            if indicator_id in indicator_ids:
                issues.append(
                    _issue(
                        "duplicate_indicator_id",
                        StrategyIssueSeverity.ERROR,
                        f"Indicator id '{indicator_id}' is duplicated.",
                        f"$.indicators[{index}].id",
                    )
                )
            indicator_ids.add(str(indicator_id))

        references = indicator_ids | {"open", "high", "low", "close", "adjusted_close", "volume"}
        for group_name in ("entry_rules", "exit_rules"):
            self._validate_rule_group(
                strategy.get(group_name), f"$.{group_name}", references, issues
            )

        capital = strategy.get("capital", {})
        if isinstance(capital, dict):
            for key in ("initial_cash", "commission", "slippage"):
                value = capital.get(key)
                if not isinstance(value, int | float) or value < 0:
                    issues.append(
                        _issue(
                            "invalid_capital_assumption",
                            StrategyIssueSeverity.ERROR,
                            f"Capital assumption '{key}' must be a non-negative number.",
                            f"$.capital.{key}",
                        )
                    )
        risk = strategy.get("risk_rules", {})
        if isinstance(risk, dict):
            max_position = risk.get("max_position_pct")
            if not isinstance(max_position, int | float) or max_position <= 0 or max_position > 1:
                issues.append(
                    _issue(
                        "invalid_max_position_pct",
                        StrategyIssueSeverity.ERROR,
                        "max_position_pct must be > 0 and <= 1.",
                        "$.risk_rules.max_position_pct",
                    )
                )
        return tuple(issues)

    def _validate_rule_group(
        self,
        group: Any,
        path: str,
        references: set[str],
        issues: list[StrategyValidationIssue],
    ) -> None:
        if not isinstance(group, dict):
            issues.append(
                _issue(
                    "invalid_rule_group",
                    StrategyIssueSeverity.ERROR,
                    "Rule group must be an object.",
                    path,
                )
            )
            return
        if group.get("operator") not in {"AND", "OR"}:
            issues.append(
                _issue(
                    "invalid_rule_operator",
                    StrategyIssueSeverity.ERROR,
                    "Rule operator must be AND or OR.",
                    f"{path}.operator",
                )
            )
        conditions = group.get("conditions")
        if not isinstance(conditions, list) or not conditions:
            issues.append(
                _issue(
                    "empty_conditions",
                    StrategyIssueSeverity.ERROR,
                    "Rule group requires at least one condition.",
                    f"{path}.conditions",
                )
            )
            return
        for index, condition in enumerate(conditions):
            if not isinstance(condition, dict):
                issues.append(
                    _issue(
                        "invalid_condition",
                        StrategyIssueSeverity.ERROR,
                        "Condition must be an object.",
                        f"{path}.conditions[{index}]",
                    )
                )
                continue
            for side in ("left", "right"):
                value = condition.get(side)
                if isinstance(value, str) and not _is_known_reference(value, references):
                    issues.append(
                        _issue(
                            "unknown_rule_reference",
                            StrategyIssueSeverity.ERROR,
                            f"Unknown rule reference: {value}.",
                            f"{path}.conditions[{index}].{side}",
                        )
                    )


def _build_templates() -> tuple[StrategyTemplate, ...]:
    source = (
        StrategyParameterOption("close", "Close"),
        StrategyParameterOption("adjusted_close", "Adjusted close"),
    )
    return (
        StrategyTemplate(
            id="buy_and_hold",
            name="Buy and Hold",
            description="Enter once and hold until the final bar. Useful as a baseline benchmark.",
            category=StrategyTemplateCategory.BASELINE,
            summary="Long-only baseline for comparing active strategies.",
            parameters=(
                _float(
                    "max_position_pct",
                    "Max position",
                    1.0,
                    "Portfolio fraction",
                    0.01,
                    1.0,
                    0.01,
                    "fraction",
                ),
            ),
            tags=("baseline", "benchmark"),
            indicator_kinds=(),
            risk_notes=("No timing signal; drawdown can follow the underlying asset.",),
        ),
        StrategyTemplate(
            id="ma_crossover",
            name="MA Crossover",
            description=(
                "Buy when a fast simple moving average crosses above a slow simple moving average."
            ),
            category=StrategyTemplateCategory.TREND_FOLLOWING,
            summary="Classic trend-following crossover template.",
            parameters=(
                _integer(
                    "fast_window",
                    "Fast SMA window",
                    20,
                    "Fast moving-average period.",
                    2,
                    250,
                    1,
                    "bars",
                ),
                _integer(
                    "slow_window",
                    "Slow SMA window",
                    60,
                    "Slow moving-average period.",
                    3,
                    400,
                    1,
                    "bars",
                ),
                _select("source", "Price source", "close", "Input price field.", source),
                *_risk_parameters(0.0, 0.0),
            ),
            tags=("trend", "moving-average", "crossover"),
            indicator_kinds=("SMA",),
            risk_notes=("Moving-average crossovers can whipsaw in range-bound markets.",),
        ),
        StrategyTemplate(
            id="ma_crossover_rsi",
            name="MA Crossover + RSI Filter",
            description=(
                "Buy on a bullish moving-average crossover only when RSI is below the "
                "configured ceiling."
            ),
            category=StrategyTemplateCategory.TREND_FOLLOWING,
            summary="Trend-following template with an overextension filter.",
            parameters=(
                _integer(
                    "fast_window",
                    "Fast SMA window",
                    20,
                    "Fast moving-average period.",
                    2,
                    250,
                    1,
                    "bars",
                ),
                _integer(
                    "slow_window",
                    "Slow SMA window",
                    60,
                    "Slow moving-average period.",
                    3,
                    400,
                    1,
                    "bars",
                ),
                _integer("rsi_window", "RSI window", 14, "RSI lookback period.", 2, 100, 1, "bars"),
                _float(
                    "rsi_entry_max",
                    "Entry RSI max",
                    70,
                    "Require RSI below this level on entry.",
                    1,
                    99,
                    1,
                    "level",
                ),
                _float(
                    "rsi_exit_min",
                    "Exit RSI min",
                    80,
                    "Exit when RSI rises above this level.",
                    2,
                    100,
                    1,
                    "level",
                ),
                _select("source", "Price source", "close", "Input price field.", source),
                *_risk_parameters(0.08, 0.2),
            ),
            tags=("trend", "moving-average", "rsi", "filter"),
            indicator_kinds=("SMA", "RSI"),
            risk_notes=("The filter can skip strong momentum continuation moves.",),
        ),
        StrategyTemplate(
            id="rsi_mean_reversion",
            name="RSI Mean Reversion",
            description=(
                "Buy when RSI is oversold and exit after RSI recovers above a neutral threshold."
            ),
            category=StrategyTemplateCategory.MEAN_REVERSION,
            summary="Long-only RSI mean-reversion template.",
            parameters=(
                _integer("rsi_window", "RSI window", 14, "RSI lookback period.", 2, 100, 1, "bars"),
                _float(
                    "entry_below",
                    "Entry below",
                    30,
                    "Enter when RSI is below this level.",
                    1,
                    99,
                    1,
                    "level",
                ),
                _float(
                    "exit_above",
                    "Exit above",
                    50,
                    "Exit when RSI recovers above this level.",
                    2,
                    100,
                    1,
                    "level",
                ),
                _select("source", "Price source", "close", "Input price field.", source),
                *_risk_parameters(0.1, 0.0),
            ),
            tags=("mean-reversion", "rsi", "oscillator"),
            indicator_kinds=("RSI",),
            risk_notes=("Oversold can become more oversold during persistent downtrends.",),
        ),
        StrategyTemplate(
            id="macd_trend_following",
            name="MACD Trend Following",
            description=(
                "Buy when MACD line crosses above the signal line and exit on the opposite cross."
            ),
            category=StrategyTemplateCategory.TREND_FOLLOWING,
            summary="EMA oscillator crossover template.",
            parameters=(
                _integer(
                    "fast_window",
                    "Fast EMA window",
                    12,
                    "Fast EMA period used by MACD.",
                    2,
                    200,
                    1,
                    "bars",
                ),
                _integer(
                    "slow_window",
                    "Slow EMA window",
                    26,
                    "Slow EMA period used by MACD.",
                    3,
                    300,
                    1,
                    "bars",
                ),
                _integer(
                    "signal_window", "Signal EMA window", 9, "Signal EMA period.", 2, 100, 1, "bars"
                ),
                _select("source", "Price source", "close", "Input price field.", source),
                *_risk_parameters(0.0, 0.0),
            ),
            tags=("momentum", "macd", "trend"),
            indicator_kinds=("MACD",),
            risk_notes=("MACD can lag fast reversals because it is moving-average based.",),
        ),
    )


def _risk_parameters(
    stop_loss: float, take_profit: float
) -> tuple[StrategyParameterDefinition, ...]:
    return (
        _float(
            "stop_loss_pct",
            "Stop loss",
            stop_loss,
            "Fractional stop loss; 0 disables it.",
            0,
            0.8,
            0.01,
            "fraction",
        ),
        _float(
            "take_profit_pct",
            "Take profit",
            take_profit,
            "Fractional take profit; 0 disables it.",
            0,
            3.0,
            0.01,
            "fraction",
        ),
        _float(
            "max_position_pct",
            "Max position",
            1.0,
            "Maximum portfolio fraction allocated to this strategy.",
            0.01,
            1.0,
            0.01,
            "fraction",
        ),
    )


def _integer(
    key: str,
    label: str,
    default: int,
    description: str,
    minimum: int,
    maximum: int,
    step: int,
    unit: str,
) -> StrategyParameterDefinition:
    return StrategyParameterDefinition(
        key,
        label,
        StrategyParameterKind.INTEGER,
        default,
        description,
        minimum,
        maximum,
        step,
        unit,
    )


def _float(
    key: str,
    label: str,
    default: float,
    description: str,
    minimum: float,
    maximum: float,
    step: float,
    unit: str,
) -> StrategyParameterDefinition:
    return StrategyParameterDefinition(
        key, label, StrategyParameterKind.FLOAT, default, description, minimum, maximum, step, unit
    )


def _select(
    key: str,
    label: str,
    default: str,
    description: str,
    options: tuple[StrategyParameterOption, ...],
) -> StrategyParameterDefinition:
    return StrategyParameterDefinition(
        key, label, StrategyParameterKind.SELECT, default, description, options=options
    )


def _indicator(
    indicator_id: str, indicator_type: str, source: str, **parameters: int | float
) -> dict[str, Any]:
    return {"id": indicator_id, "type": indicator_type, "source": source, **parameters}


def _rule(operator: str, conditions: list[dict[str, Any]]) -> dict[str, Any]:
    return {"operator": operator, "conditions": conditions}


def _issue(
    code: str,
    severity: StrategyIssueSeverity,
    message: str,
    path: str,
    context: dict[str, Any] | None = None,
) -> StrategyValidationIssue:
    return StrategyValidationIssue(
        code=code, severity=severity, message=message, path=path, context=context or {}
    )


def _date(value: Any) -> str | None:
    return value.isoformat() if value else None


def _normalize_template_id(template_id: str) -> str:
    return template_id.strip().lower().replace("-", "_")


def _is_known_reference(value: str, references: set[str]) -> bool:
    if value in references or _is_number(value):
        return True
    if "." in value:
        return value.split(".", 1)[0] in references
    return False


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True
