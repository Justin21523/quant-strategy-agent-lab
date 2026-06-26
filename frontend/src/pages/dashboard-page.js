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
              createElement("span", { className: "eyebrow", text: "Phase 1 · Data layer online" }),
              createElement("h1", {
                text: "Reliable strategy research starts with visible data lineage.",
              }),
              createElement("p", {
                text: "The workbench now provides a provider boundary, normalization pipeline, SQLite OHLCV cache, deterministic offline fixtures, optional yfinance synchronization, typed API contracts, and a raw-data inspection page.",
              }),
              createElement("div", {
                className: "hero__actions",
                children: [
                  createElement("a", {
                    className: "button button--primary",
                    text: "Open Market Data Lab",
                    attributes: { href: "#/market-data" },
                  }),
                  createElement("a", {
                    className: "button button--secondary",
                    text: "Inspect Strategy DSL",
                    attributes: { href: "#/strategy-builder" },
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
                  createElement("span", { text: "✓ Market API tests" }),
                  createElement("strong", { text: "Phase 1 ready" }),
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
            value: "1 / 13",
            meta: "Market Data Layer",
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
            label: "Next phase",
            value: "Indicators",
            meta: "SMA · EMA · RSI · MACD",
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
                      createElement("span", { className: "eyebrow", text: "Data pipeline" }),
                      createElement("h2", { text: "One schema across providers" }),
                    ],
                  }),
                  createElement("span", { className: "phase-chip", text: "Phase 01" }),
                ],
              }),
              createElement("div", {
                className: "architecture-stack",
                children: [
                  architectureRow("Provider", "CSV · yfinance · FinMind boundary"),
                  architectureRow("Normalize", "types · ordering · duplicates · OHLC rules"),
                  architectureRow("Persist", "SQLite cache · source metadata · sync audit"),
                  architectureRow("Expose", "symbols · OHLCV · sync · typed warnings"),
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
                      createElement("span", { className: "eyebrow", text: "Future workflow" }),
                      createElement("h2", { text: "Data remains the first Agent tool" }),
                    ],
                  }),
                ],
              }),
              createAgentTimeline([
                ["Market data loaded", "Provider, range, adjustment, and fixture status"],
                ["Indicators built", "Phase 2 computes tested technical features"],
                ["Strategy validated", "Controlled JSON DSL instead of arbitrary code"],
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
