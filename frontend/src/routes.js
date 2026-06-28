import { createDashboardPage } from "./pages/dashboard-page.js";
import { createPlaceholderPage } from "./pages/placeholder-page.js";

export const routes = [
  {
    path: "/",
    label: "Overview",
    eyebrow: "Phase 0",
    render: createDashboardPage,
  },
  {
    path: "/strategy-builder",
    label: "Strategy Builder",
    eyebrow: "Phase 3 / 9",
    render: (context) =>
      createPlaceholderPage({
        ...context,
        title: "Strategy Builder",
        description: "Template-driven rules and the constrained Strategy JSON DSL will live here.",
        phase: "Phase 3 and Phase 9",
      }),
  },
  {
    path: "/backtest-lab",
    label: "Backtest Lab",
    eyebrow: "Phase 4 / 5",
    render: (context) =>
      createPlaceholderPage({
        ...context,
        title: "Backtest Lab",
        description:
          "Market data, signals, transaction costs, trades, and equity curves will meet here.",
        phase: "Phase 4 and Phase 5",
      }),
  },
  {
    path: "/performance",
    label: "Performance",
    eyebrow: "Phase 7",
    render: (context) =>
      createPlaceholderPage({
        ...context,
        title: "Performance Report",
        description:
          "Risk-adjusted metrics, drawdowns, trade behavior, and assumptions will be explained here.",
        phase: "Phase 7",
      }),
  },
  {
    path: "/parameter-scanner",
    label: "Scanner",
    eyebrow: "Phase 7A",
    render: (context) =>
      createPlaceholderPage({
        ...context,
        title: "Stock Scanner",
        description: "Universe-based technical scanning for cached market data belongs here.",
        phase: "Phase 7A",
      }),
  },
  {
    path: "/data-quality",
    label: "Data Quality",
    eyebrow: "Phase 8A",
    render: (context) =>
      createPlaceholderPage({
        ...context,
        title: "Data Quality",
        description: "Universe cache coverage, missing bars, and indicator readiness live here.",
        phase: "Phase 8A",
      }),
  },
  {
    path: "/comparison",
    label: "Multi-Asset",
    eyebrow: "Phase 8A",
    render: (context) =>
      createPlaceholderPage({
        ...context,
        title: "Multi-Asset Comparison",
        description:
          "Batch runs and risk-return comparisons will test whether a strategy generalizes.",
        phase: "Phase 8A",
      }),
  },
  {
    path: "/reports",
    label: "Report Center",
    eyebrow: "Phase 12",
    render: (context) =>
      createPlaceholderPage({
        ...context,
        title: "Report Center",
        description:
          "Reproducible Markdown, JSON, and CSV research exports will be generated here.",
        phase: "Phase 12",
      }),
  },
];
