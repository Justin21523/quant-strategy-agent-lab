import { ApiError } from "../core/api-client.js";
import { createElement } from "../core/dom.js";
import { portfolioService } from "../services/portfolio-service.js";
import { formatInteger } from "../utils/market-formatters.js";

function errorMessage(error) {
  if (error instanceof ApiError) return error.details?.error?.message ?? error.message;
  return error?.message ?? "Unexpected performance error.";
}

function pct(value) {
  return Number.isFinite(Number(value)) ? `${Number(value).toFixed(2)}%` : "-";
}

function metricCard(label, value) {
  return createElement("article", {
    className: "metric-card",
    children: [
      createElement("span", { className: "metric-card__label", text: label }),
      createElement("strong", { text: String(value) }),
    ],
  });
}

export function createPerformanceReportPage() {
  let destroyed = false;
  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Load a portfolio run to inspect performance metrics.",
  });
  const runSelect = createElement("select", {
    className: "form-control",
    attributes: { "aria-label": "Portfolio run", "data-testid": "performance-run-select" },
  });
  const loadButton = createElement("button", {
    className: "button button--primary",
    text: "Load report",
    attributes: { type: "button", "data-testid": "load-performance-report-button" },
  });
  const summary = createElement("div", {
    className: "metric-grid",
    attributes: { "data-testid": "performance-summary" },
  });
  const monthlyBody = createElement("tbody");

  const element = createElement("section", {
    className: "page performance-report-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Performance" }),
          createElement("h1", { text: "Portfolio performance analyzer." }),
          createElement("p", {
            text: "Review CAGR, volatility, Sharpe, Sortino, Calmar, drawdown, monthly returns, and benchmark comparison.",
          }),
        ],
      }),
      activity,
      createElement("section", {
        className: "panel",
        children: [
          createElement("div", {
            className: "form-grid",
            children: [
              createElement("label", {
                className: "form-field",
                children: [
                  createElement("span", { className: "form-field__label", text: "Portfolio run" }),
                  runSelect,
                ],
              }),
            ],
          }),
          createElement("div", { className: "form-actions", children: [loadButton] }),
        ],
      }),
      summary,
      createElement("section", {
        className: "panel",
        children: [
          createElement("div", {
            className: "panel__header",
            children: [
              createElement("div", {
                children: [
                  createElement("span", { className: "eyebrow", text: "Calendar" }),
                  createElement("h2", { text: "Monthly returns" }),
                ],
              }),
            ],
          }),
          createElement("div", {
            className: "table-scroll",
            children: [
              createElement("table", {
                className: "data-table",
                children: [
                  createElement("thead", {
                    children: [
                      createElement("tr", {
                        children: ["Year", "Month", "Return"].map((text) =>
                          createElement("th", { text }),
                        ),
                      }),
                    ],
                  }),
                  monthlyBody,
                ],
              }),
            ],
          }),
        ],
      }),
    ],
  });

  function setActivity(status, message) {
    activity.dataset.status = status;
    activity.textContent = message;
  }

  async function loadRuns() {
    try {
      const response = await portfolioService.listRuns({ limit: 30 });
      if (destroyed) return;
      runSelect.replaceChildren(
        ...response.runs.map((run) =>
          createElement("option", {
            text: `${run.run_id} (${run.status})`,
            attributes: { value: run.run_id },
          }),
        ),
      );
      setActivity("success", `${formatInteger(response.total)} portfolio runs loaded.`);
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    }
  }

  async function loadReport() {
    if (!runSelect.value) return;
    try {
      setActivity("loading", `Loading ${runSelect.value}...`);
      const run = await portfolioService.getRun(runSelect.value);
      if (destroyed) return;
      const performance = run.performance ?? {};
      const benchmark = run.benchmark ?? {};
      summary.replaceChildren(
        metricCard("Total return", pct(performance.total_return_pct)),
        metricCard("CAGR", pct(performance.cagr_pct)),
        metricCard("Annual vol", pct(performance.annual_volatility_pct)),
        metricCard("Sharpe", performance.sharpe_ratio?.toFixed?.(2) ?? "-"),
        metricCard("Sortino", performance.sortino_ratio?.toFixed?.(2) ?? "-"),
        metricCard("Calmar", performance.calmar_ratio?.toFixed?.(2) ?? "-"),
        metricCard("Max DD", pct(performance.max_drawdown_pct)),
        metricCard("Benchmark", pct(benchmark.total_return_pct)),
      );
      monthlyBody.replaceChildren(
        ...(performance.monthly_returns ?? []).map((item) =>
          createElement("tr", {
            children: [
              createElement("td", { text: String(item.year) }),
              createElement("td", { text: String(item.month).padStart(2, "0") }),
              createElement("td", { text: pct(item.return_pct) }),
            ],
          }),
        ),
      );
      setActivity("success", `${run.run_id} performance loaded.`);
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    }
  }

  loadButton.addEventListener("click", loadReport);
  loadRuns();

  return {
    element,
    destroy() {
      destroyed = true;
    },
  };
}
