import { createBacktestCandlestickChart } from "../charts/backtest-candlestick-chart.js";
import { createBacktestLineChart } from "../charts/backtest-line-chart.js";
import { createBacktestTradeTable } from "../components/backtest-trade-table.js";
import { createMetricCard } from "../components/metric-card.js";
import { createStrategyJsonPreview } from "../components/strategy-json-preview.js";
import { ApiError } from "../core/api-client.js";
import { createElement } from "../core/dom.js";
import { backtestService } from "../services/backtest-service.js";
import { marketService } from "../services/market-service.js";
import { strategyService } from "../services/strategy-service.js";
import { formatPrice } from "../utils/market-formatters.js";

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

function apiMessage(error) {
  if (error instanceof ApiError) {
    return error.details?.error?.message ?? error.message;
  }
  return error?.message ?? "Unexpected backtest error.";
}

function formatPercent(value) {
  return Number.isFinite(Number(value)) ? `${Number(value).toFixed(2)}%` : "—";
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

export function createBacktestLabPage() {
  let destroyed = false;
  let templates = [];
  let selectedTemplate = null;
  let lastStrategyJson = null;

  const templateSelect = createElement("select", { className: "form-control" });
  const symbolSelect = createElement("select", { className: "form-control" });
  const marketInput = createElement("input", {
    className: "form-control",
    attributes: { value: "US", maxlength: "12" },
  });
  const startInput = createElement("input", {
    className: "form-control",
    attributes: { type: "date", value: "2023-01-03" },
  });
  const endInput = createElement("input", {
    className: "form-control",
    attributes: { type: "date", value: "2025-12-31", max: today() },
  });
  const cashInput = createElement("input", {
    className: "form-control",
    attributes: { type: "number", value: "100000", min: "1", step: "1000" },
  });
  const commissionInput = createElement("input", {
    className: "form-control",
    attributes: { type: "number", value: "0.001", min: "0", max: "1", step: "0.0001" },
  });
  const slippageInput = createElement("input", {
    className: "form-control",
    attributes: { type: "number", value: "0.0005", min: "0", max: "1", step: "0.0001" },
  });
  const parameterFields = createElement("div", { className: "strategy-parameter-grid" });
  const metricGrid = createElement("div", { className: "metric-grid" });
  const stepList = createElement("ol", { className: "agent-timeline" });
  const warningsList = createElement("ul", { className: "backtest-warning-list" });
  const preview = createStrategyJsonPreview();
  const tradeTable = createBacktestTradeTable();
  const candlestickChart = createBacktestCandlestickChart();
  const equityChart = createBacktestLineChart({ label: "Equity curve", valueKey: "equity" });
  const drawdownChart = createBacktestLineChart({
    label: "Drawdown curve",
    valueKey: "drawdown_pct",
    formatter: formatPercent,
    area: true,
    zeroLine: true,
  });

  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Loading templates and symbols…",
  });
  const runButton = createElement("button", {
    className: "button button--primary",
    text: "Run Backtest",
    attributes: { type: "button" },
  });

  const element = createElement("section", {
    className: "page backtest-lab-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Phase 5 · Backtest Lab Frontend" }),
          createElement("h1", { text: "Interactive strategy backtest workbench." }),
          createElement("p", {
            text: "Choose a cached asset, render a Strategy JSON template, run the deterministic engine, then inspect candles, buy/sell markers, equity, drawdown, metrics, trades, warnings, and execution steps.",
          }),
        ],
      }),
      activity,
      createElement("div", {
        className: "backtest-layout backtest-layout--phase5",
        children: [
          createElement("article", {
            className: "panel backtest-control-panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Run config" }),
                      createElement("h2", { text: "Template + execution assumptions" }),
                    ],
                  }),
                  createElement("span", { className: "phase-chip", text: "Frontend lab" }),
                ],
              }),
              createElement("div", {
                className: "form-grid form-grid--strategy-context",
                children: [
                  field("Template", templateSelect),
                  field("Symbol", symbolSelect),
                  field("Market", marketInput),
                  field("Start", startInput),
                  field("End", endInput),
                  field("Initial cash", cashInput),
                  field("Commission", commissionInput, "Fraction, e.g. 0.001 = 0.1%."),
                  field("Slippage", slippageInput, "Fractional fill friction."),
                ],
              }),
              createElement("hr", { className: "panel-separator" }),
              parameterFields,
              createElement("div", { className: "backtest-actions", children: [runButton] }),
            ],
          }),
          createElement("article", {
            className: "panel backtest-preview-panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Strategy JSON" }),
                      createElement("h2", { text: "Rendered input to the engine" }),
                    ],
                  }),
                ],
              }),
              preview.element,
            ],
          }),
        ],
      }),
      metricGrid,
      createElement("article", {
        className: "panel backtest-chart-panel",
        children: [
          createElement("div", {
            className: "panel__header",
            children: [
              createElement("div", {
                children: [
                  createElement("span", { className: "eyebrow", text: "Price action" }),
                  createElement("h2", { text: "Candles + SMA overlay + executed trades" }),
                ],
              }),
            ],
          }),
          candlestickChart.element,
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
                      createElement("span", { className: "eyebrow", text: "Equity" }),
                      createElement("h2", { text: "Portfolio value over time" }),
                    ],
                  }),
                ],
              }),
              equityChart.element,
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
                      createElement("span", { className: "eyebrow", text: "Drawdown" }),
                      createElement("h2", { text: "Peak-to-trough pressure" }),
                    ],
                  }),
                ],
              }),
              drawdownChart.element,
            ],
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
                      createElement("span", { className: "eyebrow", text: "Agent steps" }),
                      createElement("h2", { text: "Engine execution timeline" }),
                    ],
                  }),
                ],
              }),
              stepList,
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
                      createElement("span", { className: "eyebrow", text: "Warnings" }),
                      createElement("h2", { text: "Data and engine notes" }),
                    ],
                  }),
                ],
              }),
              warningsList,
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
                  createElement("span", { className: "eyebrow", text: "Trade ledger" }),
                  createElement("h2", { text: "Closed trades" }),
                ],
              }),
            ],
          }),
          tradeTable.element,
        ],
      }),
      createElement("aside", {
        className: "disclaimer",
        children: [
          createElement("strong", { text: "Backtest boundary" }),
          createElement("p", {
            text: "Phase 5 improves the research UI around the deterministic backtest engine. Historical backtests do not guarantee future performance and this project does not provide investment advice.",
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
    for (const control of [
      templateSelect,
      symbolSelect,
      marketInput,
      startInput,
      endInput,
      cashInput,
      commissionInput,
      slippageInput,
      runButton,
      ...parameterFields.querySelectorAll("input, select"),
    ]) {
      control.disabled = isBusy;
    }
  }

  function selectedTemplateDefaults() {
    return selectedTemplate?.parameters ?? [];
  }

  function renderParameterFields() {
    parameterFields.replaceChildren(
      ...selectedTemplateDefaults().map((parameter) => {
        let control;
        if (parameter.kind === "select") {
          control = createElement("select", {
            className: "form-control",
            dataset: { parameterKey: parameter.key, kind: parameter.kind },
            children: parameter.options.map((option) =>
              createElement("option", { text: option.label, attributes: { value: option.value } }),
            ),
          });
          control.value = String(parameter.default);
        } else {
          control = createElement("input", {
            className: "form-control",
            dataset: { parameterKey: parameter.key, kind: parameter.kind },
            attributes: {
              type: "number",
              value: parameter.default,
              min: parameter.minimum,
              max: parameter.maximum,
              step: parameter.step ?? (parameter.kind === "integer" ? "1" : "0.01"),
            },
          });
        }
        return field(parameter.label, control, parameter.description);
      }),
    );
  }

  function collectParameters() {
    const parameters = {};
    for (const control of parameterFields.querySelectorAll("input, select")) {
      const key = control.dataset.parameterKey;
      if (!key) continue;
      if (control.dataset.kind === "integer") parameters[key] = Number.parseInt(control.value, 10);
      else if (control.dataset.kind === "float") parameters[key] = Number.parseFloat(control.value);
      else parameters[key] = control.value;
    }
    return parameters;
  }

  function payload() {
    return {
      symbol: symbolSelect.value || "AAPL",
      market: marketInput.value || "US",
      timeframe: "1d",
      start: startInput.value || null,
      end: endInput.value || null,
      initial_cash: Number.parseFloat(cashInput.value || "0"),
      commission: Number.parseFloat(commissionInput.value || "0"),
      slippage: Number.parseFloat(slippageInput.value || "0"),
      parameters: collectParameters(),
    };
  }

  async function refreshStrategyPreview() {
    if (!selectedTemplate) return null;
    const rendered = await strategyService.renderTemplate(selectedTemplate.id, payload());
    lastStrategyJson = rendered.strategy_json;
    preview.update(lastStrategyJson);
    return lastStrategyJson;
  }

  function updateMetrics(metrics) {
    metricGrid.replaceChildren(
      createMetricCard({
        label: "Total return",
        value: formatPercent(metrics.total_return_pct),
        meta: "Final equity vs initial cash",
        tone: "accent",
      }),
      createMetricCard({
        label: "Sharpe ratio",
        value: metrics.sharpe_ratio === null ? "—" : formatPrice(metrics.sharpe_ratio),
        meta: "Daily returns, annualized",
      }),
      createMetricCard({
        label: "Max drawdown",
        value: formatPercent(metrics.max_drawdown_pct),
        meta: "Worst equity peak-to-trough",
      }),
      createMetricCard({
        label: "Trades",
        value: String(metrics.trade_count),
        meta: `Win rate ${formatPercent(metrics.win_rate_pct)}`,
        tone: "muted",
      }),
    );
  }

  function updateSteps(steps = []) {
    if (!steps.length) {
      stepList.replaceChildren(
        createElement("li", { className: "empty-copy", text: "Run a backtest to see steps." }),
      );
      return;
    }
    stepList.replaceChildren(
      ...steps.map((step, index) =>
        createElement("li", {
          className: "agent-step",
          dataset: { status: step.status },
          children: [
            createElement("span", { className: "agent-step__index", text: String(index + 1) }),
            createElement("div", {
              children: [
                createElement("strong", { text: step.key }),
                createElement("p", { text: step.message }),
              ],
            }),
          ],
        }),
      ),
    );
  }

  function updateWarnings(warnings = []) {
    if (!warnings.length) {
      warningsList.replaceChildren(
        createElement("li", { className: "empty-copy", text: "No warnings for this run." }),
      );
      return;
    }
    warningsList.replaceChildren(
      ...warnings.map((warning) =>
        createElement("li", {
          className: "backtest-warning-item",
          dataset: { severity: warning.severity },
          children: [
            createElement("strong", { text: warning.code }),
            createElement("p", { text: warning.message }),
          ],
        }),
      ),
    );
  }

  async function runBacktest() {
    if (!selectedTemplate) return;
    setBusy(true);
    setActivity("loading", "Rendering template and executing backtest…");
    try {
      const strategyJson = await refreshStrategyPreview();
      const result = await backtestService.run(strategyJson);
      if (destroyed) return;
      let overlayBars = [];
      let warnings = result.warnings ?? [];

      try {
        const overlay = await marketService.getOhlcv({
          symbol: result.symbol,
          start: result.data.start,
          end: result.data.end,
          includeIndicators: true,
        });
        overlayBars = overlay.bars ?? [];
      } catch (error) {
        warnings = [
          ...warnings,
          {
            code: "frontend_market_overlay_unavailable",
            severity: "warning",
            message: apiMessage(error),
          },
        ];
      }

      candlestickChart.update({ bars: overlayBars, trades: result.trades });
      updateMetrics(result.metrics);
      equityChart.update(result.equity_curve);
      drawdownChart.update(result.drawdown_curve);
      tradeTable.update(result.trades);
      updateSteps(result.agent_steps);
      updateWarnings(warnings);
      setActivity(
        "success",
        `${result.strategy_name}: ${result.metrics.trade_count} trade(s), ${formatPercent(result.metrics.total_return_pct)} total return.`,
      );
    } catch (error) {
      if (!destroyed) setActivity("error", apiMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  async function loadSymbols() {
    try {
      const response = await marketService.getSymbols();
      if (destroyed) return;
      symbolSelect.replaceChildren(
        ...response.symbols.map((symbol) =>
          createElement("option", {
            text: `${symbol.symbol} — ${symbol.name}`,
            attributes: { value: symbol.symbol },
          }),
        ),
      );
      const first = response.symbols[0];
      if (first) {
        symbolSelect.value = first.symbol;
        marketInput.value = first.market;
        startInput.value = first.first_cached_date ?? startInput.value;
        endInput.value = first.last_cached_date ?? endInput.value;
      }
    } catch {
      symbolSelect.replaceChildren(
        ...["AAPL", "SPY", "QQQ"].map((symbol) =>
          createElement("option", { text: symbol, attributes: { value: symbol } }),
        ),
      );
    }
  }

  async function initialize() {
    setBusy(true);
    try {
      await loadSymbols();
      const response = await strategyService.getTemplates();
      if (destroyed) return;
      templates = response.templates;
      templateSelect.replaceChildren(
        ...templates.map((template) =>
          createElement("option", { text: template.name, attributes: { value: template.id } }),
        ),
      );
      selectedTemplate =
        templates.find((template) => template.id === "ma_crossover_rsi") ?? templates[0];
      templateSelect.value = selectedTemplate.id;
      renderParameterFields();
      await refreshStrategyPreview();
      updateSteps();
      updateWarnings();
      setActivity("success", "Ready to run an interactive Phase 5 backtest workflow.");
    } catch (error) {
      if (!destroyed) setActivity("error", apiMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  templateSelect.addEventListener("change", async () => {
    selectedTemplate = templates.find((template) => template.id === templateSelect.value) ?? null;
    renderParameterFields();
    setActivity("loading", "Rendering selected template…");
    try {
      await refreshStrategyPreview();
      setActivity("success", "Strategy JSON preview updated.");
    } catch (error) {
      setActivity("error", apiMessage(error));
    }
  });
  for (const control of [
    symbolSelect,
    marketInput,
    startInput,
    endInput,
    cashInput,
    commissionInput,
    slippageInput,
  ]) {
    control.addEventListener("change", () => {
      refreshStrategyPreview().catch((error) => setActivity("error", apiMessage(error)));
    });
  }
  runButton.addEventListener("click", runBacktest);

  initialize();

  return {
    element,
    destroy() {
      destroyed = true;
    },
  };
}
