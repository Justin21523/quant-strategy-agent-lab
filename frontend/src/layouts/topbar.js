import { createStatusPill } from "../components/status-pill.js";
import { createElement } from "../core/dom.js";

const pageTitles = {
  "/": "Research Demo",
  "/research-lab": "Research Lab",
  "/market-data": "Market Data Lab",
  "/strategy-builder": "Strategy Builder",
  "/backtest-lab": "Backtest Lab",
  "/agent-workflow": "Agent Workflow",
  "/performance-report": "Performance Report",
  "/parameter-scanner": "Stock Scanner",
  "/data-quality": "Data Quality",
  "/portfolio-rebalance": "Portfolio Rebalance",
  "/jobs": "Jobs",
  "/comparison": "Multi-Asset Comparison",
  "/report-center": "Report Center",
};

export function createTopbar({ apiDocsUrl, onGuideClick = () => {} }) {
  const title = createElement("h2", { text: pageTitles["/"] });
  const apiStatus = createStatusPill({ status: "checking", label: "API checking" });
  const latency = createElement("span", { className: "topbar__latency", text: "" });
  const guideButton = createElement("button", {
    className: "button button--secondary button--small",
    text: "Guide",
    attributes: { type: "button", "data-testid": "open-site-guide" },
    on: { click: onGuideClick },
  });
  const element = createElement("header", {
    className: "topbar",
    attributes: { "data-guide": "shell-topbar" },
    children: [
      createElement("div", {
        children: [
          createElement("span", { className: "eyebrow", text: "Quant Strategy Agent Lab" }),
          title,
        ],
      }),
      createElement("div", {
        className: "topbar__actions",
        children: [
          apiStatus.element,
          latency,
          guideButton,
          createElement("a", {
            className: "button button--secondary button--small",
            text: "API Docs ↗",
            attributes: { href: apiDocsUrl, target: "_blank", rel: "noreferrer" },
          }),
        ],
      }),
    ],
  });

  return {
    element,
    update(state) {
      title.textContent = pageTitles[state.route] ?? "Not Found";
      apiStatus.update({ status: state.api.status, label: state.api.message });
      latency.textContent = state.api.latencyMs === null ? "" : `${state.api.latencyMs} ms`;
    },
  };
}
