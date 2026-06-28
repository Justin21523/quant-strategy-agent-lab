import { ApiError } from "../core/api-client.js";
import { createElement } from "../core/dom.js";
import { multiBacktestService } from "../services/multi-backtest-service.js";
import { scannerService } from "../services/scanner-service.js";
import { strategyService } from "../services/strategy-service.js";
import { formatInteger } from "../utils/market-formatters.js";

function errorMessage(error) {
  if (error instanceof ApiError) return error.details?.error?.message ?? error.message;
  return error?.message ?? "Unexpected multi-asset backtest error.";
}

function field(label, control, helpText = "") {
  return createElement("label", {
    className: "form-field",
    children: [
      createElement("span", { className: "form-field__label", text: label }),
      control,
      helpText ? createElement("small", { text: helpText }) : null,
    ],
  });
}

function input(type, value, attributes = {}) {
  return createElement("input", {
    className: "form-control",
    attributes: { type, value, ...attributes },
  });
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

function pct(value) {
  return Number.isFinite(Number(value)) ? `${Number(value).toFixed(2)}%` : "-";
}

export function createComparisonPage() {
  let destroyed = false;
  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Select a saved scan run and strategy template to compare symbols.",
  });
  const scanSelect = createElement("select", {
    className: "form-control",
    attributes: { name: "scanRun", "aria-label": "Scan run" },
  });
  const templateSelect = createElement("select", {
    className: "form-control",
    attributes: { name: "template", "aria-label": "Strategy template" },
  });
  const topNInput = input("number", "10", { min: "1", max: "100" });
  const startInput = input("date", "2023-01-03");
  const endInput = input("date", "2025-12-31");
  const cashInput = input("number", "100000", { min: "1", step: "1000" });
  const commissionInput = input("number", "0.001", { min: "0", step: "0.0001" });
  const slippageInput = input("number", "0.0005", { min: "0", step: "0.0001" });
  const parametersInput = createElement("textarea", {
    className: "form-control",
    text: "{}",
    attributes: { rows: "5", spellcheck: "false" },
  });
  const runButton = createElement("button", {
    className: "button button--primary",
    text: "Run multi-asset backtest",
    attributes: { type: "button" },
  });
  const summary = createElement("div", { className: "metric-grid" });
  const tableBody = createElement("tbody");
  const caption = createElement("p", {
    className: "table-caption",
    text: "No multi-asset run loaded.",
  });

  const element = createElement("section", {
    className: "page comparison-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Multi-Asset Backtest" }),
          createElement("h1", { text: "Run one strategy across scanner candidates." }),
          createElement("p", {
            text: "Use saved scanner results as a candidate list, then compare the same template across the top ranked symbols.",
          }),
        ],
      }),
      activity,
      createElement("section", {
        className: "panel",
        children: [
          createElement("div", {
            className: "panel__header",
            children: [
              createElement("div", {
                children: [
                  createElement("span", { className: "eyebrow", text: "Run setup" }),
                  createElement("h2", { text: "Scanner source and strategy" }),
                ],
              }),
              createElement("span", { className: "phase-chip", text: "Batch" }),
            ],
          }),
          createElement("div", {
            className: "form-grid",
            children: [
              field("Scan run", scanSelect),
              field("Template", templateSelect),
              field("Top N", topNInput),
              field("Start", startInput),
              field("End", endInput),
              field("Initial cash", cashInput),
              field("Commission", commissionInput),
              field("Slippage", slippageInput),
            ],
          }),
          field("Template parameters JSON", parametersInput, "Leave {} to use template defaults."),
          createElement("div", { className: "form-actions", children: [runButton] }),
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
                  createElement("span", { className: "eyebrow", text: "Ranking" }),
                  createElement("h2", { text: "Per-symbol performance" }),
                ],
              }),
            ],
          }),
          caption,
          createElement("div", {
            className: "table-scroll",
            children: [
              createElement("table", {
                className: "data-table",
                children: [
                  createElement("thead", {
                    children: [
                      createElement("tr", {
                        children: [
                          "Rank",
                          "Symbol",
                          "Status",
                          "Return",
                          "Max DD",
                          "Sharpe",
                          "Win rate",
                          "Trades",
                          "Warnings",
                          "Error",
                        ].map((text) => createElement("th", { text })),
                      }),
                    ],
                  }),
                  tableBody,
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

  function setBusy(isBusy) {
    for (const control of element.querySelectorAll("button,input,select,textarea")) {
      control.disabled = isBusy;
    }
  }

  function renderRun(run) {
    const aggregate = run.aggregate ?? {};
    summary.replaceChildren(
      metricCard("Status", run.status),
      metricCard("Success", `${run.successful_symbols}/${run.requested_symbols}`),
      metricCard("Avg return", pct(aggregate.average_total_return_pct)),
      metricCard("Avg max DD", pct(aggregate.average_max_drawdown_pct)),
      metricCard("Best", aggregate.best_symbol ?? "-"),
      metricCard("Worst", aggregate.worst_symbol ?? "-"),
    );
    tableBody.replaceChildren(
      ...[...(run.results ?? [])]
        .sort(
          (left, right) =>
            Number(right.metrics?.total_return_pct ?? -Infinity) -
            Number(left.metrics?.total_return_pct ?? -Infinity),
        )
        .map((result, index) => {
          const metrics = result.metrics ?? {};
          return createElement("tr", {
            children: [
              createElement("td", { text: String(index + 1) }),
              createElement("td", { text: result.symbol }),
              createElement("td", { text: result.status }),
              createElement("td", { text: pct(metrics.total_return_pct) }),
              createElement("td", { text: pct(metrics.max_drawdown_pct) }),
              createElement("td", { text: metrics.sharpe_ratio?.toFixed?.(2) ?? "-" }),
              createElement("td", { text: pct(metrics.win_rate_pct) }),
              createElement("td", { text: formatInteger(metrics.trade_count ?? 0) }),
              createElement("td", { text: (result.warnings ?? []).join(", ") || "-" }),
              createElement("td", { text: result.error ?? "-" }),
            ],
          });
        }),
    );
    caption.textContent = `${run.run_id}: ${formatInteger(run.results.length)} symbols ranked.`;
  }

  async function loadOptions() {
    try {
      const [scans, templates] = await Promise.all([
        scannerService.list({ limit: 30 }),
        strategyService.getTemplates(),
      ]);
      if (destroyed) return;
      scanSelect.replaceChildren(
        ...scans.runs.map((run) =>
          createElement("option", {
            text: `${run.run_id} (${run.matched_symbols} matched)`,
            attributes: { value: run.run_id },
          }),
        ),
      );
      templateSelect.replaceChildren(
        ...templates.templates.map((template) =>
          createElement("option", {
            text: template.name,
            attributes: { value: template.id },
          }),
        ),
      );
      setActivity("success", "Saved scans and strategy templates loaded.");
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    }
  }

  async function runComparison() {
    setBusy(true);
    setActivity("loading", "Running multi-asset backtest...");
    try {
      const parameters = JSON.parse(parametersInput.value || "{}");
      const run = await multiBacktestService.run({
        scan_run_id: scanSelect.value,
        template_id: templateSelect.value,
        parameters,
        top_n: Number(topNInput.value || 10),
        start: startInput.value,
        end: endInput.value,
        initial_cash: Number(cashInput.value || 100000),
        commission: Number(commissionInput.value || 0),
        slippage: Number(slippageInput.value || 0),
      });
      if (destroyed) return;
      renderRun(run);
      setActivity(
        run.failed_symbols ? "warning" : "success",
        `${run.run_id}: ${run.successful_symbols} success, ${run.failed_symbols} failed.`,
      );
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  runButton.addEventListener("click", runComparison);
  loadOptions();

  return {
    element,
    destroy() {
      destroyed = true;
    },
  };
}
