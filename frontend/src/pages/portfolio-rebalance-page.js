import { ApiError } from "../core/api-client.js";
import { createElement } from "../core/dom.js";
import { jobService } from "../services/job-service.js";
import { portfolioService } from "../services/portfolio-service.js";
import { scannerService } from "../services/scanner-service.js";
import { formatInteger } from "../utils/market-formatters.js";

function errorMessage(error) {
  if (error instanceof ApiError) return error.details?.error?.message ?? error.message;
  return error?.message ?? "Unexpected portfolio error.";
}

function field(label, control) {
  return createElement("label", {
    className: "form-field",
    children: [createElement("span", { className: "form-field__label", text: label }), control],
  });
}

function input(type, value, attributes = {}) {
  return createElement("input", {
    className: "form-control",
    attributes: { type, value, ...attributes },
  });
}

function select(options = []) {
  return createElement("select", {
    className: "form-control",
    children: options.map(([value, label]) =>
      createElement("option", { text: label, attributes: { value } }),
    ),
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

export function createPortfolioRebalancePage() {
  let destroyed = false;
  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Queue a portfolio rebalance job from scanner presets or a fixed scan run.",
  });
  const presetSelect = select();
  const modeSelect = select([
    ["rescan_each_period", "Rescan each period"],
    ["fixed_scan_run", "Fixed scan run"],
  ]);
  const scanSelect = select();
  const frequencySelect = select([
    ["monthly", "Monthly"],
    ["weekly", "Weekly"],
  ]);
  const topNInput = input("number", "20", { min: "1", max: "100" });
  const startInput = input("date", "2023-01-03");
  const endInput = input("date", "2025-12-31");
  const lookbackInput = input("number", "365", { min: "30", max: "1500" });
  const cashInput = input("number", "100000", { min: "1", step: "1000" });
  const benchmarkInput = input("text", "SPY");
  const minBarsInput = input("number", "0", { min: "0" });
  const allowFixtureInput = input("checkbox", "");
  allowFixtureInput.checked = true;
  presetSelect.dataset.testid = "portfolio-preset-select";
  modeSelect.dataset.testid = "portfolio-selection-mode";
  frequencySelect.dataset.testid = "portfolio-frequency-select";
  topNInput.dataset.testid = "portfolio-top-n-input";
  startInput.dataset.testid = "portfolio-start-input";
  endInput.dataset.testid = "portfolio-end-input";
  minBarsInput.dataset.testid = "portfolio-min-bars-input";
  const runButton = createElement("button", {
    className: "button button--primary",
    text: "Queue portfolio job",
    attributes: { type: "button", "data-testid": "queue-portfolio-button" },
  });
  const summary = createElement("div", { className: "metric-grid" });
  const runsBody = createElement("tbody");

  const element = createElement("section", {
    className: "page portfolio-rebalance-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Portfolio" }),
          createElement("h1", { text: "Scanner-driven portfolio rebalance." }),
          createElement("p", {
            text: "Queue equal-weight weekly or monthly portfolio simulations from scanner presets or saved scan runs.",
          }),
        ],
      }),
      activity,
      createElement("section", {
        className: "panel",
        attributes: { "data-guide": "portfolio-workbench" },
        children: [
          createElement("div", {
            className: "panel__header",
            children: [
              createElement("div", {
                children: [
                  createElement("span", { className: "eyebrow", text: "Setup" }),
                  createElement("h2", { text: "Rebalance configuration" }),
                ],
              }),
              createElement("span", { className: "phase-chip", text: "Job" }),
            ],
          }),
          createElement("div", {
            className: "form-grid",
            children: [
              field("Portfolio preset", presetSelect),
              field("Selection mode", modeSelect),
              field("Fixed scan run", scanSelect),
              field("Frequency", frequencySelect),
              field("Top N", topNInput),
              field("Start", startInput),
              field("End", endInput),
              field("Lookback days", lookbackInput),
              field("Initial cash", cashInput),
              field("Benchmark", benchmarkInput),
              field("Min bars", minBarsInput),
              field(
                "Allow fixture data",
                createElement("label", {
                  className: "checkbox-field",
                  children: [allowFixtureInput, createElement("span", { text: "Enabled" })],
                }),
              ),
            ],
          }),
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
                  createElement("span", { className: "eyebrow", text: "Runs" }),
                  createElement("h2", { text: "Recent portfolio runs" }),
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
                        children: [
                          "Run",
                          "Status",
                          "Mode",
                          "Frequency",
                          "Final equity",
                          "Return",
                          "Max DD",
                          "Rebalances",
                        ].map((text) => createElement("th", { text })),
                      }),
                    ],
                  }),
                  runsBody,
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
    for (const control of element.querySelectorAll("button,input,select")) {
      control.disabled = isBusy;
    }
  }

  function applyPreset() {
    const preset = (presetSelect._presets ?? []).find(
      (item) => item.preset_id === presetSelect.value,
    );
    if (!preset) return;
    modeSelect.value = preset.config.selection_mode ?? "rescan_each_period";
    frequencySelect.value = preset.config.frequency ?? "monthly";
    topNInput.value = preset.config.top_n ?? 20;
    lookbackInput.value = preset.config.lookback_days ?? 365;
  }

  async function loadOptions() {
    try {
      const [presets, scans] = await Promise.all([
        portfolioService.listPresets(),
        scannerService.list({ limit: 30 }),
      ]);
      if (destroyed) return;
      presetSelect._presets = presets.presets;
      presetSelect.replaceChildren(
        ...presets.presets.map((preset) =>
          createElement("option", {
            text: preset.name,
            attributes: { value: preset.preset_id },
          }),
        ),
      );
      scanSelect.replaceChildren(
        createElement("option", { text: "None", attributes: { value: "" } }),
        ...scans.runs.map((run) =>
          createElement("option", {
            text: `${run.run_id} (${run.matched_symbols})`,
            attributes: { value: run.run_id },
          }),
        ),
      );
      applyPreset();
      setActivity("success", "Portfolio presets loaded.");
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    }
  }

  async function loadRuns() {
    const response = await portfolioService.listRuns({ limit: 20 });
    if (destroyed) return;
    runsBody.replaceChildren(...response.runs.map(runRow));
    summary.replaceChildren(
      metricCard("Runs", formatInteger(response.total)),
      metricCard("Latest", response.runs[0]?.run_id ?? "-"),
      metricCard("Status", response.runs[0]?.status ?? "-"),
      metricCard("Final", response.runs[0]?.aggregate?.final_equity?.toFixed?.(2) ?? "-"),
    );
  }

  function runRow(run) {
    return createElement("tr", {
      children: [
        createElement("td", { text: run.run_id }),
        createElement("td", { text: run.status }),
        createElement("td", { text: run.selection_mode }),
        createElement("td", { text: run.frequency }),
        createElement("td", { text: run.aggregate?.final_equity?.toFixed?.(2) ?? "-" }),
        createElement("td", { text: pct(run.performance?.total_return_pct) }),
        createElement("td", { text: pct(run.performance?.max_drawdown_pct) }),
        createElement("td", { text: formatInteger(run.aggregate?.rebalance_count ?? 0) }),
      ],
    });
  }

  async function queueRun() {
    setBusy(true);
    setActivity("loading", "Queueing portfolio rebalance job...");
    try {
      const preset = (presetSelect._presets ?? []).find(
        (item) => item.preset_id === presetSelect.value,
      );
      const job = await jobService.queuePortfolio({
        selection_mode: modeSelect.value,
        universe_id: "us_common_stocks",
        scanner_preset_id: preset?.config?.scanner_preset_id ?? "trend_momentum",
        fixed_scan_run_id: scanSelect.value || null,
        frequency: frequencySelect.value,
        top_n: Number(topNInput.value || 20),
        start: startInput.value,
        end: endInput.value,
        lookback_days: Number(lookbackInput.value || 365),
        initial_cash: Number(cashInput.value || 100000),
        benchmark_symbol: benchmarkInput.value || "SPY",
        quality_gate: {
          min_bars: Number(minBarsInput.value || 0),
          allow_fixture_data: allowFixtureInput.checked,
        },
      });
      setActivity("success", `${job.job_id} queued. Open Jobs to watch progress.`);
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  presetSelect.addEventListener("change", applyPreset);
  runButton.addEventListener("click", queueRun);
  loadOptions();
  loadRuns().catch((error) => setActivity("error", errorMessage(error)));

  return {
    element,
    destroy() {
      destroyed = true;
    },
  };
}
