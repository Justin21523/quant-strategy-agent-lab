# Backtest Engine — Phase 4 MVP

Phase 4 adds a deterministic long-only backtest engine that executes validated Strategy JSON DSL documents produced by the Phase 3 template system.

The MVP intentionally avoids arbitrary Python strategy execution and does not depend on `backtesting.py` yet. This keeps the first execution layer small, readable, testable, and safe. A later phase can add `backtesting.py` or `vectorbt` adapters behind the same Strategy JSON contract.

## Engine pipeline

```text
Strategy JSON DSL
  ↓
Backend Strategy DSL validation
  ↓
MarketDataService cached OHLCV load
  ↓
Feature frame build
  ↓
Indicator computation from Strategy JSON requirements
  ↓
Entry / exit signal generation
  ↓
Long-only execution engine
  ↓
Trade ledger
  ↓
Equity curve and drawdown curve
  ↓
Metrics and Agent-style execution steps
```

## Supported Strategy JSON condition types

```text
ENTER_ON_FIRST_BAR
EXIT_ON_LAST_BAR
CROSSOVER
CROSSUNDER
LESS_THAN
LESS_THAN_OR_EQUAL
GREATER_THAN
GREATER_THAN_OR_EQUAL
```

`CROSSOVER` and `CROSSUNDER` compare the current completed bar against the previous completed bar.

## Supported indicators inside backtests

```text
SMA
EMA
RSI
MACD
BOLLINGER_BANDS / BBANDS
ATR
```

Indicator output naming follows the Strategy JSON DSL:

```text
single-output indicators use their indicator id
MACD uses <id>.line, <id>.signal, <id>.histogram
Bollinger Bands uses <id>.middle, <id>.upper, <id>.lower
```

## Execution assumptions

The response includes assumptions explicitly, but the core MVP semantics are:

```text
timeframe: daily bars only
position model: long-only
max positions: 1
normal signal timing: completed bar
normal fill timing: next bar open
Buy and Hold first entry: first bar open
final liquidation: final bar close
commission: percentage of notional
slippage: percentage fill adjustment
position sizing: cash * max_position_pct
```

This avoids look-ahead bias by never using a bar's close signal to fill on the same bar open. The one exception is the explicit `ENTER_ON_FIRST_BAR` primitive used by the Buy and Hold template.

## Risk rules

The engine currently supports:

```text
stop_loss_pct
take_profit_pct
max_position_pct
```

Stop-loss and take-profit checks are evaluated against each daily bar's low/high while a position is open. In Phase 4 they close on the next open unless the rule occurs on the final bar, where final liquidation logic applies.

## Trade ledger

Each closed trade includes:

```text
trade_id
side
entry_date
exit_date
entry_price
exit_price
quantity
gross_pnl
net_pnl
return_pct
holding_period_bars
entry_reason
exit_reason
commission_paid
slippage_paid
```

## Equity and drawdown

The engine returns one equity point per input OHLCV bar:

```text
date
equity
cash
position_value
drawdown_pct
in_position
```

The drawdown curve is derived from the running high-water mark.

## Metrics

Phase 4 returns:

```text
total_return_pct
annual_return_pct
sharpe_ratio
max_drawdown_pct
win_rate_pct
profit_factor
trade_count
exposure_time_pct
average_trade_return_pct
final_equity
```

More advanced metrics are reserved for Phase 7.

## Warnings

The engine emits warnings such as:

```text
synthetic_fixture_data
forced_final_liquidation
entry_signal_on_final_bar_skipped
no_closed_trades
```

Warnings are part of the API contract and should be displayed by the UI.

## Limitations

Phase 4 intentionally does not support:

```text
short selling
leverage
partial fills
limit orders
intraday bars
portfolio-level multi-asset execution
vectorized parameter scanning
benchmark comparison
advanced risk analytics
LLM explanation
```

Those items belong to later roadmap phases.
