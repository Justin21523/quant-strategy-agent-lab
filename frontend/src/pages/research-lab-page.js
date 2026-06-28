import { createElement } from "../core/dom.js";
import { jobService } from "../services/job-service.js";
import { researchService } from "../services/research-service.js";
import { formatCompact, formatInteger } from "../utils/market-formatters.js";

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NAMESPACE, name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
  return element;
}

function pct(value, digits = 1) {
  return Number.isFinite(Number(value)) ? `${Number(value).toFixed(digits)}%` : "-";
}

function signedPct(value, digits = 1) {
  if (!Number.isFinite(Number(value))) return "-";
  const number = Number(value);
  return `${number > 0 ? "+" : ""}${number.toFixed(digits)}%`;
}

function titleize(value = "") {
  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function defaultPayload() {
  return {
    run_label: "Demo Quick Research",
    universe_id: "demo_research_sample",
    start: "2023-01-03",
    end: "2025-12-31",
    provider: "csv",
    sync_mode: "all",
    sync_chunk_size: 25,
    allow_fallback: false,
    benchmark_symbol: "SPY",
    initial_cash: 100000,
    commission: 0.001,
    slippage: 0.0005,
    quality_gate: {
      min_bars: 120,
      allow_fixture_data: true,
      max_missing_weekdays: 1000,
    },
    scanner_config: {
      preset_id: "trend_momentum",
      sort_key: "return_60d_pct",
      sort_direction: "desc",
      result_limit: 12,
      rules: {
        enable_close_above_sma_200: false,
        enable_sma_20_above_sma_60: false,
        enable_rsi_range: false,
        enable_volume_ratio_20d: false,
        enable_return_20d: false,
        enable_return_60d: false,
        enable_return_252d: false,
        enable_atr_pct_max: false,
        close_above_sma_200: true,
        sma_20_above_sma_60: true,
        rsi_min: 0,
        rsi_max: 100,
        volume_ratio_20d_min: 0,
        return_20d_min_pct: 0,
        return_60d_min_pct: -100,
        return_252d_min_pct: 0,
        atr_pct_max: 12,
      },
    },
    portfolio_matrix_configs: [
      {
        label: "Trend Momentum Monthly Top 8",
        scanner_preset_id: "trend_momentum",
        frequency: "monthly",
        top_n: 8,
        lookback_days: 365,
        start: "2023-01-03",
        end: "2023-09-29",
      },
      {
        label: "Low Volatility Monthly Top 10",
        scanner_preset_id: "low_volatility_trend",
        frequency: "monthly",
        top_n: 10,
        lookback_days: 365,
        start: "2023-01-03",
        end: "2023-09-29",
      },
      {
        label: "Oversold Weekly Top 5",
        scanner_preset_id: "oversold_watchlist",
        frequency: "weekly",
        top_n: 5,
        lookback_days: 365,
        start: "2023-01-03",
        end: "2023-09-29",
      },
    ],
    strategy_matrix_configs: [
      { template_id: "buy_and_hold", top_n: 6, start: "2023-01-03", end: "2023-09-29" },
      { template_id: "ma_crossover", top_n: 6, start: "2023-01-03", end: "2023-09-29" },
      {
        template_id: "macd_trend_following",
        top_n: 6,
        start: "2023-01-03",
        end: "2023-09-29",
      },
    ],
  };
}

function metricCard(label, value, meta = "") {
  return createElement("article", {
    className: "metric-card",
    children: [
      createElement("span", { className: "metric-card__label", text: label }),
      createElement("strong", { className: "metric-card__value", text: String(value) }),
      meta ? createElement("small", { className: "metric-card__meta", text: meta }) : null,
    ],
  });
}

function timeline(events = [], job = null) {
  const progress = job?.total ? Math.round((job.processed / job.total) * 100) : 0;
  return createElement("div", {
    className: "research-progress",
    attributes: { "data-testid": "research-progress" },
    children: [
      createElement("div", {
        className: "agent-timeline-summary",
        children: [
          createElement("strong", { text: job?.status ?? "idle" }),
          createElement("span", { text: job ? `${job.processed}/${job.total}` : "0/0" }),
        ],
      }),
      createElement("div", {
        className: "agent-timeline-progress",
        children: [
          createElement("span", {
            className: "agent-timeline-progress__fill",
            attributes: { style: `width: ${progress}%` },
          }),
        ],
      }),
      createElement("ol", {
        className: "demo-timeline",
        children: events.map((event, index) =>
          createElement("li", {
            className: "demo-timeline__step",
            dataset: { state: index < (job?.processed ?? events.length) ? "done" : "pending" },
            children: [
              createElement("span", {
                className: "demo-timeline__index",
                text: String(index + 1).padStart(2, "0"),
              }),
              createElement("div", {
                children: [
                  createElement("strong", { text: event.label ?? titleize(event.id) }),
                  createElement("small", { text: event.message ?? "" }),
                ],
              }),
            ],
          }),
        ),
      }),
    ],
  });
}

function sparkline(points = [], key = "equity", tone = "accent") {
  const valid = points
    .map((point, index) => ({ index, value: Number(point[key]) }))
    .filter((point) => Number.isFinite(point.value));
  if (valid.length < 2) {
    return createElement("div", {
      className: "demo-sparkline demo-sparkline--empty",
      text: "No chart",
    });
  }
  const width = 240;
  const height = 74;
  const min = Math.min(...valid.map((point) => point.value));
  const max = Math.max(...valid.map((point) => point.value));
  const spread = max - min || 1;
  const x = (index) => 8 + (index / Math.max(1, valid.length - 1)) * (width - 16);
  const y = (value) => 8 + ((max - value) / spread) * (height - 16);
  const pointsAttr = valid
    .map((point) => `${x(point.index).toFixed(2)},${y(point.value).toFixed(2)}`)
    .join(" ");
  const svg = svgElement("svg", {
    class: `demo-sparkline demo-sparkline--${tone}`,
    viewBox: `0 0 ${width} ${height}`,
    preserveAspectRatio: "none",
  });
  svg.append(svgElement("polyline", { class: "demo-sparkline__line", points: pointsAttr }));
  return svg;
}

function qualityHeatmap(symbols = []) {
  return createElement("div", {
    className: "quality-heatmap",
    attributes: { "data-testid": "research-quality-heatmap" },
    children: symbols.slice(0, 20).map((item) => {
      const tone =
        !item.supports_sma_200 || !item.supports_return_252d
          ? "danger"
          : item.warnings?.length || Number(item.missing_weekday_count) > 20
            ? "warning"
            : "success";
      return createElement("div", {
        className: "quality-tile",
        dataset: { tone },
        children: [
          createElement("strong", { text: item.symbol }),
          createElement("span", { text: `${formatInteger(item.cached_bar_count)} bars` }),
          createElement("small", { text: `${formatInteger(item.missing_weekday_count)} missing` }),
        ],
      });
    }),
  });
}

function scannerRanking(results = []) {
  const max = Math.max(...results.map((item) => Number(item.return_60d_pct) || 0), 1);
  return createElement("div", {
    className: "scanner-ranking",
    attributes: { "data-testid": "research-scanner-ranking" },
    children: results.slice(0, 10).map((item) =>
      createElement("div", {
        className: "scanner-ranking__row",
        children: [
          createElement("span", { className: "scanner-ranking__rank", text: `#${item.rank}` }),
          createElement("strong", { text: item.symbol }),
          createElement("div", {
            className: "scanner-ranking__bar",
            children: [
              createElement("span", {
                attributes: {
                  style: `width: ${Math.max(8, ((Number(item.return_60d_pct) || 0) / max) * 100)}%`,
                },
              }),
            ],
          }),
          createElement("span", { text: signedPct(item.return_60d_pct) }),
          createElement("small", {
            text: `RSI ${Number(item.rsi_14 ?? 0).toFixed(1)} · ATR ${pct(item.atr_pct)}`,
          }),
        ],
      }),
    ),
  });
}

function portfolioCards(items = []) {
  return createElement("div", {
    className: "portfolio-card-grid",
    attributes: { "data-testid": "research-portfolio-matrix" },
    children: items.map((item, index) =>
      createElement("article", {
        className: "portfolio-demo-card",
        dataset: { best: index === 0 ? "true" : "false" },
        children: [
          createElement("div", {
            className: "portfolio-demo-card__header",
            children: [
              createElement("div", {
                children: [
                  createElement("span", { className: "eyebrow", text: item.frequency ?? "" }),
                  createElement("h3", { text: titleize(item.preset) }),
                ],
              }),
              createElement("strong", { text: signedPct(item.total_return_pct) }),
            ],
          }),
          createElement("div", {
            className: "portfolio-demo-card__charts",
            children: [
              sparkline(item.equity_curve ?? [], "equity"),
              sparkline(item.drawdown_curve ?? [], "drawdown_pct", "danger"),
            ],
          }),
          createElement("div", {
            className: "portfolio-demo-card__stats",
            children: [
              createElement("span", { text: `Final $${formatCompact(item.final_equity)}` }),
              createElement("span", { text: `DD ${pct(item.max_drawdown_pct)}` }),
              createElement("span", {
                text: `Sharpe ${Number(item.sharpe_ratio ?? 0).toFixed(2)}`,
              }),
              createElement("span", { text: `Turnover ${pct(item.turnover_pct)}` }),
            ],
          }),
        ],
      }),
    ),
  });
}

function strategyBars(items = []) {
  const max = Math.max(
    ...items.map((item) => Math.abs(Number(item.average_total_return_pct) || 0)),
    1,
  );
  return createElement("div", {
    className: "strategy-bars",
    attributes: { "data-testid": "research-strategy-matrix" },
    children: items.map((item) =>
      createElement("article", {
        className: "strategy-bars__row",
        children: [
          createElement("strong", { text: titleize(item.template_id) }),
          createElement("div", {
            className: "strategy-bars__track",
            children: [
              createElement("span", {
                attributes: {
                  style: `width: ${Math.max(6, (Math.abs(Number(item.average_total_return_pct) || 0) / max) * 100)}%`,
                },
              }),
            ],
          }),
          createElement("span", { text: signedPct(item.average_total_return_pct) }),
          createElement("small", {
            text: `Best ${item.best_symbol ?? "-"} · Worst ${item.worst_symbol ?? "-"}`,
          }),
        ],
      }),
    ),
  });
}

function clonePayload(payload) {
  return JSON.parse(JSON.stringify(payload));
}

function field(label, control, hint = "") {
  return createElement("label", {
    className: "form-field",
    children: [
      createElement("span", { className: "form-field__label", text: label }),
      control,
      hint ? createElement("small", { text: hint }) : null,
    ],
  });
}

function input(type, value, attributes = {}) {
  return createElement("input", {
    className: "form-control",
    attributes: { type, value, ...attributes },
  });
}

function checkbox(checked = false) {
  const control = createElement("input", { attributes: { type: "checkbox" } });
  control.checked = checked;
  return control;
}

function select(options = []) {
  return createElement("select", {
    className: "form-control",
    children: options.map(([value, label]) =>
      createElement("option", { attributes: { value }, text: label }),
    ),
  });
}

function slug(value) {
  return String(value || "research_preset")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 64);
}

export function createResearchLabPage() {
  let destroyed = false;
  let pollTimer = null;
  let currentSummary = null;
  let presets = [];

  const runLabelInput = input("text", "Demo Quick Research", {
    "data-testid": "research-run-label-input",
  });
  const presetNameInput = input("text", "Demo Quick Research", {
    "data-testid": "research-preset-name-input",
  });
  const presetDescriptionInput = input("text", "Reusable fixture-backed research pipeline preset.");
  const presetSelect = select();
  presetSelect.dataset.testid = "research-preset-select";
  const universeInput = input("text", "demo_research_sample");
  const startInput = input("date", "2023-01-03");
  const endInput = input("date", "2025-12-31");
  const providerSelect = select([
    ["csv", "CSV fixture"],
    ["yfinance", "YFinance"],
    ["finmind", "FinMind"],
  ]);
  const scannerPresetSelect = select([
    ["trend_momentum", "Trend Momentum"],
    ["pullback_in_uptrend", "Pullback in Uptrend"],
    ["volume_breakout", "Volume Breakout"],
    ["low_volatility_trend", "Low Volatility Trend"],
    ["oversold_watchlist", "Oversold Watchlist"],
  ]);
  const sortKeySelect = select([
    ["return_60d_pct", "60D return"],
    ["return_20d_pct", "20D return"],
    ["return_252d_pct", "252D return"],
    ["rsi_14", "RSI"],
    ["atr_pct", "ATR%"],
    ["volume_ratio_20d", "Volume ratio"],
  ]);
  const scannerLimitInput = input("number", "12", { min: "1", max: "200" });
  const strictRulesInput = checkbox(false);
  const minBarsInput = input("number", "120", { min: "0" });
  const allowFixtureInput = checkbox(true);
  const maxMissingInput = input("number", "1000", { min: "0" });
  const portfolioTopNsInput = input("text", "8,10,5", {
    "data-testid": "research-portfolio-topns-input",
  });
  const portfolioFrequencySelect = select([
    ["monthly", "Monthly"],
    ["weekly", "Weekly"],
  ]);
  const strategyChecks = ["buy_and_hold", "ma_crossover", "macd_trend_following"].map((id) => {
    const control = checkbox(true);
    return { id, control };
  });
  const benchmarkInput = input("text", "SPY");
  const cashInput = input("number", "100000", { min: "1", step: "1000" });
  const commissionInput = input("number", "0.001", { min: "0", step: "0.0001" });
  const slippageInput = input("number", "0.0005", { min: "0", step: "0.0001" });

  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite", "data-testid": "research-status" },
    text: "Ready to run Demo Quick Research.",
  });
  const runButton = createElement("button", {
    className: "button button--primary",
    text: "Run Pipeline",
    attributes: { type: "button", "data-testid": "run-research-pipeline" },
  });
  const loadLatestButton = createElement("button", {
    className: "button button--secondary",
    text: "Load Latest",
    attributes: { type: "button" },
  });
  const savePresetButton = createElement("button", {
    className: "button button--secondary",
    text: "Save Preset",
    attributes: { type: "button", "data-testid": "save-research-preset" },
  });
  const loadPresetButton = createElement("button", {
    className: "button button--secondary",
    text: "Load Preset",
    attributes: { type: "button", "data-testid": "load-research-preset" },
  });
  const payloadPreview = createElement("pre", {
    className: "strategy-json-preview",
    text: JSON.stringify(defaultPayload(), null, 2),
  });
  const summaryGrid = createElement("div", { className: "metric-grid" });
  const progressPanel = createElement("div");
  const historyPanel = createElement("div");
  const qualityPanel = createElement("div");
  const scannerPanel = createElement("div");
  const portfolioPanel = createElement("div");
  const strategyPanel = createElement("div");

  const element = createElement("section", {
    className: "page research-lab-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Phase 9E · Research Pipeline" }),
          createElement("h1", { text: "One-click quant research pipeline." }),
          createElement("p", {
            text: "Run sync, data quality, scanner ranking, portfolio matrix, strategy comparison, and report generation as one saved job.",
          }),
        ],
      }),
      activity,
      createElement("section", {
        className: "research-lab-layout",
        children: [
          createElement("aside", {
            className: "panel research-builder",
            attributes: { "data-guide": "research-builder" },
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Builder" }),
                      createElement("h2", { text: "Pipeline preset builder" }),
                    ],
                  }),
                ],
              }),
              createElement("div", {
                className: "form-grid research-builder-grid",
                children: [
                  field("Preset", presetSelect),
                  field("Preset name", presetNameInput),
                  field("Run label", runLabelInput),
                  field("Universe", universeInput),
                  field("Start", startInput),
                  field("End", endInput),
                  field("Provider", providerSelect),
                  field("Scanner preset", scannerPresetSelect),
                  field("Sort key", sortKeySelect),
                  field("Scanner limit", scannerLimitInput),
                  field("Min bars", minBarsInput),
                  field("Max missing weekdays", maxMissingInput),
                  field("Portfolio top N", portfolioTopNsInput, "Comma list maps to matrix rows."),
                  field("Portfolio frequency", portfolioFrequencySelect),
                  field("Benchmark", benchmarkInput),
                  field("Initial cash", cashInput),
                  field("Commission", commissionInput),
                  field("Slippage", slippageInput),
                ],
              }),
              createElement("label", {
                className: "checkbox-field",
                children: [
                  strictRulesInput,
                  createElement("span", {
                    text: "Use strict scanner preset rules instead of permissive demo rules.",
                  }),
                ],
              }),
              createElement("label", {
                className: "checkbox-field",
                children: [
                  allowFixtureInput,
                  createElement("span", { text: "Allow fixture/sample data in quality gates." }),
                ],
              }),
              createElement("div", {
                className: "research-checkbox-row",
                children: strategyChecks.map(({ id, control }) =>
                  createElement("label", {
                    className: "checkbox-field checkbox-field--compact",
                    children: [control, createElement("span", { text: titleize(id) })],
                  }),
                ),
              }),
              field("Description", presetDescriptionInput),
              createElement("div", {
                className: "form-actions",
                children: [runButton, savePresetButton, loadPresetButton, loadLatestButton],
              }),
              payloadPreview,
            ],
          }),
          createElement("div", {
            className: "research-results",
            children: [
              createElement("article", {
                className: "panel",
                attributes: { "data-guide": "research-progress" },
                children: [
                  createElement("div", {
                    className: "panel__header",
                    children: [
                      createElement("div", {
                        children: [
                          createElement("span", { className: "eyebrow", text: "Progress" }),
                          createElement("h2", { text: "Live run monitor" }),
                        ],
                      }),
                    ],
                  }),
                  progressPanel,
                ],
              }),
              summaryGrid,
              createElement("article", {
                className: "panel",
                children: [
                  createElement("div", {
                    className: "panel__header",
                    children: [
                      createElement("div", {
                        children: [
                          createElement("span", { className: "eyebrow", text: "History" }),
                          createElement("h2", { text: "Saved research runs" }),
                        ],
                      }),
                    ],
                  }),
                  historyPanel,
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
                          createElement("span", { className: "eyebrow", text: "Quality" }),
                          createElement("h2", { text: "Data readiness heatmap" }),
                        ],
                      }),
                    ],
                  }),
                  qualityPanel,
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
                          createElement("span", { className: "eyebrow", text: "Scanner" }),
                          createElement("h2", { text: "Ranked candidates" }),
                        ],
                      }),
                    ],
                  }),
                  scannerPanel,
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
                          createElement("span", { className: "eyebrow", text: "Portfolio Matrix" }),
                          createElement("h2", { text: "Rebalance comparison" }),
                        ],
                      }),
                    ],
                  }),
                  portfolioPanel,
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
                          createElement("span", { className: "eyebrow", text: "Strategy Matrix" }),
                          createElement("h2", { text: "Template comparison" }),
                        ],
                      }),
                    ],
                  }),
                  strategyPanel,
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

  function buildPayload() {
    const payload = clonePayload(defaultPayload());
    const topNs = portfolioTopNsInput.value
      .split(",")
      .map((value) => Number.parseInt(value.trim(), 10))
      .filter((value) => Number.isFinite(value) && value > 0);
    const selectedStrategies = strategyChecks
      .filter(({ control }) => control.checked)
      .map(({ id }) => id);

    payload.run_label = runLabelInput.value || "Research Pipeline";
    payload.universe_id = universeInput.value || "demo_research_sample";
    payload.start = startInput.value || "2023-01-03";
    payload.end = endInput.value || "2025-12-31";
    payload.provider = providerSelect.value || "csv";
    payload.benchmark_symbol = (benchmarkInput.value || "SPY").toUpperCase();
    payload.initial_cash = Number(cashInput.value || 100000);
    payload.commission = Number(commissionInput.value || 0);
    payload.slippage = Number(slippageInput.value || 0);
    payload.quality_gate = {
      min_bars: Number(minBarsInput.value || 0),
      allow_fixture_data: allowFixtureInput.checked,
      max_missing_weekdays: Number(maxMissingInput.value || 0),
    };
    payload.scanner_config.preset_id = scannerPresetSelect.value || "trend_momentum";
    payload.scanner_config.sort_key = sortKeySelect.value || "return_60d_pct";
    payload.scanner_config.result_limit = Number(scannerLimitInput.value || 12);
    payload.scanner_config.rules = strictRulesInput.checked ? null : payload.scanner_config.rules;
    payload.portfolio_matrix_configs = payload.portfolio_matrix_configs.map((config, index) => ({
      ...config,
      frequency: portfolioFrequencySelect.value || config.frequency,
      top_n: topNs[index] ?? config.top_n,
      start: payload.start,
      end: config.end || payload.end,
    }));
    payload.strategy_matrix_configs = selectedStrategies.map((template_id) => ({
      template_id,
      top_n: Math.min(Number(scannerLimitInput.value || 6), 20),
      start: payload.start,
      end: "2023-09-29",
    }));
    return payload;
  }

  function updatePreview() {
    payloadPreview.textContent = JSON.stringify(buildPayload(), null, 2);
  }

  function applyPayload(config = {}) {
    const payload = { ...defaultPayload(), ...config };
    runLabelInput.value = payload.run_label ?? "Research Pipeline";
    universeInput.value = payload.universe_id ?? "demo_research_sample";
    startInput.value = payload.start ?? "2023-01-03";
    endInput.value = payload.end ?? "2025-12-31";
    providerSelect.value = payload.provider ?? "csv";
    benchmarkInput.value = payload.benchmark_symbol ?? "SPY";
    cashInput.value = payload.initial_cash ?? 100000;
    commissionInput.value = payload.commission ?? 0.001;
    slippageInput.value = payload.slippage ?? 0.0005;
    minBarsInput.value = payload.quality_gate?.min_bars ?? 120;
    allowFixtureInput.checked = payload.quality_gate?.allow_fixture_data ?? true;
    maxMissingInput.value = payload.quality_gate?.max_missing_weekdays ?? 1000;
    scannerPresetSelect.value = payload.scanner_config?.preset_id ?? "trend_momentum";
    sortKeySelect.value = payload.scanner_config?.sort_key ?? "return_60d_pct";
    scannerLimitInput.value = payload.scanner_config?.result_limit ?? 12;
    strictRulesInput.checked = !payload.scanner_config?.rules;
    const matrix = payload.portfolio_matrix_configs ?? [];
    portfolioTopNsInput.value = matrix.map((item) => item.top_n).join(",") || "8,10,5";
    portfolioFrequencySelect.value = matrix[0]?.frequency ?? "monthly";
    const selected = new Set(
      (payload.strategy_matrix_configs ?? []).map((item) => item.template_id),
    );
    for (const { id, control } of strategyChecks) {
      control.checked = selected.size ? selected.has(id) : true;
    }
    updatePreview();
  }

  function renderSummary(summary) {
    currentSummary = summary;
    const quality = summary.quality ?? {};
    const scanner = summary.scanner ?? {};
    summaryGrid.replaceChildren(
      metricCard("Run", summary.run_id ?? "-", summary.run_label ?? ""),
      metricCard(
        "Coverage",
        pct(quality.coverage_pct),
        `${formatInteger(quality.covered_symbols ?? 0)} cached`,
      ),
      metricCard(
        "Scanner matches",
        formatInteger(scanner.matched_symbols ?? 0),
        `${formatInteger(scanner.skipped_symbols ?? 0)} skipped`,
      ),
      metricCard("Portfolio runs", formatInteger(summary.portfolio_matrix?.length ?? 0), "matrix"),
    );
    progressPanel.replaceChildren(timeline(summary.events ?? []));
    qualityPanel.replaceChildren(qualityHeatmap(quality.symbols ?? []));
    scannerPanel.replaceChildren(scannerRanking(scanner.results ?? []));
    portfolioPanel.replaceChildren(portfolioCards(summary.portfolio_matrix ?? []));
    strategyPanel.replaceChildren(strategyBars(summary.strategy_comparison ?? []));
  }

  function renderHistory(runs = []) {
    historyPanel.replaceChildren(
      createElement("div", {
        className: "research-history",
        children: runs.map((summary) =>
          createElement("div", {
            className: "architecture-row research-history__item",
            children: [
              createElement("button", {
                className: "research-history__load",
                text: `${summary.run_label ?? "Research"} · ${summary.run_id}`,
                attributes: { type: "button" },
                on: {
                  click() {
                    renderSummary(summary);
                    setActivity("success", `${summary.run_id} loaded from history.`);
                  },
                },
              }),
              createElement("a", {
                className: "button button--secondary button--small",
                text: "Open Report",
                attributes: { href: `#/report-center?run=${encodeURIComponent(summary.run_id)}` },
              }),
            ],
          }),
        ),
      }),
    );
  }

  function renderPresets() {
    presetSelect.replaceChildren(
      ...presets.map((preset) =>
        createElement("option", {
          attributes: { value: preset.preset_id },
          text: `${preset.name} · ${preset.preset_id}`,
        }),
      ),
    );
  }

  async function refreshPresets() {
    try {
      const response = await researchService.listPresets();
      presets = response.presets ?? [];
      if (!destroyed) renderPresets();
    } catch {
      presets = [];
      if (!destroyed) renderPresets();
    }
  }

  async function refreshHistory() {
    try {
      const response = await researchService.list({ limit: 10 });
      if (!destroyed) renderHistory(response.runs ?? []);
    } catch {
      if (!destroyed) renderHistory([]);
    }
  }

  async function loadLatest() {
    try {
      const response = await researchService.latest();
      if (destroyed) return;
      renderSummary(response.summary);
      setActivity("success", `${response.summary.run_id} loaded.`);
      await refreshHistory();
    } catch (error) {
      if (!destroyed) setActivity("warning", error?.message ?? "No saved research runs yet.");
    }
  }

  async function pollJob(jobId) {
    const job = await jobService.get(jobId);
    if (destroyed) return;
    progressPanel.replaceChildren(timeline(currentSummary?.events ?? [], job));
    setActivity(job.status === "running" ? "loading" : "idle", job.message);
    if (["success", "failed", "cancelled"].includes(job.status)) {
      globalThis.clearInterval(pollTimer);
      pollTimer = null;
      runButton.disabled = false;
      if (job.status !== "success") {
        setActivity("error", job.error ?? `Pipeline ended with ${job.status}.`);
        return;
      }
      const response = await researchService.get(job.result_id);
      if (!destroyed) {
        renderSummary(response.summary);
        setActivity("success", `${response.summary.run_id} completed.`);
        await refreshHistory();
      }
    }
  }

  runButton.addEventListener("click", async () => {
    runButton.disabled = true;
    setActivity("loading", "Queueing research pipeline...");
    try {
      const queued = await jobService.queueResearchPipeline(buildPayload());
      setActivity("loading", `${queued.job_id} queued.`);
      pollTimer = globalThis.setInterval(() => pollJob(queued.job_id), 900);
      await pollJob(queued.job_id);
    } catch (error) {
      runButton.disabled = false;
      setActivity("error", error?.message ?? "Unable to queue research pipeline.");
    }
  });

  savePresetButton.addEventListener("click", async () => {
    setActivity("loading", "Saving research preset...");
    try {
      const name = presetNameInput.value || runLabelInput.value || "Research Preset";
      const response = await researchService.savePreset({
        preset_id: slug(name),
        name,
        description: presetDescriptionInput.value || "Saved Research Lab preset.",
        config: buildPayload(),
      });
      await refreshPresets();
      presetSelect.value = response.preset_id;
      setActivity("success", `${response.preset_id} saved.`);
    } catch (error) {
      setActivity("error", error?.message ?? "Unable to save research preset.");
    }
  });

  loadPresetButton.addEventListener("click", async () => {
    if (!presetSelect.value) return;
    setActivity("loading", `Loading ${presetSelect.value}...`);
    try {
      const preset = await researchService.getPreset(presetSelect.value);
      presetNameInput.value = preset.name;
      presetDescriptionInput.value = preset.description;
      applyPayload(preset.config);
      setActivity("success", `${preset.preset_id} loaded.`);
    } catch (error) {
      setActivity("error", error?.message ?? "Unable to load research preset.");
    }
  });

  for (const control of [
    runLabelInput,
    presetNameInput,
    universeInput,
    startInput,
    endInput,
    providerSelect,
    scannerPresetSelect,
    sortKeySelect,
    scannerLimitInput,
    strictRulesInput,
    minBarsInput,
    allowFixtureInput,
    maxMissingInput,
    portfolioTopNsInput,
    portfolioFrequencySelect,
    benchmarkInput,
    cashInput,
    commissionInput,
    slippageInput,
    ...strategyChecks.map((item) => item.control),
  ]) {
    control.addEventListener("input", updatePreview);
    control.addEventListener("change", updatePreview);
  }

  loadLatestButton.addEventListener("click", loadLatest);
  updatePreview();
  progressPanel.replaceChildren(timeline([]));
  refreshPresets();
  refreshHistory();

  return {
    element,
    destroy() {
      destroyed = true;
      if (pollTimer) globalThis.clearInterval(pollTimer);
    },
  };
}
