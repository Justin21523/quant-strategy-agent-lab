import { createComingSoonPage } from "../components/coming-soon.js";

export function createPerformanceReportPage() {
  return createComingSoonPage({
    phase: 7,
    title: "Performance Report",
    description:
      "Risk-adjusted metrics, trade behavior, assumptions, and failure-mode explanations.",
    deliverables: [
      "CAGR, volatility, Sharpe, Sortino, Calmar, max drawdown",
      "Win/loss distribution and profit factor",
      "Benchmark comparison",
      "Metric definitions and interpretation tooltips",
    ],
  });
}
