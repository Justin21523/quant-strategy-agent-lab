import { createAgentTimeline } from "../components/agent-timeline.js";
import { createMetricCard } from "../components/metric-card.js";
import { createElement } from "../core/dom.js";

function architectureRow(title, detail) {
  return createElement("div", {
    className: "architecture-row",
    children: [createElement("strong", { text: title }), createElement("span", { text: detail })],
  });
}

export function createDashboardPage() {
  return createElement("section", {
    className: "page dashboard-page",
    children: [
      createElement("section", {
        className: "hero",
        children: [
          createElement("div", {
            className: "hero__content",
            children: [
              createElement("span", {
                className: "eyebrow",
                text: "Phase 4 · Backtest engine online",
              }),
              createElement("h1", {
                text: "Strategy research now executes reproducible backtests.",
              }),
              createElement("p", {
                text: "The workbench now renders safe Strategy JSON DSL, generates signals, executes long-only backtests, and returns trades, equity, drawdown, metrics, and Agent steps.",
              }),
              createElement("div", {
                className: "hero__actions",
                children: [
                  createElement("a", {
                    className: "button button--primary",
                    text: "Run Backtest Lab",
                    attributes: { href: "#/backtest-lab" },
                  }),
                  createElement("a", {
                    className: "button button--secondary",
                    text: "Inspect Market + Indicators",
                    attributes: { href: "#/market-data" },
                  }),
                ],
              }),
            ],
          }),
          createElement("div", {
            className: "hero__visual",
            attributes: { "aria-hidden": "true" },
            children: [
              createElement("div", { className: "market-grid" }),
              createElement("div", {
                className: "terminal-card",
                children: [
                  createElement("span", { text: "$ make check" }),
                  createElement("span", { text: "✓ Provider adapters" }),
                  createElement("span", { text: "✓ SQLite cache" }),
                  createElement("span", { text: "✓ Backtest engine tests" }),
                  createElement("strong", { text: "Phase 4 ready" }),
                ],
              }),
            ],
          }),
        ],
      }),
      createElement("div", {
        className: "metric-grid",
        children: [
          createMetricCard({
            label: "Current phase",
            value: "4 / 13",
            meta: "Backtest Engine",
            tone: "accent",
          }),
          createMetricCard({
            label: "Offline catalog",
            value: "3 assets",
            meta: "AAPL · SPY · QQQ",
          }),
          createMetricCard({
            label: "Persistence",
            value: "SQLite",
            meta: "Normalized daily OHLCV",
          }),
          createMetricCard({
            label: "Current features",
            value: "Backtests",
            meta: "Trades · Equity · Drawdown",
            tone: "muted",
          }),
        ],
      }),
      createElement("div", {
        className: "content-grid content-grid--two",
        children: [
          createElement("article", {
            className: "panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Feature pipeline" }),
                      createElement("h2", { text: "Template-to-backtest execution path" }),
                    ],
                  }),
                  createElement("span", { className: "phase-chip", text: "Phase 04" }),
                ],
              }),
              createElement("div", {
                className: "architecture-stack",
                children: [
                  architectureRow("Provider", "CSV · yfinance · FinMind boundary"),
                  architectureRow("Normalize", "SQLite OHLCV · sorted · validated · cached"),
                  architectureRow("Compute", "SMA · EMA · RSI · MACD · Bollinger Bands · ATR"),
                  architectureRow(
                    "Execute",
                    "Signals · next-open fills · trade ledger · equity and drawdown",
                  ),
                ],
              }),
            ],
          }),
          createElement("article", {
            className: "panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Agent-ready workflow" }),
                      createElement("h2", {
                        text: "Backtesting becomes the fourth Agent tool",
                      }),
                    ],
                  }),
                ],
              }),
              createAgentTimeline([
                ["Market data loaded", "Provider, range, adjustment, and fixture status"],
                ["Indicators built", "Phase 2 computes tested technical features"],
                [
                  "Strategy rendered",
                  "Phase 3 produces controlled JSON DSL instead of arbitrary code",
                ],
                ["Backtest executed", "Explicit fees, slippage, and timing assumptions"],
                ["Risk explained", "Evidence-based report with source lineage"],
              ]),
            ],
          }),
        ],
      }),
      createElement("aside", {
        className: "disclaimer",
        children: [
          createElement("strong", { text: "Research boundary" }),
          createElement("p", {
            text: "The bundled CSV dataset is synthetic and exists only for deterministic offline development. Historical data and backtests do not guarantee future performance. This project does not provide investment advice.",
          }),
        ],
      }),
    ],
  });
}
