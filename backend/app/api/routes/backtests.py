from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_backtest_service
from app.domain.agent_workflow import workflow_step_definition
from app.domain.backtest import BacktestResult
from app.schemas.backtests import (
    BacktestAgentStepResponse,
    BacktestDataSourceResponse,
    BacktestDataSummaryResponse,
    BacktestDrawdownPointResponse,
    BacktestEquityPointResponse,
    BacktestMetricsResponse,
    BacktestRunRequest,
    BacktestRunResponse,
    BacktestSignalPointResponse,
    BacktestTradeResponse,
    BacktestWarningResponse,
)
from app.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtests", tags=["backtest engine"])
BacktestServiceDependency = Annotated[BacktestService, Depends(get_backtest_service)]


@router.post(
    "/run",
    response_model=BacktestRunResponse,
    summary="Run one Strategy JSON DSL backtest",
)
def run_backtest(
    request: BacktestRunRequest,
    service: BacktestServiceDependency,
) -> BacktestRunResponse:
    return _response(service.run(request.strategy_json))


def _response(result: BacktestResult) -> BacktestRunResponse:
    data = result.data_source
    final_equity = result.equity_curve[-1].equity if result.equity_curve else 0.0
    assumptions = {
        "price_field": result.assumptions.price_field,
        "signal_timing": result.assumptions.signal_timing,
        "fill_timing": result.assumptions.fill_timing,
        "position_type": result.assumptions.position_type,
        "max_positions": result.assumptions.max_positions,
        "commission": result.assumptions.commission,
        "slippage": result.assumptions.slippage,
        "forced_final_liquidation": result.assumptions.forced_final_liquidation,
        "final_liquidation": result.assumptions.forced_final_liquidation,
        "disclaimer": "Educational research output only; not investment advice.",
    }
    return BacktestRunResponse(
        run_id=result.run_id,
        created_at=datetime.now(tz=UTC).replace(microsecond=0),
        status="success",
        strategy_id=result.strategy_id,
        strategy_name=result.strategy_name,
        symbol=result.symbol,
        timeframe="1d",
        assumptions=assumptions,
        data=BacktestDataSummaryResponse(
            symbol=result.symbol,
            market="US",
            timeframe="1d",
            start=data.effective_start,
            end=data.effective_end,
            bars=data.bar_count,
            providers=list(data.provider),
            datasets=list(data.dataset),
            contains_fixture_data=data.contains_fixture_data,
        ),
        data_source=BacktestDataSourceResponse(
            provider=list(data.provider),
            dataset=list(data.dataset),
            contains_fixture_data=data.contains_fixture_data,
            effective_start=data.effective_start,
            effective_end=data.effective_end,
            bar_count=data.bar_count,
        ),
        metrics=BacktestMetricsResponse(
            total_return_pct=result.metrics.total_return_pct,
            annual_return_pct=result.metrics.annual_return_pct,
            sharpe_ratio=result.metrics.sharpe_ratio,
            max_drawdown_pct=result.metrics.max_drawdown_pct,
            win_rate_pct=result.metrics.win_rate_pct,
            profit_factor=result.metrics.profit_factor,
            trade_count=result.metrics.trade_count,
            exposure_time_pct=result.metrics.exposure_time_pct,
            average_trade_return_pct=result.metrics.average_trade_return_pct,
            final_equity=final_equity,
        ),
        equity_curve=[
            BacktestEquityPointResponse(
                date=point.date,
                equity=point.equity,
                cash=point.cash,
                position_value=point.position_value,
                drawdown_pct=point.drawdown_pct,
                in_position=point.position_value > 0,
            )
            for point in result.equity_curve
        ],
        drawdown_curve=[
            BacktestDrawdownPointResponse(date=point.date, drawdown_pct=point.drawdown_pct)
            for point in result.drawdown_curve
        ],
        trades=[
            BacktestTradeResponse(
                trade_id=f"trade_{trade.trade_id:04d}",
                legacy_trade_id=trade.trade_id,
                side="long",
                entry_date=trade.entry_date,
                exit_date=trade.exit_date,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                shares=max(0, int(trade.quantity)),
                quantity=trade.quantity,
                gross_pnl=trade.gross_pnl,
                net_pnl=trade.net_pnl,
                return_pct=trade.return_pct,
                holding_period_bars=trade.holding_period_bars,
                entry_reason=trade.entry_reason,
                exit_reason=trade.exit_reason,
                entry_commission=0.0,
                exit_commission=0.0,
                commission_paid=trade.commission_paid,
                slippage_paid=trade.slippage_paid,
            )
            for trade in result.trades
        ],
        signals=[
            BacktestSignalPointResponse(
                signal_id=f"signal_{index + 1:04d}",
                date=signal.date,
                entry_signal=signal.entry_signal,
                exit_signal=signal.exit_signal,
                entry_reason=signal.entry_reason,
                exit_reason=signal.exit_reason,
                executed_order=signal.executed_order,
                side=_signal_side(signal.executed_order),
                reason=signal.entry_reason or signal.exit_reason,
                status="executed"
                if signal.executed_order
                else "scheduled"
                if signal.entry_signal or signal.exit_signal
                else "none",
                details={},
            )
            for index, signal in enumerate(result.signals)
        ],
        warnings=[
            BacktestWarningResponse(
                code=warning.code,
                severity=warning.severity,
                message=warning.message,
                context=warning.context,
            )
            for warning in result.warnings
        ],
        agent_steps=[
            _agent_step_response(index, step) for index, step in enumerate(result.agent_steps)
        ],
    )


def _signal_side(executed_order: str | None) -> str | None:
    if executed_order == "entry":
        return "buy"
    if executed_order == "exit":
        return "sell"
    return None


def _agent_step_response(index: int, step) -> BacktestAgentStepResponse:
    definition = workflow_step_definition(step.key)
    return BacktestAgentStepResponse(
        sequence=definition.sequence if definition else index + 1,
        key=step.key,
        label=definition.label if definition else step.key.replace("_", " ").title(),
        description=(
            definition.description
            if definition
            else "Custom engine step returned by the backtest service."
        ),
        status=step.status,
        message=step.message,
        detail=step.detail,
        duration_ms=None,
    )
