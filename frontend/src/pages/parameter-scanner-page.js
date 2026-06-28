import { ApiError } from "../core/api-client.js";
import { createElement } from "../core/dom.js";
import { jobService } from "../services/job-service.js";
import { marketService } from "../services/market-service.js";
import { scannerService } from "../services/scanner-service.js";
import { universeService } from "../services/universe-service.js";
import { formatInteger, formatPrice } from "../utils/market-formatters.js";

const RESULT_COLUMNS = [
  ["rank", "Rank"],
  ["symbol", "Symbol"],
  ["name", "Name"],
  ["close", "Close"],
  ["rsi_14", "RSI"],
  ["atr_pct", "ATR%"],
  ["volume_ratio_20d", "Vol ratio"],
  ["return_20d_pct", "20D"],
  ["return_60d_pct", "60D"],
  ["return_252d_pct", "252D"],
];

const SORT_KEYS = [
  "return_60d_pct",
  "return_20d_pct",
  "return_252d_pct",
  "rsi_14",
  "atr_pct",
  "volume_ratio_20d",
  "close",
  "volume",
];

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

function checkbox(label, checked = true) {
  const input = createElement("input", { attributes: { type: "checkbox" } });
  input.checked = checked;
  return {
    input,
    element: createElement("label", {
      className: "checkbox-field",
      children: [input, createElement("span", { text: label })],
    }),
  };
}

function errorMessage(error) {
  if (error instanceof ApiError) return error.details?.error?.message ?? error.message;
  return error?.message ?? "Unexpected scanner error.";
}

function metric(value, formatter = String) {
  return Number.isFinite(Number(value)) ? formatter(Number(value)) : "-";
}

function formatPercent(value) {
  return `${Number(value).toFixed(2)}%`;
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

export function createParameterScannerPage() {
  let destroyed = false;
  let universeId = "us_common_stocks";
  let currentRun = null;
  let tableSort = { key: "rank", direction: "asc" };

  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Load a universe, sync bars, then run or reload scanner results.",
  });
  const universeMeta = createElement("p", {
    className: "table-caption",
    text: "Universe not loaded.",
  });
  const universeSelect = select("universe");
  const syncStartInput = dateInput("syncStart", "2023-01-03");
  const syncEndInput = dateInput("syncEnd", "2025-12-31");
  const chunkSizeInput = numberInput("50", { min: "1", max: "100" });
  const cursorInput = numberInput("0", { min: "0" });
  const syncModeSelect = select("syncMode", [
    ["all", "All symbols"],
    ["missing_or_stale", "Missing or stale"],
    ["retry_failed", "Retry failed"],
  ]);
  const staleAfterInput = dateInput("staleAfter", "2025-01-01");
  const failedRunIdInput = createElement("input", {
    className: "form-control",
    attributes: { type: "text", placeholder: "sync_..." },
  });
  const scanStartInput = dateInput("scanStart", "2023-01-03");
  const scanEndInput = dateInput("scanEnd", "2025-12-31");
  const presetSelect = select("preset");
  const sortKeySelect = select(
    "sortKey",
    SORT_KEYS.map((key) => [key, key]),
  );
  sortKeySelect.value = "return_60d_pct";
  const sortDirectionSelect = select("sortDirection", [
    ["desc", "Descending"],
    ["asc", "Ascending"],
  ]);
  const savedScanSelect = select("savedScan");
  const rsiMinInput = numberInput("40", { min: "0", max: "100" });
  const rsiMaxInput = numberInput("70", { min: "0", max: "100" });
  const volumeRatioInput = numberInput("1.0", { min: "0", step: "0.1" });
  const return20Input = numberInput("0", { step: "0.1" });
  const return60Input = numberInput("0", { step: "0.1" });
  const return252Input = numberInput("0", { step: "0.1" });
  const atrPctInput = numberInput("12", { min: "0", step: "0.1" });
  const limitInput = numberInput("100", { min: "1", max: "500" });
  const minBarsInput = numberInput("0", { min: "0" });
  const minLastCachedInput = dateInput("minLastCached", "");
  const maxMissingInput = numberInput("", { min: "0" });
  const allowFixture = checkbox("Allow fixture data", true);
  const closeAboveSma200 = checkbox("Close > SMA200", true);
  const sma20AboveSma60 = checkbox("SMA20 > SMA60", true);
  const rsiRange = checkbox("RSI range", true);
  const volumeRatio = checkbox("Volume ratio", true);
  const return20 = checkbox("20D return", false);
  const return60 = checkbox("60D return", true);
  const return252 = checkbox("252D return", false);
  const atrPct = checkbox("ATR% max", false);
  const refreshButton = button("Refresh US universe", "secondary");
  const syncButton = button("Sync chunk", "secondary");
  const queueSyncButton = button("Queue sync", "secondary");
  const scanButton = button("Run scanner", "primary");
  const queueScanButton = button("Queue scanner", "secondary");
  const loadScanButton = button("Load saved run", "secondary");
  presetSelect.dataset.testid = "scanner-preset-select";
  limitInput.dataset.testid = "scanner-limit-input";
  queueScanButton.dataset.testid = "queue-scanner-button";
  const summary = createElement("div", { className: "metric-grid" });
  const resultsBody = createElement("tbody");
  const skippedBody = createElement("tbody");
  const syncHistoryBody = createElement("tbody");
  const resultsCaption = createElement("p", {
    className: "table-caption",
    text: "No scan results.",
  });
  const skippedCaption = createElement("p", {
    className: "table-caption",
    text: "No skipped symbols.",
  });

  const element = createElement("section", {
    className: "page parameter-scanner-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Market Scanner" }),
          createElement("h1", { text: "Scanner operations for cached stock universes." }),
          createElement("p", {
            text: "Run reusable technical screens, inspect skipped symbols, and manage batch sync history.",
          }),
        ],
      }),
      activity,
      createElement("section", {
        className: "panel",
        children: [
          panelHeader("Universe + sync", "Prepare cached data", "Operational"),
          universeMeta,
          createElement("div", {
            className: "form-grid",
            children: [
              field("Universe", universeSelect),
              field("Sync start", syncStartInput),
              field("Sync end", syncEndInput),
              field("Chunk size", chunkSizeInput),
              field("Cursor", cursorInput),
              field("Mode", syncModeSelect),
              field("Stale before", staleAfterInput),
              field("Failed sync run", failedRunIdInput),
            ],
          }),
          createElement("div", {
            className: "form-actions",
            children: [refreshButton, syncButton, queueSyncButton],
          }),
        ],
      }),
      createElement("section", {
        className: "panel",
        attributes: { "data-guide": "scanner-workbench" },
        children: [
          panelHeader("Rules", "Scanner presets and filters", "Presets"),
          createElement("div", {
            className: "form-grid",
            children: [
              field("Preset", presetSelect),
              field("Scan start", scanStartInput),
              field("Scan end", scanEndInput),
              field("Sort key", sortKeySelect),
              field("Sort direction", sortDirectionSelect),
              field("RSI min", rsiMinInput),
              field("RSI max", rsiMaxInput),
              field("Min volume ratio", volumeRatioInput),
              field("Min 20D return %", return20Input),
              field("Min 60D return %", return60Input),
              field("Min 252D return %", return252Input),
              field("Max ATR %", atrPctInput),
              field("Result limit", limitInput),
              field("Saved run", savedScanSelect),
              field("Min bars", minBarsInput),
              field("Min last cached", minLastCachedInput),
              field("Max missing weekdays", maxMissingInput),
            ],
          }),
          createElement("div", {
            className: "checkbox-grid",
            children: [
              closeAboveSma200.element,
              sma20AboveSma60.element,
              rsiRange.element,
              volumeRatio.element,
              return20.element,
              return60.element,
              return252.element,
              atrPct.element,
              allowFixture.element,
            ],
          }),
          createElement("div", {
            className: "form-actions",
            children: [scanButton, queueScanButton, loadScanButton],
          }),
        ],
      }),
      summary,
      tablePanel("Results", "Matched symbols", resultsCaption, resultTable(resultsBody)),
      tablePanel(
        "Skipped",
        "Skipped symbols and reasons",
        skippedCaption,
        skippedTable(skippedBody),
      ),
      tablePanel("Sync History", "Recent batch sync runs", null, syncHistoryTable(syncHistoryBody)),
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

  function renderSummary(run) {
    summary.replaceChildren(
      metricCard("Run", run?.run_id ?? "-"),
      metricCard("Status", run?.status ?? "-"),
      metricCard("Analyzed", formatInteger(run?.analyzed_symbols ?? 0)),
      metricCard("Matched", formatInteger(run?.matched_symbols ?? 0)),
      metricCard("Skipped", formatInteger(run?.skipped_symbols ?? 0)),
    );
  }

  function renderResults(run) {
    const results = sortedResults(run?.results ?? []);
    resultsBody.replaceChildren(...results.map(resultRow));
    resultsCaption.textContent = results.length
      ? `Showing ${results.length} of ${run.matched_symbols} matched symbols.`
      : "No scan results.";
  }

  function renderSkipped(run) {
    const skipped = run?.skipped ?? [];
    skippedBody.replaceChildren(
      ...skipped.map((item) =>
        createElement("tr", {
          children: [
            createElement("td", { text: item.symbol }),
            createElement("td", { text: item.name }),
            createElement("td", { text: item.reason }),
            createElement("td", { text: formatInteger(item.cached_rows) }),
            createElement("td", { text: formatInteger(item.required_rows) }),
            createElement("td", { text: JSON.stringify(item.details ?? {}) }),
          ],
        }),
      ),
    );
    skippedCaption.textContent = skipped.length
      ? `${formatInteger(skipped.length)} symbols skipped.`
      : "No skipped symbols.";
  }

  function sortedResults(results) {
    const direction = tableSort.direction === "asc" ? 1 : -1;
    return [...results].sort((a, b) => {
      const left = valueFor(a, tableSort.key);
      const right = valueFor(b, tableSort.key);
      if (typeof left === "number" && typeof right === "number") return (left - right) * direction;
      return String(left ?? "").localeCompare(String(right ?? "")) * direction;
    });
  }

  function valueFor(result, key) {
    if (key in result) return result[key];
    return result.metrics?.[key] ?? null;
  }

  function resultRow(result) {
    const metrics = result.metrics ?? {};
    return createElement("tr", {
      children: [
        createElement("td", { text: String(result.rank) }),
        createElement("td", { text: result.symbol }),
        createElement("td", { text: result.name }),
        createElement("td", { text: metric(metrics.close, formatPrice) }),
        createElement("td", { text: metric(metrics.rsi_14, (value) => value.toFixed(1)) }),
        createElement("td", { text: metric(metrics.atr_pct, formatPercent) }),
        createElement("td", {
          text: metric(metrics.volume_ratio_20d, (value) => `${value.toFixed(2)}x`),
        }),
        createElement("td", { text: metric(metrics.return_20d_pct, formatPercent) }),
        createElement("td", { text: metric(metrics.return_60d_pct, formatPercent) }),
        createElement("td", { text: metric(metrics.return_252d_pct, formatPercent) }),
      ],
    });
  }

  async function loadUniverses() {
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
    if (response.universes.length) {
      universeId = response.universes[0].universe_id;
      universeSelect.value = universeId;
      await loadUniverseDetail();
    }
  }

  async function loadUniverseDetail() {
    if (!universeSelect.value) return;
    const detail = await universeService.get(universeSelect.value);
    if (destroyed) return;
    universeMeta.textContent = `${detail.universe.name}: ${formatInteger(detail.member_count)} members, refreshed ${new Date(detail.universe.refreshed_at).toLocaleString()}.`;
  }

  async function loadPresets() {
    const response = await scannerService.presets();
    if (destroyed) return;
    presetSelect.replaceChildren(
      createElement("option", { text: "Custom", attributes: { value: "" } }),
      ...response.presets.map((preset) =>
        createElement("option", { text: preset.name, attributes: { value: preset.preset_id } }),
      ),
    );
    presetSelect._presets = response.presets;
  }

  async function loadSavedScans() {
    const response = await scannerService.list({ limit: 20 });
    if (destroyed) return;
    savedScanSelect.replaceChildren(
      ...response.runs.map((run) =>
        createElement("option", {
          text: `${run.run_id} (${run.matched_symbols} matched)`,
          attributes: { value: run.run_id },
        }),
      ),
    );
  }

  async function loadSyncHistory() {
    const response = await marketService.getBatchSyncRuns({ universeId, limit: 10 });
    if (destroyed) return;
    syncHistoryBody.replaceChildren(...response.runs.map(syncHistoryRow));
  }

  function syncHistoryRow(run) {
    const retryButton = button("Retry", "secondary");
    retryButton.classList.add("button--small");
    retryButton.disabled = run.failed === 0;
    retryButton.addEventListener("click", () => {
      syncModeSelect.value = "retry_failed";
      failedRunIdInput.value = run.child_sync_run_id;
      cursorInput.value = "0";
      setActivity("idle", `Retry mode loaded for ${run.child_sync_run_id}.`);
    });
    return createElement("tr", {
      children: [
        createElement("td", { text: run.run_id }),
        createElement("td", { text: run.child_sync_run_id }),
        createElement("td", { text: `${run.cursor_start}-${run.cursor_end}` }),
        createElement("td", { text: formatInteger(run.processed) }),
        createElement("td", { text: formatInteger(run.successful) }),
        createElement("td", { text: formatInteger(run.failed) }),
        createElement("td", { text: run.complete ? "yes" : String(run.next_cursor) }),
        createElement("td", { children: [retryButton] }),
      ],
    });
  }

  function applyPreset() {
    const preset = (presetSelect._presets ?? []).find(
      (item) => item.preset_id === presetSelect.value,
    );
    if (!preset) return;
    const rules = preset.rules;
    closeAboveSma200.input.checked = rules.enable_close_above_sma_200;
    sma20AboveSma60.input.checked = rules.enable_sma_20_above_sma_60;
    rsiRange.input.checked = rules.enable_rsi_range;
    volumeRatio.input.checked = rules.enable_volume_ratio_20d;
    return20.input.checked = rules.enable_return_20d;
    return60.input.checked = rules.enable_return_60d;
    return252.input.checked = rules.enable_return_252d;
    atrPct.input.checked = rules.enable_atr_pct_max;
    rsiMinInput.value = rules.rsi_min;
    rsiMaxInput.value = rules.rsi_max;
    volumeRatioInput.value = rules.volume_ratio_20d_min;
    return20Input.value = rules.return_20d_min_pct;
    return60Input.value = rules.return_60d_min_pct;
    return252Input.value = rules.return_252d_min_pct;
    atrPctInput.value = rules.atr_pct_max;
  }

  async function refreshUniverse() {
    await runBusy("Refreshing US common-stock universe...", async () => {
      const response = await universeService.refreshUsCommonStocks();
      await loadUniverses();
      universeSelect.value = response.universe.universe_id;
      universeId = response.universe.universe_id;
      setActivity("success", `${formatInteger(response.member_count)} symbols loaded.`);
    });
  }

  async function syncChunk() {
    universeId = universeSelect.value || universeId;
    await runBusy(`Synchronizing ${universeId}...`, async () => {
      const response = await marketService.batchSync({
        universeId,
        start: syncStartInput.value,
        end: syncEndInput.value,
        chunkSize: Number(chunkSizeInput.value || 50),
        cursor: Number(cursorInput.value || 0),
        mode: syncModeSelect.value,
        staleAfter: staleAfterInput.value,
        failedRunId: failedRunIdInput.value,
      });
      cursorInput.value = String(response.next_cursor ?? 0);
      setActivity(
        response.failed ? "warning" : "success",
        `${response.processed} processed, ${response.successful} successful, ${response.failed} failed.`,
      );
      await loadSyncHistory();
    });
  }

  async function queueSyncChunk() {
    universeId = universeSelect.value || universeId;
    await runBusy(`Queueing ${universeId} sync...`, async () => {
      const job = await jobService.queueBatchSync(syncPayload());
      setActivity("success", `${job.job_id} queued for batch sync.`);
    });
  }

  async function runScanner() {
    universeId = universeSelect.value || universeId;
    await runBusy(`Scanning ${universeId}...`, async () => {
      const run = await scannerService.run({
        universe_id: universeId,
        start: scanStartInput.value,
        end: scanEndInput.value,
        rules: rulesPayload(),
        quality_gate: qualityGatePayload(),
        sort_key: sortKeySelect.value,
        sort_direction: sortDirectionSelect.value,
        result_limit: Number(limitInput.value || 100),
      });
      currentRun = run;
      renderRun(run);
      await loadSavedScans();
      setActivity(
        "success",
        `${run.run_id}: ${run.matched_symbols} matched, ${run.skipped_symbols} skipped.`,
      );
    });
  }

  async function queueScanner() {
    universeId = universeSelect.value || universeId;
    await runBusy(`Queueing ${universeId} scanner job...`, async () => {
      const job = await jobService.queueScan(scanPayload());
      setActivity("success", `${job.job_id} queued for scanner run.`);
    });
  }

  function syncPayload() {
    return {
      universe_id: universeId,
      start: syncStartInput.value,
      end: syncEndInput.value,
      chunk_size: Number(chunkSizeInput.value || 50),
      cursor: Number(cursorInput.value || 0),
      mode: syncModeSelect.value,
      stale_after: staleAfterInput.value || null,
      failed_run_id: failedRunIdInput.value || null,
    };
  }

  function scanPayload() {
    return {
      universe_id: universeId,
      start: scanStartInput.value,
      end: scanEndInput.value,
      rules: rulesPayload(),
      quality_gate: qualityGatePayload(),
      sort_key: sortKeySelect.value,
      sort_direction: sortDirectionSelect.value,
      result_limit: Number(limitInput.value || 100),
    };
  }

  async function loadSavedRun() {
    if (!savedScanSelect.value) return;
    await runBusy(`Loading ${savedScanSelect.value}...`, async () => {
      const run = await scannerService.get(savedScanSelect.value);
      currentRun = run;
      renderRun(run);
      setActivity("success", `${run.run_id} loaded.`);
    });
  }

  function rulesPayload() {
    return {
      enable_close_above_sma_200: closeAboveSma200.input.checked,
      enable_sma_20_above_sma_60: sma20AboveSma60.input.checked,
      enable_rsi_range: rsiRange.input.checked,
      enable_volume_ratio_20d: volumeRatio.input.checked,
      enable_return_20d: return20.input.checked,
      enable_return_60d: return60.input.checked,
      enable_return_252d: return252.input.checked,
      enable_atr_pct_max: atrPct.input.checked,
      close_above_sma_200: true,
      sma_20_above_sma_60: true,
      rsi_min: Number(rsiMinInput.value || 0),
      rsi_max: Number(rsiMaxInput.value || 100),
      volume_ratio_20d_min: Number(volumeRatioInput.value || 0),
      return_20d_min_pct: Number(return20Input.value || 0),
      return_60d_min_pct: Number(return60Input.value || 0),
      return_252d_min_pct: Number(return252Input.value || 0),
      atr_pct_max: Number(atrPctInput.value || 0),
    };
  }

  function qualityGatePayload() {
    return {
      min_bars: Number(minBarsInput.value || 0),
      allow_fixture_data: allowFixture.input.checked,
      min_last_cached_date: minLastCachedInput.value || null,
      max_missing_weekdays: maxMissingInput.value === "" ? null : Number(maxMissingInput.value),
    };
  }

  function renderRun(run) {
    renderSummary(run);
    renderResults(run);
    renderSkipped(run);
  }

  async function runBusy(message, action) {
    setBusy(true);
    setActivity("loading", message);
    try {
      await action();
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  universeSelect.addEventListener("change", async () => {
    universeId = universeSelect.value;
    cursorInput.value = "0";
    await loadUniverseDetail();
    await loadSyncHistory();
  });
  presetSelect.addEventListener("change", applyPreset);
  refreshButton.addEventListener("click", refreshUniverse);
  syncButton.addEventListener("click", syncChunk);
  queueSyncButton.addEventListener("click", queueSyncChunk);
  scanButton.addEventListener("click", runScanner);
  queueScanButton.addEventListener("click", queueScanner);
  loadScanButton.addEventListener("click", loadSavedRun);

  Promise.allSettled([loadUniverses(), loadPresets(), loadSavedScans(), loadSyncHistory()]).then(
    () => {
      if (!destroyed) setActivity("success", "Scanner workspace loaded.");
    },
  );
  renderSummary(null);

  return {
    element,
    destroy() {
      destroyed = true;
    },
  };

  function resultTable(body) {
    return createElement("table", {
      className: "data-table",
      children: [
        createElement("thead", {
          children: [
            createElement("tr", {
              children: RESULT_COLUMNS.map(([key, label]) =>
                createElement("th", {
                  children: [
                    createElement("button", {
                      className: "table-sort-button",
                      text: label,
                      attributes: { type: "button" },
                      on: {
                        click() {
                          tableSort = {
                            key,
                            direction:
                              tableSort.key === key && tableSort.direction === "asc"
                                ? "desc"
                                : "asc",
                          };
                          if (currentRun) renderResults(currentRun);
                        },
                      },
                    }),
                  ],
                }),
              ),
            }),
          ],
        }),
        body,
      ],
    });
  }
}

function panelHeader(eyebrow, title, chip) {
  return createElement("div", {
    className: "panel__header",
    children: [
      createElement("div", {
        children: [
          createElement("span", { className: "eyebrow", text: eyebrow }),
          createElement("h2", { text: title }),
        ],
      }),
      createElement("span", { className: "phase-chip", text: chip }),
    ],
  });
}

function tablePanel(eyebrow, title, caption, table) {
  return createElement("section", {
    className: "panel",
    children: [
      panelHeader(eyebrow, title, "Live"),
      caption,
      createElement("div", { className: "table-scroll", children: [table] }),
    ],
  });
}

function skippedTable(body) {
  return simpleTable(["Symbol", "Name", "Reason", "Cached", "Required", "Details"], body);
}

function syncHistoryTable(body) {
  return simpleTable(
    ["Batch run", "Sync run", "Cursor", "Processed", "Success", "Failed", "Done", "Action"],
    body,
  );
}

function simpleTable(headers, body) {
  return createElement("table", {
    className: "data-table",
    children: [
      createElement("thead", {
        children: [
          createElement("tr", { children: headers.map((text) => createElement("th", { text })) }),
        ],
      }),
      body,
    ],
  });
}

function select(name, options = []) {
  return createElement("select", {
    className: "form-control",
    attributes: { name, "aria-label": name },
    children: options.map(([value, label]) =>
      createElement("option", { text: label, attributes: { value } }),
    ),
  });
}

function dateInput(name, value) {
  return createElement("input", {
    className: "form-control",
    attributes: { type: "date", name, value },
  });
}

function numberInput(value, attributes = {}) {
  return createElement("input", {
    className: "form-control",
    attributes: { type: "number", value, ...attributes },
  });
}

function button(text, tone) {
  return createElement("button", {
    className: `button button--${tone}`,
    text,
    attributes: { type: "button" },
  });
}
