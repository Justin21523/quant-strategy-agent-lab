import { createElement } from "../core/dom.js";
import { researchService } from "../services/research-service.js";

const EXPORTS = [
  ["summary", "json", "Summary JSON"],
  ["scanner", "csv", "Scanner CSV"],
  ["quality", "csv", "Quality CSV"],
  ["portfolio", "csv", "Portfolio CSV"],
  ["strategy", "csv", "Strategy CSV"],
];

function queryRunId() {
  const query = window.location.hash.split("?")[1] ?? "";
  return new URLSearchParams(query).get("run");
}

function optionForRun(summary) {
  return createElement("option", {
    attributes: { value: summary.run_id },
    text: `${summary.run_label ?? "Research"} · ${summary.run_id}`,
  });
}

function downloadLink(runId, artifact, format, label) {
  return createElement("a", {
    className: "button button--secondary button--small",
    text: label,
    attributes: {
      href: researchService.exportUrl(runId, { artifact, format }),
      download: `${runId}-${artifact}.${format}`,
    },
  });
}

export function createReportCenterPage() {
  let destroyed = false;
  let runs = [];

  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite", "data-testid": "report-status" },
    text: "Loading research runs...",
  });
  const runSelect = createElement("select", {
    className: "form-control",
    attributes: { "data-testid": "report-run-select" },
  });
  const loadButton = createElement("button", {
    className: "button button--primary",
    text: "Load Report",
    attributes: { type: "button", "data-testid": "load-research-report" },
  });
  const refreshButton = createElement("button", {
    className: "button button--secondary",
    text: "Refresh Runs",
    attributes: { type: "button" },
  });
  const exportPanel = createElement("div", { className: "report-export-grid" });
  const preview = createElement("pre", {
    className: "strategy-json-preview report-markdown-preview",
    attributes: { "data-testid": "research-report-preview" },
    text: "No report selected.",
  });
  const runMeta = createElement("div", { className: "metric-grid" });

  const element = createElement("section", {
    className: "page report-center-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Phase 9E · Report Center" }),
          createElement("h1", { text: "Research report center." }),
          createElement("p", {
            text: "Preview completed research pipeline reports and export reusable artifacts for review.",
          }),
        ],
      }),
      activity,
      createElement("section", {
        className: "report-center-layout",
        children: [
          createElement("article", {
            className: "panel",
            attributes: { "data-guide": "report-controls" },
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Runs" }),
                      createElement("h2", { text: "Research artifacts" }),
                    ],
                  }),
                ],
              }),
              createElement("div", {
                className: "form-grid report-control-grid",
                children: [
                  createElement("label", {
                    className: "form-field",
                    children: [
                      createElement("span", { className: "form-field__label", text: "Run" }),
                      runSelect,
                    ],
                  }),
                ],
              }),
              createElement("div", {
                className: "form-actions",
                children: [loadButton, refreshButton],
              }),
              runMeta,
              exportPanel,
            ],
          }),
          createElement("article", {
            className: "panel",
            attributes: { "data-guide": "report-preview" },
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Markdown" }),
                      createElement("h2", { text: "Report preview" }),
                    ],
                  }),
                ],
              }),
              preview,
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

  function renderRunSelect(selectedRunId = "") {
    runSelect.replaceChildren(...runs.map(optionForRun));
    if (selectedRunId) runSelect.value = selectedRunId;
  }

  function renderExports(runId) {
    exportPanel.replaceChildren(
      createElement("a", {
        className: "button button--secondary button--small",
        text: "Markdown Report",
        attributes: {
          href: researchService.reportUrl(runId),
          download: `${runId}-research-report.md`,
        },
      }),
      ...EXPORTS.map(([artifact, format, label]) => downloadLink(runId, artifact, format, label)),
    );
  }

  function renderMeta(summary) {
    const quality = summary.quality ?? {};
    const scanner = summary.scanner ?? {};
    runMeta.replaceChildren(
      metric("Run", summary.run_id ?? "-", summary.run_label ?? ""),
      metric("Coverage", `${Number(quality.coverage_pct ?? 0).toFixed(1)}%`, "cached universe"),
      metric("Scanner", scanner.matched_symbols ?? 0, `${scanner.skipped_symbols ?? 0} skipped`),
      metric("Portfolio runs", summary.portfolio_matrix?.length ?? 0, "matrix"),
    );
  }

  async function refreshRuns() {
    setActivity("loading", "Loading research runs...");
    try {
      const response = await researchService.list({ limit: 20 });
      if (destroyed) return;
      runs = response.runs ?? [];
      renderRunSelect(queryRunId() || runs[0]?.run_id);
      setActivity(runs.length ? "success" : "warning", `${runs.length} research runs loaded.`);
    } catch (error) {
      if (!destroyed) setActivity("error", error?.message ?? "Unable to load research runs.");
    }
  }

  async function loadReport() {
    if (!runSelect.value) {
      setActivity("warning", "No research run is available.");
      return;
    }
    setActivity("loading", `Loading ${runSelect.value} report...`);
    try {
      const [run, markdown] = await Promise.all([
        researchService.get(runSelect.value),
        researchService.report(runSelect.value),
      ]);
      if (destroyed) return;
      preview.textContent = markdown;
      renderMeta(run.summary);
      renderExports(run.summary.run_id);
      setActivity("success", `${run.summary.run_id} report loaded.`);
    } catch (error) {
      if (!destroyed) setActivity("error", error?.message ?? "Unable to load report.");
    }
  }

  loadButton.addEventListener("click", loadReport);
  refreshButton.addEventListener("click", refreshRuns);
  refreshRuns().then(loadReport);

  return {
    element,
    destroy() {
      destroyed = true;
    },
  };
}

function metric(label, value, meta = "") {
  return createElement("article", {
    className: "metric-card",
    children: [
      createElement("span", { className: "metric-card__label", text: label }),
      createElement("strong", { className: "metric-card__value", text: String(value) }),
      meta ? createElement("small", { className: "metric-card__meta", text: meta }) : null,
    ],
  });
}
