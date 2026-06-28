import { ApiError } from "../core/api-client.js";
import { createElement } from "../core/dom.js";
import { dataQualityService } from "../services/data-quality-service.js";
import { universeService } from "../services/universe-service.js";
import { formatInteger } from "../utils/market-formatters.js";

function errorMessage(error) {
  if (error instanceof ApiError) return error.details?.error?.message ?? error.message;
  return error?.message ?? "Unexpected data-quality error.";
}

function field(label, control) {
  return createElement("label", {
    className: "form-field",
    children: [createElement("span", { className: "form-field__label", text: label }), control],
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

export function createDataQualityPage() {
  let destroyed = false;
  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Select a universe and date range to inspect cached data quality.",
  });
  const universeSelect = createElement("select", {
    className: "form-control",
    attributes: { name: "universe", "aria-label": "Universe" },
  });
  const startInput = createElement("input", {
    className: "form-control",
    attributes: { type: "date", value: "2023-01-03" },
  });
  const endInput = createElement("input", {
    className: "form-control",
    attributes: { type: "date", value: "2025-12-31" },
  });
  const limitInput = createElement("input", {
    className: "form-control",
    attributes: { type: "number", min: "1", max: "5000", value: "500" },
  });
  const runButton = createElement("button", {
    className: "button button--primary",
    text: "Run report",
    attributes: { type: "button" },
  });
  const summary = createElement("div", { className: "metric-grid" });
  const tableBody = createElement("tbody");
  const caption = createElement("p", { className: "table-caption", text: "No report loaded." });

  const element = createElement("section", {
    className: "page data-quality-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Data Quality" }),
          createElement("h1", { text: "Universe cache coverage and readiness report." }),
          createElement("p", {
            text: "Check bar coverage, missing weekdays, fixture data, and whether symbols can support long-window indicators.",
          }),
        ],
      }),
      activity,
      createElement("section", {
        className: "panel",
        attributes: { "data-guide": "data-quality-report" },
        children: [
          createElement("div", {
            className: "panel__header",
            children: [
              createElement("div", {
                children: [
                  createElement("span", { className: "eyebrow", text: "Inputs" }),
                  createElement("h2", { text: "Report scope" }),
                ],
              }),
              createElement("span", { className: "phase-chip", text: "Coverage" }),
            ],
          }),
          createElement("div", {
            className: "form-grid",
            children: [
              field("Universe", universeSelect),
              field("Start", startInput),
              field("End", endInput),
              field("Symbol limit", limitInput),
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
                  createElement("span", { className: "eyebrow", text: "Symbols" }),
                  createElement("h2", { text: "Cached data quality" }),
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
                          "Symbol",
                          "Name",
                          "Bars",
                          "First",
                          "Last",
                          "Missing",
                          "Providers",
                          "Fixture",
                          "SMA200",
                          "252D",
                          "Warnings",
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
    for (const control of [universeSelect, startInput, endInput, limitInput, runButton]) {
      control.disabled = isBusy;
    }
  }

  function renderReport(report) {
    summary.replaceChildren(
      metricCard("Members", formatInteger(report.member_count)),
      metricCard("Covered", `${formatInteger(report.covered_symbols)} (${report.coverage_pct}%)`),
      metricCard("SMA200 ready", formatInteger(report.sma_200_ready_symbols)),
      metricCard("252D ready", formatInteger(report.return_252d_ready_symbols)),
      metricCard("Fixture symbols", formatInteger(report.fixture_symbols)),
    );
    tableBody.replaceChildren(
      ...report.symbols.map((item) =>
        createElement("tr", {
          children: [
            createElement("td", { text: item.symbol }),
            createElement("td", { text: item.name }),
            createElement("td", { text: formatInteger(item.cached_bar_count) }),
            createElement("td", { text: item.first_cached_date ?? "-" }),
            createElement("td", { text: item.last_cached_date ?? "-" }),
            createElement("td", { text: formatInteger(item.missing_weekday_count) }),
            createElement("td", { text: item.providers.join(", ") || "-" }),
            createElement("td", { text: item.contains_fixture_data ? "yes" : "no" }),
            createElement("td", { text: item.supports_sma_200 ? "yes" : "no" }),
            createElement("td", { text: item.supports_return_252d ? "yes" : "no" }),
            createElement("td", { text: item.warnings.join(", ") || "-" }),
          ],
        }),
      ),
    );
    caption.textContent = `${formatInteger(report.symbols.length)} symbols displayed. Generated ${new Date(report.generated_at).toLocaleString()}.`;
  }

  async function loadUniverses() {
    try {
      const response = await universeService.list();
      if (destroyed) return;
      universeSelect.replaceChildren(
        ...response.universes.map((universe) =>
          createElement("option", {
            text: `${universe.name} (${formatInteger(universe.member_count)})`,
            attributes: { value: universe.universe_id },
          }),
        ),
      );
      if (response.universes.length) setActivity("success", "Universe list loaded.");
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    }
  }

  async function runReport() {
    setBusy(true);
    setActivity("loading", "Generating data-quality report...");
    try {
      const report = await dataQualityService.universeReport({
        universeId: universeSelect.value || "us_common_stocks",
        start: startInput.value,
        end: endInput.value,
        limit: Number(limitInput.value || 500),
      });
      if (destroyed) return;
      renderReport(report);
      setActivity("success", `${report.universe_id} coverage report loaded.`);
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  runButton.addEventListener("click", runReport);
  loadUniverses();

  return {
    element,
    destroy() {
      destroyed = true;
    },
  };
}
