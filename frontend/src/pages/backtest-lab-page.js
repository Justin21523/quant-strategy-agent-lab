import { createComingSoonPage } from "../components/coming-soon.js";

export function createBacktestLabPage() {
  return createComingSoonPage({
    phase: 4,
    title: "Backtest Lab",
    description: "Execute one validated strategy against one asset and inspect every assumption.",
    deliverables: [
      "Symbol, date, capital, fee, and slippage controls",
      "Candles with entry and exit markers",
      "Equity and drawdown series",
      "Trade ledger and Agent steps",
    ],
  });
}
