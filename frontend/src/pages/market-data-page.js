import { createDataQualityList } from "../components/data-quality-list.js";
import { createMarketDataTable } from "../components/market-data-table.js";
import { createMetricCard } from "../components/metric-card.js";
import { createPricePreviewChart } from "../charts/price-preview-chart.js";
import { ApiError } from "../core/api-client.js";
import { createElement } from "../core/dom.js";
import { marketService } from "../services/market-service.js";
import { formatCompact, formatPrice, formatTimestamp } from "../utils/market-formatters.js";

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

function metadataRow(label, value) {
  return createElement("div", {
    className: "metadata-row",
    children: [createElement("dt", { text: label }), createElement("dd", { text: value })],
  });
}

function errorMessage(error) {
  if (error instanceof ApiError) {
    return error.details?.error?.message ?? error.message;
  }
  return error?.message ?? "Unexpected market-data error.";
}

export function createMarketDataPage() {
  let destroyed = false;
  let catalog = [];

  const symbolSelect = createElement("select", {
    className: "form-control",
    attributes: { name: "symbol", "aria-label": "Symbol" },
  });
  const startInput = createElement("input", {
    className: "form-control",
    attributes: { type: "date", name: "start" },
  });
  const endInput = createElement("input", {
    className: "form-control",
    attributes: { type: "date", name: "end" },
  });
  const providerSelect = createElement("select", {
    className: "form-control",
    attributes: { name: "provider", "aria-label": "Synchronization provider" },
    children: [
      createElement("option", {
        text: "Auto: yfinance first",
        attributes: { value: "auto" },
      }),
      createElement("option", { text: "yfinance", attributes: { value: "yfinance" } }),
      createElement("option", { text: "Offline CSV fixture", attributes: { value: "csv" } }),
      createElement("option", { text: "FinMind (reserved)", attributes: { value: "finmind" } }),
    ],
  });
  const fallbackInput = createElement("input", {
    attributes: { type: "checkbox", name: "fallback", checked: "" },
  });
  fallbackInput.checked = true;

  const loadButton = createElement("button", {
    className: "button button--primary",
    text: "Load cached OHLCV",
    attributes: { type: "button" },
  });
  const syncButton = createElement("button", {
    className: "button button--secondary",
    text: "Sync provider, then load",
    attributes: { type: "button" },
  });
  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Initializing Phase 1 market catalog…",
  });
  const metrics = createElement("div", { className: "metric-grid" });
  const metadata = createElement("dl", { className: "metadata-list" });
  const providerCards = createElement("div", { className: "provider-grid" });
  const chart = createPricePreviewChart();
  const table = createMarketDataTable();
  const quality = createDataQualityList();

  const controls = createElement("form", {
    className: "market-controls panel",
    children: [
      createElement("div", {
        className: "panel__header",
        children: [
          createElement("div", {
            children: [
              createElement("span", { className: "eyebrow", text: "Query contract" }),
              createElement("h2", { text: "Select a cached market series" }),
            ],
          }),
          createElement("span", { className: "phase-chip", text: "Daily · 1d" }),
        ],
      }),
      createElement("div", {
        className: "form-grid",
        children: [
          field("Symbol", symbolSelect, "Phase 1 catalog: AAPL, SPY, QQQ"),
          field("Start date", startInput),
          field("End date", endInput),
          field(
            "Sync provider",
            providerSelect,
            "Auto uses CSV after a network failure only when fallback is enabled.",
          ),
        ],
      }),
      createElement("label", {
        className: "checkbox-field",
        children: [
          fallbackInput,
          createElement("span", {
            text: "Allow deterministic CSV fallback when the requested provider is unavailable",
          }),
        ],
      }),
      createElement("div", {
        className: "form-actions",
        children: [loadButton, syncButton],
      }),
    ],
  });

  const element = createElement("section", {
    className: "page market-data-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Phase 1 · Market Data Layer" }),
          createElement("h1", { text: "Inspect the data before trusting the strategy." }),
          createElement("p", {
            text: "Query normalized daily OHLCV from SQLite, inspect provider and adjustment metadata, synchronize an optional public source, and keep the demo operational offline.",
          }),
        ],
      }),
      activity,
      controls,
      metrics,
      createElement("div", {
        className: "content-grid market-grid-layout",
        children: [
          createElement("article", {
            className: "panel market-chart-panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Close preview" }),
                      createElement("h2", { text: "Cached series shape" }),
                    ],
                  }),
                  createElement("span", { className: "phase-chip", text: "Vanilla SVG" }),
                ],
              }),
              chart.element,
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
                      createElement("span", { className: "eyebrow", text: "Provenance" }),
                      createElement("h2", { text: "Source metadata" }),
                    ],
                  }),
                ],
              }),
              metadata,
            ],
          }),
        ],
      }),
      createElement("div", {
        className: "content-grid content-grid--two market-secondary-grid",
        children: [
          createElement("article", {
            className: "panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Validation" }),
                      createElement("h2", { text: "Data-quality warnings" }),
                    ],
                  }),
                ],
              }),
              quality.element,
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
                      createElement("span", { className: "eyebrow", text: "Adapters" }),
                      createElement("h2", { text: "Provider capabilities" }),
                    ],
                  }),
                ],
              }),
              providerCards,
            ],
          }),
        ],
      }),
      createElement("article", {
        className: "panel market-table-panel",
        children: [
          createElement("div", {
            className: "panel__header",
            children: [
              createElement("div", {
                children: [
                  createElement("span", { className: "eyebrow", text: "Raw preview" }),
                  createElement("h2", { text: "Normalized OHLCV rows" }),
                ],
              }),
              createElement("span", { className: "phase-chip", text: "SQLite cache" }),
            ],
          }),
          table.element,
        ],
      }),
      createElement("aside", {
        className: "disclaimer",
        children: [
          createElement("strong", { text: "Data disclaimer" }),
          createElement("p", {
            text: "Bundled rows are explicitly marked synthetic fixtures for offline engineering tests. Network-synchronized data is for personal research and remains subject to its provider terms. Neither mode is investment advice.",
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
    loadButton.disabled = isBusy;
    syncButton.disabled = isBusy;
    symbolSelect.disabled = isBusy || !catalog.length;
    startInput.disabled = isBusy;
    endInput.disabled = isBusy;
    providerSelect.disabled = isBusy;
    fallbackInput.disabled = isBusy;
  }

  function selectedCatalogItem() {
    return catalog.find((item) => item.symbol === symbolSelect.value);
  }

  function applyCatalogDateRange() {
    const selected = selectedCatalogItem();
    if (!selected) return;
    const today = new Date().toISOString().slice(0, 10);
    startInput.value = selected.first_cached_date ?? "";
    endInput.value = selected.last_cached_date ?? "";
    startInput.min = "1970-01-01";
    startInput.max = today;
    endInput.min = "1970-01-01";
    endInput.max = today;
  }

  function renderProviders(providers = []) {
    providerCards.replaceChildren(
      ...providers.map((provider) =>
        createElement("article", {
          className: "provider-card",
          dataset: { status: provider.status },
          children: [
            createElement("div", {
              className: "provider-card__header",
              children: [
                createElement("strong", { text: provider.provider }),
                createElement("span", { text: provider.status }),
              ],
            }),
            createElement("p", { text: provider.notes }),
            createElement("small", {
              text: provider.supports_sync ? "Synchronization enabled" : "No Phase 1 sync",
            }),
          ],
        }),
      ),
    );
  }

  function renderSeries(series) {
    const bars = series.bars ?? [];
    const first = bars[0];
    const last = bars.at(-1);
    const change = first && last ? Number(last.close) - Number(first.close) : 0;
    const changePercent = first ? (change / Number(first.close)) * 100 : 0;
    metrics.replaceChildren(
      createMetricCard({
        label: "Rows",
        value: String(series.count),
        meta: `${series.effective_range.start} → ${series.effective_range.end}`,
        tone: "accent",
      }),
      createMetricCard({
        label: "Last close",
        value: formatPrice(last?.close),
        meta: `${series.symbol.currency} · ${last?.date ?? "—"}`,
      }),
      createMetricCard({
        label: "Range change",
        value: `${change >= 0 ? "+" : ""}${formatPrice(change)}`,
        meta: `${changePercent >= 0 ? "+" : ""}${changePercent.toFixed(2)}%`,
      }),
      createMetricCard({
        label: "Latest volume",
        value: formatCompact(last?.volume),
        meta: series.source.providers.join(" + "),
      }),
    );
    metadata.replaceChildren(
      metadataRow("Symbol", `${series.symbol.symbol} · ${series.symbol.name}`),
      metadataRow("Market / exchange", `${series.symbol.market} · ${series.symbol.exchange}`),
      metadataRow("Timezone", series.source.source_timezone),
      metadataRow("Currency", series.source.currency),
      metadataRow("Provider", series.source.providers.join(", ")),
      metadataRow("Dataset", series.source.datasets.join(", ")),
      metadataRow("Adjustment", series.source.adjustment),
      metadataRow("Served from", series.source.served_from_cache ? "SQLite cache" : "Provider"),
      metadataRow("Retrieved at", formatTimestamp(series.source.retrieved_at)),
      metadataRow("Fixture rows", series.source.contains_fixture_data ? "Yes — synthetic" : "No"),
    );
    quality.update(series.warnings);
    chart.update(bars);
    table.update(bars);
  }

  async function loadCatalog() {
    setBusy(true);
    setActivity("loading", "Loading symbol catalog and provider capabilities…");
    try {
      const response = await marketService.getSymbols();
      if (destroyed) return;
      catalog = response.symbols;
      symbolSelect.replaceChildren(
        ...catalog.map((item) =>
          createElement("option", {
            text: `${item.symbol} — ${item.name}`,
            attributes: { value: item.symbol },
          }),
        ),
      );
      renderProviders(response.providers);
      applyCatalogDateRange();
      setActivity(
        "success",
        `${response.total} symbols ready. Offline fixtures are already normalized in SQLite.`,
      );
      await loadSeries();
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  async function loadSeries() {
    if (!symbolSelect.value) return;
    setBusy(true);
    setActivity("loading", `Reading ${symbolSelect.value} from the normalized cache…`);
    try {
      const series = await marketService.getOhlcv({
        symbol: symbolSelect.value,
        start: startInput.value,
        end: endInput.value,
      });
      if (destroyed) return;
      renderSeries(series);
      setActivity(
        "success",
        `${series.symbol.symbol}: loaded ${series.count} rows from ${series.source.providers.join(", ")}.`,
      );
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  async function syncSeries() {
    if (!symbolSelect.value || !startInput.value || !endInput.value) {
      setActivity("error", "Choose a symbol and a complete date range before synchronization.");
      return;
    }
    setBusy(true);
    setActivity("loading", `Synchronizing ${symbolSelect.value} with ${providerSelect.value}…`);
    try {
      const response = await marketService.sync({
        symbols: [symbolSelect.value],
        provider: providerSelect.value,
        start: startInput.value,
        end: endInput.value,
        allowFallback: fallbackInput.checked,
      });
      if (destroyed) return;
      const result = response.results[0];
      if (result.status !== "success") {
        throw new Error(result.error ?? result.attempts.join(" · "));
      }
      await loadSeries();
      setActivity(
        result.fallback_used ? "warning" : "success",
        `${result.symbol}: stored ${result.bars_stored} rows via ${result.provider_used}${
          result.fallback_used ? " after fallback" : ""
        } and refreshed the cached view.`,
      );
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  controls.addEventListener("submit", (event) => event.preventDefault());
  symbolSelect.addEventListener("change", () => {
    applyCatalogDateRange();
    loadSeries();
  });
  loadButton.addEventListener("click", loadSeries);
  syncButton.addEventListener("click", syncSeries);

  loadCatalog();

  return {
    element,
    destroy() {
      destroyed = true;
    },
  };
}
