from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

import pandas as pd

from app.domain.backtest import (
    BacktestAgentStep,
    BacktestAssumptions,
    BacktestDataSource,
    BacktestEquityPoint,
    BacktestMetrics,
    BacktestResult,
    BacktestSignalPoint,
    BacktestStepStatus,
    BacktestTrade,
    BacktestWarning,
    BacktestWarningSeverity,
)
from app.domain.errors import StrategyDslValidationError
from app.domain.market import MarketBar, MarketSeries
from app.domain.strategy import StrategyValidationIssue
from app.services.market_data_service import MarketDataService
from app.services.strategy_template_service import StrategyTemplateService

TRADING_DAYS_PER_YEAR = 252
PRICE_FIELDS = {"open", "high", "low", "close", "adjusted_close", "volume"}


@dataclass(slots=True)
class _OpenPosition:
    entry_date: date
    entry_index: int
    entry_price: float
    raw_entry_price: float
    quantity: float
    entry_reason: str
    entry_commission: float
    entry_slippage: float


@dataclass(frozen=True, slots=True)
class _SignalEvaluation:
    entry_signal: bool
    exit_signal: bool
    entry_reason: str | None
    exit_reason: str | None


class BacktestService:
    """Deterministic long-only MVP backtesting engine for Strategy JSON DSL."""

    def __init__(
        self,
        *,
        market_data_service: MarketDataService,
        strategy_template_service: StrategyTemplateService,
    ) -> None:
        self.market_data_service = market_data_service
        self.strategy_template_service = strategy_template_service

    def run(self, strategy_json: dict[str, Any]) -> BacktestResult:
        steps: list[BacktestAgentStep] = []
        warnings: list[BacktestWarning] = []
        steps.append(
            BacktestAgentStep(
                key="strategy_received",
                status=BacktestStepStatus.SUCCESS,
                message="Received Strategy JSON DSL and execution assumptions.",
                detail={
                    "strategy_id": strategy_json.get("strategy_id"),
                    "symbol": strategy_json.get("symbol"),
                    "timeframe": strategy_json.get("timeframe"),
                },
            )
        )
        self._validate_strategy(strategy_json, steps)

        symbol = str(strategy_json["symbol"]).upper()
        timeframe = str(strategy_json["timeframe"])
        date_range = strategy_json.get("date_range") or {}
        start = _optional_date(date_range.get("start"))
        end = _optional_date(date_range.get("end"))
        series = self.market_data_service.get_series(
            symbol, start=start, end=end, interval=timeframe
        )
        steps.append(
            BacktestAgentStep(
                key="fetch_market_data",
                status=BacktestStepStatus.SUCCESS,
                message=f"Loaded {len(series.bars)} normalized OHLCV bars for {symbol}.",
                detail={
                    "symbol": symbol,
                    "effective_start": series.effective_start.isoformat(),
                    "effective_end": series.effective_end.isoformat(),
                    "providers": list(series.providers),
                },
            )
        )
        if series.contains_fixture_data:
            warnings.append(
                BacktestWarning(
                    code="synthetic_fixture_data",
                    severity=BacktestWarningSeverity.INFO,
                    message=(
                        "This run uses deterministic offline fixture data; it is suitable for "
                        "engineering tests, not market research."
                    ),
                    context={"symbol": symbol},
                )
            )

        frame = self._feature_frame(series.bars, strategy_json.get("indicators", []))
        non_feature_columns = PRICE_FIELDS | {"date"}
        indicator_columns = [c for c in frame.columns if c not in non_feature_columns]
        steps.append(
            BacktestAgentStep(
                key="compute_indicators",
                status=BacktestStepStatus.SUCCESS,
                message=f"Computed {len(indicator_columns)} indicator output column(s).",
                detail={"columns": indicator_columns},
            )
        )

        signal_evaluations = self._generate_signals(frame, strategy_json)
        steps.append(
            BacktestAgentStep(
                key="generate_signals",
                status=BacktestStepStatus.SUCCESS,
                message="Generated entry and exit signals from Strategy JSON DSL rules.",
                detail={
                    "entry_signals": sum(item.entry_signal for item in signal_evaluations),
                    "exit_signals": sum(item.exit_signal for item in signal_evaluations),
                },
            )
        )

        result = self._execute_backtest(
            strategy_json=strategy_json,
            series=series,
            frame=frame,
            signal_evaluations=signal_evaluations,
            warnings=warnings,
        )
        steps.append(
            BacktestAgentStep(
                key="run_backtest",
                status=BacktestStepStatus.SUCCESS,
                message=f"Executed long-only backtest with {len(result.trades)} closed trade(s).",
                detail={
                    "final_equity": _round(result.equity_curve[-1].equity),
                    "trade_count": len(result.trades),
                },
            )
        )
        steps.append(
            BacktestAgentStep(
                key="analyze_performance",
                status=BacktestStepStatus.SUCCESS,
                message=(
                    "Computed total return, annual return, Sharpe, drawdown, and trade metrics."
                ),
                detail={
                    "total_return_pct": result.metrics.total_return_pct,
                    "max_drawdown_pct": result.metrics.max_drawdown_pct,
                    "sharpe_ratio": result.metrics.sharpe_ratio,
                },
            )
        )
        if not result.trades:
            warnings.append(
                BacktestWarning(
                    code="no_closed_trades",
                    severity=BacktestWarningSeverity.WARNING,
                    message="The selected rules did not produce any closed trades over the range.",
                    context={"symbol": symbol},
                )
            )
        warning_summary = [warning.code for warning in warnings]
        steps.append(
            BacktestAgentStep(
                key="risk_review",
                status=BacktestStepStatus.WARNING if warnings else BacktestStepStatus.SUCCESS,
                message=(
                    f"Reviewed {len(warnings)} warning(s): {', '.join(warning_summary)}."
                    if warnings
                    else "No data-quality or execution warnings were produced for this run."
                ),
                detail={"warning_count": len(warnings), "warning_codes": warning_summary},
            )
        )
        return BacktestResult(
            run_id=result.run_id,
            strategy_id=result.strategy_id,
            strategy_name=result.strategy_name,
            symbol=result.symbol,
            timeframe=result.timeframe,
            assumptions=result.assumptions,
            data_source=result.data_source,
            metrics=result.metrics,
            equity_curve=result.equity_curve,
            drawdown_curve=result.drawdown_curve,
            trades=result.trades,
            signals=result.signals,
            warnings=tuple(warnings),
            agent_steps=tuple(steps),
        )

    def _validate_strategy(
        self, strategy_json: dict[str, Any], steps: list[BacktestAgentStep]
    ) -> None:
        report = self.strategy_template_service.validate_strategy(strategy_json)
        if not report.is_valid:
            raise StrategyDslValidationError(
                "Strategy JSON DSL failed validation and cannot be backtested.",
                details={"issues": [_issue_detail(issue) for issue in report.issues]},
            )
        steps.append(
            BacktestAgentStep(
                key="validate_strategy",
                status=BacktestStepStatus.SUCCESS,
                message="Strategy JSON DSL passed structural validation.",
                detail={"issue_count": len(report.issues)},
            )
        )

    def _feature_frame(
        self, bars: tuple[MarketBar, ...], indicators: list[dict[str, Any]]
    ) -> pd.DataFrame:
        frame = pd.DataFrame(
            [
                {
                    "date": bar.trade_date,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "adjusted_close": bar.adjusted_close,
                    "volume": bar.volume,
                }
                for bar in bars
            ]
        ).sort_values("date", ignore_index=True)
        for indicator in indicators:
            indicator_type = str(indicator.get("type", "")).upper()
            indicator_id = str(indicator.get("id", "")).strip()
            source = _source(indicator.get("source", "close"))
            if not indicator_id:
                raise StrategyDslValidationError(
                    "Indicator is missing an id.", details={"indicator": indicator}
                )
            if indicator_type == "SMA":
                window = _positive_int(indicator.get("window"), "window")
                frame[indicator_id] = (
                    frame[source].rolling(window=window, min_periods=window).mean()
                )
            elif indicator_type == "EMA":
                window = _positive_int(indicator.get("window"), "window")
                frame[indicator_id] = (
                    frame[source].ewm(span=window, adjust=False, min_periods=window).mean()
                )
            elif indicator_type == "RSI":
                window = _positive_int(indicator.get("window"), "window")
                frame[indicator_id] = _rsi(frame[source], window)
            elif indicator_type == "MACD":
                fast = _positive_int(indicator.get("fast"), "fast")
                slow = _positive_int(indicator.get("slow"), "slow")
                signal_window = _positive_int(indicator.get("signal"), "signal")
                if fast >= slow:
                    raise StrategyDslValidationError(
                        "MACD fast window must be smaller than slow window.",
                        details={"indicator_id": indicator_id, "fast": fast, "slow": slow},
                    )
                fast_ema = frame[source].ewm(span=fast, adjust=False, min_periods=fast).mean()
                slow_ema = frame[source].ewm(span=slow, adjust=False, min_periods=slow).mean()
                macd = fast_ema - slow_ema
                signal = macd.ewm(
                    span=signal_window, adjust=False, min_periods=signal_window
                ).mean()
                frame[f"{indicator_id}.line"] = macd
                frame[f"{indicator_id}.signal"] = signal
                frame[f"{indicator_id}.histogram"] = macd - signal
            elif indicator_type in {"BOLLINGER_BANDS", "BBANDS"}:
                window = _positive_int(indicator.get("window"), "window")
                stddev = float(indicator.get("stddev", indicator.get("standard_deviations", 2)))
                middle = frame[source].rolling(window=window, min_periods=window).mean()
                rolling_std = frame[source].rolling(window=window, min_periods=window).std(ddof=0)
                frame[f"{indicator_id}.middle"] = middle
                frame[f"{indicator_id}.upper"] = middle + stddev * rolling_std
                frame[f"{indicator_id}.lower"] = middle - stddev * rolling_std
            elif indicator_type == "ATR":
                window = _positive_int(indicator.get("window"), "window")
                frame[indicator_id] = _atr(frame, window)
            else:
                raise StrategyDslValidationError(
                    "Unsupported indicator type in Strategy JSON DSL.",
                    details={"indicator_id": indicator_id, "type": indicator_type},
                )
        return frame

    def _generate_signals(
        self, frame: pd.DataFrame, strategy_json: dict[str, Any]
    ) -> tuple[_SignalEvaluation, ...]:
        entry_group = strategy_json.get("entry_rules", {})
        exit_group = strategy_json.get("exit_rules", {})
        evaluations = []
        for index in range(len(frame)):
            entry = _evaluate_group(frame, entry_group, index)
            exit_signal = _evaluate_group(frame, exit_group, index)
            evaluations.append(
                _SignalEvaluation(
                    entry_signal=entry,
                    exit_signal=exit_signal,
                    entry_reason=_rule_reason(entry_group, frame, index) if entry else None,
                    exit_reason=_rule_reason(exit_group, frame, index) if exit_signal else None,
                )
            )
        return tuple(evaluations)

    def _execute_backtest(
        self,
        *,
        strategy_json: dict[str, Any],
        series: MarketSeries,
        frame: pd.DataFrame,
        signal_evaluations: tuple[_SignalEvaluation, ...],
        warnings: list[BacktestWarning],
    ) -> BacktestResult:
        capital = strategy_json["capital"]
        risk = strategy_json["risk_rules"]
        initial_cash = float(capital["initial_cash"])
        commission_rate = float(capital.get("commission", 0.0))
        slippage_rate = float(capital.get("slippage", 0.0))
        max_position_pct = float(risk.get("max_position_pct", 1.0))
        stop_loss_pct = float(risk.get("stop_loss_pct", 0.0))
        take_profit_pct = float(risk.get("take_profit_pct", 0.0))

        cash = initial_cash
        position: _OpenPosition | None = None
        pending_entry_reason: str | None = None
        pending_exit_reason: str | None = None
        trade_counter = 0
        exposure_bars = 0
        trades: list[BacktestTrade] = []
        signals: list[BacktestSignalPoint] = []
        equity_curve: list[BacktestEquityPoint] = []
        executed_orders: dict[int, str] = {}

        for index, row in frame.iterrows():
            bar_date = row["date"]
            raw_open = float(row["open"])
            raw_close = float(row["close"])
            if pending_exit_reason and position:
                trade_counter += 1
                cash, trade = _close_position(
                    trade_id=trade_counter,
                    position=position,
                    cash=cash,
                    raw_price=raw_open,
                    fill_price=raw_open * (1 - slippage_rate),
                    exit_date=bar_date,
                    exit_index=index,
                    exit_reason=pending_exit_reason,
                    commission_rate=commission_rate,
                )
                trades.append(trade)
                position = None
                pending_exit_reason = None
                executed_orders[index] = "exit"
            if pending_entry_reason and not position:
                cash, position = _open_position(
                    cash=cash,
                    raw_price=raw_open,
                    fill_price=raw_open * (1 + slippage_rate),
                    entry_date=bar_date,
                    entry_index=index,
                    reason=pending_entry_reason,
                    commission_rate=commission_rate,
                    max_position_pct=max_position_pct,
                )
                pending_entry_reason = None
                executed_orders[index] = "entry"

            signal = signal_evaluations[index]
            entered_on_current_bar = False
            if (
                index == 0
                and signal.entry_signal
                and signal.entry_reason == "ENTER_ON_FIRST_BAR"
                and not position
            ):
                cash, position = _open_position(
                    cash=cash,
                    raw_price=raw_open,
                    fill_price=raw_open * (1 + slippage_rate),
                    entry_date=bar_date,
                    entry_index=index,
                    reason=signal.entry_reason,
                    commission_rate=commission_rate,
                    max_position_pct=max_position_pct,
                )
                entered_on_current_bar = True
                executed_orders[index] = "entry"
            if position:
                exposure_bars += 1

            is_last_bar = index == len(frame) - 1
            exit_reason = _risk_exit_reason(
                row=row,
                position=position,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
            )
            if not exit_reason and signal.exit_signal:
                exit_reason = signal.exit_reason
            if is_last_bar and position:
                if exit_reason is None:
                    exit_reason = "final_bar_liquidation"
                    warnings.append(
                        BacktestWarning(
                            code="forced_final_liquidation",
                            severity=BacktestWarningSeverity.INFO,
                            message="An open long position was closed on the final bar close.",
                            context={"date": bar_date.isoformat()},
                        )
                    )
                trade_counter += 1
                cash, trade = _close_position(
                    trade_id=trade_counter,
                    position=position,
                    cash=cash,
                    raw_price=raw_close,
                    fill_price=raw_close * (1 - slippage_rate),
                    exit_date=bar_date,
                    exit_index=index,
                    exit_reason=exit_reason,
                    commission_rate=commission_rate,
                )
                trades.append(trade)
                position = None
                executed_orders[index] = "exit"
            elif position and exit_reason:
                pending_exit_reason = exit_reason
            elif not position and signal.entry_signal and not entered_on_current_bar:
                if is_last_bar:
                    warnings.append(
                        BacktestWarning(
                            code="entry_signal_on_final_bar_skipped",
                            severity=BacktestWarningSeverity.WARNING,
                            message=(
                                "An entry signal occurred on the final bar and could not be filled."
                            ),
                            context={"date": bar_date.isoformat()},
                        )
                    )
                else:
                    pending_entry_reason = signal.entry_reason

            position_value = 0.0 if not position else position.quantity * raw_close
            equity = cash + position_value
            high_watermark = max([initial_cash, *(point.equity for point in equity_curve), equity])
            drawdown = 0.0 if high_watermark <= 0 else (equity / high_watermark - 1) * 100
            equity_curve.append(
                BacktestEquityPoint(
                    date=bar_date,
                    equity=_round(equity),
                    cash=_round(cash),
                    position_value=_round(position_value),
                    drawdown_pct=_round(drawdown),
                )
            )
            signals.append(
                BacktestSignalPoint(
                    date=bar_date,
                    entry_signal=signal.entry_signal,
                    exit_signal=bool(signal.exit_signal or exit_reason),
                    entry_reason=signal.entry_reason,
                    exit_reason=exit_reason or signal.exit_reason,
                    executed_order=executed_orders.get(index),
                )
            )

        metrics = _metrics(
            equity_curve=equity_curve,
            trades=trades,
            initial_cash=initial_cash,
            exposure_bars=exposure_bars,
        )
        return BacktestResult(
            run_id=f"bt_{datetime.now(tz=UTC).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}",
            strategy_id=str(strategy_json.get("strategy_id", "unknown")),
            strategy_name=str(strategy_json.get("strategy_name", "Untitled strategy")),
            symbol=strategy_json["symbol"],
            timeframe=strategy_json["timeframe"],
            assumptions=BacktestAssumptions(
                price_field="close",
                signal_timing="signals use completed daily bars only",
                fill_timing=(
                    "market entries/exits fill at next bar open; final liquidation uses final close"
                ),
                position_type="long_only",
                max_positions=1,
                commission=commission_rate,
                slippage=slippage_rate,
                forced_final_liquidation=True,
            ),
            data_source=BacktestDataSource(
                provider=series.providers,
                dataset=series.datasets,
                contains_fixture_data=series.contains_fixture_data,
                effective_start=series.effective_start,
                effective_end=series.effective_end,
                bar_count=len(series.bars),
            ),
            metrics=metrics,
            equity_curve=tuple(equity_curve),
            drawdown_curve=tuple(equity_curve),
            trades=tuple(trades),
            signals=tuple(signals),
            warnings=tuple(warnings),
            agent_steps=(),
        )


def _open_position(
    *,
    cash: float,
    raw_price: float,
    fill_price: float,
    entry_date: date,
    entry_index: int,
    reason: str | None,
    commission_rate: float,
    max_position_pct: float,
) -> tuple[float, _OpenPosition]:
    deployable_cash = max(0.0, cash * max_position_pct)
    notional = deployable_cash / (1 + commission_rate)
    quantity = notional / fill_price if fill_price > 0 else 0.0
    commission = notional * commission_rate
    next_cash = cash - notional - commission
    slippage_paid = abs(fill_price - raw_price) * quantity
    return next_cash, _OpenPosition(
        entry_date=entry_date,
        entry_index=entry_index,
        entry_price=fill_price,
        raw_entry_price=raw_price,
        quantity=quantity,
        entry_reason=reason or "entry_signal",
        entry_commission=commission,
        entry_slippage=slippage_paid,
    )


def _close_position(
    *,
    trade_id: int,
    position: _OpenPosition,
    cash: float,
    raw_price: float,
    fill_price: float,
    exit_date: date,
    exit_index: int,
    exit_reason: str,
    commission_rate: float,
) -> tuple[float, BacktestTrade]:
    exit_notional = position.quantity * fill_price
    exit_commission = exit_notional * commission_rate
    gross_pnl = (fill_price - position.entry_price) * position.quantity
    commission_paid = position.entry_commission + exit_commission
    net_pnl = gross_pnl - commission_paid
    slippage_paid = position.entry_slippage + abs(fill_price - raw_price) * position.quantity
    next_cash = cash + exit_notional - exit_commission
    capital_used = position.quantity * position.entry_price + position.entry_commission
    return_pct = 0.0 if capital_used <= 0 else (net_pnl / capital_used) * 100
    return next_cash, BacktestTrade(
        trade_id=trade_id,
        side="long",
        entry_date=position.entry_date,
        exit_date=exit_date,
        entry_price=_round(position.entry_price),
        exit_price=_round(fill_price),
        quantity=_round(position.quantity),
        gross_pnl=_round(gross_pnl),
        net_pnl=_round(net_pnl),
        return_pct=_round(return_pct),
        holding_period_bars=max(0, exit_index - position.entry_index),
        entry_reason=position.entry_reason,
        exit_reason=exit_reason,
        commission_paid=_round(commission_paid),
        slippage_paid=_round(slippage_paid),
    )


def _risk_exit_reason(
    *,
    row: pd.Series,
    position: _OpenPosition | None,
    stop_loss_pct: float,
    take_profit_pct: float,
) -> str | None:
    if not position:
        return None
    if stop_loss_pct > 0 and float(row["low"]) <= position.entry_price * (1 - stop_loss_pct):
        return "stop_loss"
    if take_profit_pct > 0 and float(row["high"]) >= position.entry_price * (1 + take_profit_pct):
        return "take_profit"
    return None


def _metrics(
    *,
    equity_curve: list[BacktestEquityPoint],
    trades: list[BacktestTrade],
    initial_cash: float,
    exposure_bars: int,
) -> BacktestMetrics:
    final_equity = equity_curve[-1].equity if equity_curve else initial_cash
    total_return_pct = (final_equity / initial_cash - 1) * 100 if initial_cash else 0.0
    first_date = equity_curve[0].date
    last_date = equity_curve[-1].date
    years = max((last_date - first_date).days / 365.25, 0)
    annual_return = None
    if years > 0 and final_equity > 0 and initial_cash > 0:
        annual_return = ((final_equity / initial_cash) ** (1 / years) - 1) * 100
    returns = pd.Series([p.equity for p in equity_curve], dtype="float64").pct_change().dropna()
    sharpe = None
    if len(returns) >= 2:
        std = returns.std(ddof=1)
        if std > 0 and math.isfinite(std):
            sharpe = float((returns.mean() / std) * math.sqrt(TRADING_DAYS_PER_YEAR))
    wins = [trade.net_pnl for trade in trades if trade.net_pnl > 0]
    losses = [trade.net_pnl for trade in trades if trade.net_pnl < 0]
    win_rate = None if not trades else (len(wins) / len(trades)) * 100
    profit_factor = None
    if losses:
        profit_factor = sum(wins) / abs(sum(losses)) if wins else 0.0
    average_return = None if not trades else sum(trade.return_pct for trade in trades) / len(trades)
    max_drawdown = min((point.drawdown_pct for point in equity_curve), default=0.0)
    exposure = exposure_bars / len(equity_curve) * 100 if equity_curve else 0.0
    return BacktestMetrics(
        total_return_pct=_round(total_return_pct),
        annual_return_pct=_round_optional(annual_return),
        sharpe_ratio=_round_optional(sharpe),
        max_drawdown_pct=_round(max_drawdown),
        win_rate_pct=_round_optional(win_rate),
        profit_factor=_round_optional(profit_factor),
        trade_count=len(trades),
        exposure_time_pct=_round(exposure),
        average_trade_return_pct=_round_optional(average_return),
    )


def _evaluate_group(frame: pd.DataFrame, group: dict[str, Any], index: int) -> bool:
    conditions = group.get("conditions", []) if isinstance(group, dict) else []
    values = [_evaluate_condition(frame, condition, index) for condition in conditions]
    if not values:
        return False
    return all(values) if group.get("operator") == "AND" else any(values)


def _evaluate_condition(frame: pd.DataFrame, condition: dict[str, Any], index: int) -> bool:
    condition_type = str(condition.get("type", "")).upper()
    if condition_type == "ENTER_ON_FIRST_BAR":
        return index == 0
    if condition_type == "EXIT_ON_LAST_BAR":
        return index == len(frame) - 1
    if condition_type in {"CROSSOVER", "CROSSUNDER"}:
        if index == 0:
            return False
        left_now = _value(frame, condition.get("left"), index)
        right_now = _value(frame, condition.get("right"), index)
        left_prev = _value(frame, condition.get("left"), index - 1)
        right_prev = _value(frame, condition.get("right"), index - 1)
        if not all(_is_number(value) for value in (left_now, right_now, left_prev, right_prev)):
            return False
        if condition_type == "CROSSOVER":
            return left_prev <= right_prev and left_now > right_now
        return left_prev >= right_prev and left_now < right_now
    left = _value(frame, condition.get("left"), index)
    right = _value(frame, condition.get("right"), index)
    if not all(_is_number(value) for value in (left, right)):
        return False
    if condition_type == "LESS_THAN":
        return left < right
    if condition_type == "LESS_THAN_OR_EQUAL":
        return left <= right
    if condition_type == "GREATER_THAN":
        return left > right
    if condition_type == "GREATER_THAN_OR_EQUAL":
        return left >= right
    raise StrategyDslValidationError(
        "Unsupported rule condition type in Strategy JSON DSL.",
        details={"condition_type": condition_type},
    )


def _value(frame: pd.DataFrame, token: object, index: int) -> float | None:
    if isinstance(token, int | float):
        return float(token)
    if not isinstance(token, str):
        return None
    if token not in frame.columns:
        raise StrategyDslValidationError(
            "Rule reference is not available in the feature frame.",
            details={"reference": token},
        )
    value = frame[token].iloc[index]
    return float(value) if _is_number(value) else None


def _rule_reason(group: dict[str, Any], frame: pd.DataFrame, index: int) -> str:
    if not isinstance(group, dict):
        return "rule_signal"
    matched = []
    for condition in group.get("conditions", []):
        if isinstance(condition, dict) and _evaluate_condition(frame, condition, index):
            matched.append(str(condition.get("type", "rule_signal")).upper())
    if not matched:
        return "rule_signal"
    return "+".join(matched) if group.get("operator") == "AND" else matched[0]


def _rsi(series: pd.Series, window: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    average_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    relative_strength = average_gain / average_loss
    raw_rsi = 100 - (100 / (1 + relative_strength))
    raw_rsi = raw_rsi.mask((average_loss == 0) & (average_gain > 0), 100.0)
    return raw_rsi.mask((average_loss == 0) & (average_gain == 0), 50.0)


def _atr(frame: pd.DataFrame, window: int) -> pd.Series:
    previous_close = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


def _issue_detail(issue: StrategyValidationIssue) -> dict[str, Any]:
    return {
        "code": issue.code,
        "severity": issue.severity.value,
        "message": issue.message,
        "path": issue.path,
        "context": issue.context,
    }


def _optional_date(value: object) -> date | None:
    if value in {None, ""}:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _source(value: object) -> str:
    source = str(value)
    if source not in {"open", "high", "low", "close", "adjusted_close"}:
        raise StrategyDslValidationError(
            "Unsupported indicator source in Strategy JSON DSL.", details={"source": source}
        )
    return source


def _positive_int(value: object, name: str) -> int:
    try:
        result = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise StrategyDslValidationError(
            f"Indicator parameter '{name}' must be an integer.", details={"value": value}
        ) from exc
    if result <= 0:
        raise StrategyDslValidationError(
            f"Indicator parameter '{name}' must be positive.", details={"value": value}
        )
    return result


def _is_number(value: object) -> bool:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return math.isfinite(result) and not pd.isna(result)


def _round(value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    return round(float(value), 6)


def _round_optional(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return _round(value)
