import { createStrategyJsonPreview } from "../components/strategy-json-preview.js";
import { createStrategyValidationList } from "../components/strategy-validation-list.js";
import { ApiError } from "../core/api-client.js";
import { createElement } from "../core/dom.js";
import { marketService } from "../services/market-service.js";
import { strategyService } from "../services/strategy-service.js";

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

function apiMessage(error) {
  if (error instanceof ApiError) {
    return error.details?.error?.message ?? error.message;
  }
  return error?.message ?? "Unexpected strategy-template error.";
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

export function createStrategyBuilderPage() {
  let destroyed = false;
  let renderTimer = 0;
  let templates = [];
  let selectedTemplate = null;
  let lastRendered = null;

  const templateList = createElement("div", { className: "template-list" });
  const parameterFields = createElement("div", { className: "strategy-parameter-grid" });
  const templateMeta = createElement("dl", { className: "metadata-list" });
  const validation = createStrategyValidationList();
  const preview = createStrategyJsonPreview();

  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Loading deterministic strategy templates…",
  });

  const symbolSelect = createElement("select", {
    className: "form-control",
    attributes: { name: "symbol" },
  });
  const marketInput = createElement("input", {
    className: "form-control",
    attributes: { name: "market", value: "US", maxlength: "12" },
  });
  const startInput = createElement("input", {
    className: "form-control",
    attributes: { type: "date", name: "start", value: "2023-01-03" },
  });
  const endInput = createElement("input", {
    className: "form-control",
    attributes: { type: "date", name: "end", value: "2025-12-31", max: today() },
  });
  const cashInput = createElement("input", {
    className: "form-control",
    attributes: { type: "number", name: "initial_cash", value: "100000", min: "0", step: "1000" },
  });
  const commissionInput = createElement("input", {
    className: "form-control",
    attributes: {
      type: "number",
      name: "commission",
      value: "0.001",
      min: "0",
      max: "1",
      step: "0.0001",
    },
  });
  const slippageInput = createElement("input", {
    className: "form-control",
    attributes: {
      type: "number",
      name: "slippage",
      value: "0.0005",
      min: "0",
      max: "1",
      step: "0.0001",
    },
  });

  const copyButton = createElement("button", {
    className: "button button--secondary button--small",
    text: "Copy JSON",
    attributes: { type: "button" },
  });

  const element = createElement("section", {
    className: "page strategy-builder-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", {
            className: "eyebrow",
            text: "Phase 3 · Strategy Template System",
          }),
          createElement("h1", { text: "Build safe Strategy JSON DSL before backtesting." }),
          createElement("p", {
            text: "Select a deterministic strategy template, edit typed parameters, and preview the exact JSON contract that Phase 4 will use to generate signals. No arbitrary Python execution. No mystery meat.",
          }),
        ],
      }),
      activity,
      createElement("div", {
        className: "strategy-builder-layout",
        children: [
          createElement("article", {
            className: "panel template-panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Templates" }),
                      createElement("h2", { text: "Pick a strategy family" }),
                    ],
                  }),
                  createElement("span", { className: "phase-chip", text: "5 MVP templates" }),
                ],
              }),
              templateList,
            ],
          }),
          createElement("article", {
            className: "panel strategy-editor-panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Context + Parameters" }),
                      createElement("h2", { text: "Typed strategy form" }),
                    ],
                  }),
                  createElement("span", { className: "phase-chip", text: "Live render" }),
                ],
              }),
              createElement("div", {
                className: "form-grid form-grid--strategy-context",
                children: [
                  field(
                    "Symbol",
                    symbolSelect,
                    "Loaded from Phase 1 symbol catalog when available.",
                  ),
                  field("Market", marketInput),
                  field("Start", startInput),
                  field("End", endInput),
                  field("Initial cash", cashInput),
                  field("Commission", commissionInput, "Fraction, e.g. 0.001 = 0.1%."),
                  field("Slippage", slippageInput, "Fractional assumed execution friction."),
                ],
              }),
              createElement("hr", { className: "panel-separator" }),
              parameterFields,
            ],
          }),
          createElement("article", {
            className: "panel strategy-preview-panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Strategy JSON DSL" }),
                      createElement("h2", { text: "Authoritative preview" }),
                    ],
                  }),
                  copyButton,
                ],
              }),
              preview.element,
            ],
          }),
        ],
      }),
      createElement("div", {
        className: "content-grid content-grid--two strategy-secondary-grid",
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
                      createElement("h2", { text: "Backend structural checks" }),
                    ],
                  }),
                ],
              }),
              validation.element,
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
                      createElement("span", { className: "eyebrow", text: "Template metadata" }),
                      createElement("h2", { text: "Risk notes and indicator needs" }),
                    ],
                  }),
                ],
              }),
              templateMeta,
            ],
          }),
        ],
      }),
      createElement("aside", {
        className: "disclaimer",
        children: [
          createElement("strong", { text: "Backtest disclaimer" }),
          createElement("p", {
            text: "These templates create research DSL only. Historical backtests in later phases can evaluate past behavior but cannot guarantee future performance or provide investment advice.",
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
      symbolSelect,
      marketInput,
      startInput,
      endInput,
      cashInput,
      commissionInput,
      slippageInput,
      copyButton,
      ...parameterFields.querySelectorAll("input, select"),
    ]) {
      control.disabled = isBusy;
    }
  }

  function selectTemplate(templateId) {
    selectedTemplate = templates.find((template) => template.id === templateId) ?? templates[0];
    renderTemplateList();
    renderParameterFields();
    renderTemplateMetadata();
    scheduleRender();
  }

  function renderTemplateList() {
    templateList.replaceChildren(
      ...templates.map((template) =>
        createElement("button", {
          className: "template-card",
          dataset: { selected: template.id === selectedTemplate?.id ? "true" : "false" },
          attributes: { type: "button" },
          on: { click: () => selectTemplate(template.id) },
          children: [
            createElement("strong", { text: template.name }),
            createElement("p", { text: template.summary }),
            createElement("small", {
              text: `${template.category} · ${template.indicator_kinds.join(" + ") || "no indicators"}`,
            }),
          ],
        }),
      ),
    );
  }

  function renderParameterFields() {
    if (!selectedTemplate) return;
    parameterFields.replaceChildren(
      ...selectedTemplate.parameters.map((parameter) => {
        let control;
        if (parameter.kind === "select") {
          control = createElement("select", {
            className: "form-control",
            dataset: { parameterKey: parameter.key, kind: parameter.kind },
            children: parameter.options.map((option) =>
              createElement("option", {
                text: option.label,
                attributes: { value: option.value },
              }),
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
        control.addEventListener("input", scheduleRender);
        control.addEventListener("change", scheduleRender);
        return field(
          parameter.label,
          control,
          `${parameter.description}${parameter.unit ? ` · ${parameter.unit}` : ""}`,
        );
      }),
    );
  }

  function renderTemplateMetadata() {
    if (!selectedTemplate) return;
    templateMeta.replaceChildren(
      metadataRow("Template", selectedTemplate.name),
      metadataRow("Category", selectedTemplate.category),
      metadataRow("Tags", selectedTemplate.tags.join(", ")),
      metadataRow("Indicators", selectedTemplate.indicator_kinds.join(", ") || "None"),
      metadataRow("Description", selectedTemplate.description),
      metadataRow("Risk notes", selectedTemplate.risk_notes.join(" ") || "No extra notes."),
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

  function scheduleRender() {
    window.clearTimeout(renderTimer);
    renderTimer = window.setTimeout(renderSelectedTemplate, 180);
  }

  async function renderSelectedTemplate() {
    if (!selectedTemplate) return;
    setBusy(true);
    setActivity("loading", `Rendering ${selectedTemplate.name} into Strategy JSON DSL…`);
    try {
      const response = await strategyService.renderTemplate(selectedTemplate.id, payload());
      if (destroyed) return;
      lastRendered = response.strategy_json;
      preview.update(response.strategy_json);
      validation.update(response.validation);
      setActivity(
        response.validation.valid ? "success" : "warning",
        `${response.template.name}: rendered ${response.required_indicators.length} indicator dependency${response.required_indicators.length === 1 ? "" : "ies"}.`,
      );
    } catch (error) {
      if (destroyed) return;
      validation.update({
        issues: [
          {
            code: "render_failed",
            severity: "error",
            message: apiMessage(error),
            path: "template.parameters",
          },
        ],
      });
      setActivity("error", apiMessage(error));
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

  async function loadTemplates() {
    setBusy(true);
    try {
      await loadSymbols();
      const response = await strategyService.getTemplates();
      if (destroyed) return;
      templates = response.templates;
      selectedTemplate =
        templates.find((template) => template.id === "ma_crossover_rsi") ?? templates[0];
      renderTemplateList();
      renderParameterFields();
      renderTemplateMetadata();
      await renderSelectedTemplate();
    } catch (error) {
      if (!destroyed) setActivity("error", apiMessage(error));
    } finally {
      if (!destroyed) setBusy(false);
    }
  }

  for (const control of [
    symbolSelect,
    marketInput,
    startInput,
    endInput,
    cashInput,
    commissionInput,
    slippageInput,
  ]) {
    control.addEventListener("input", scheduleRender);
    control.addEventListener("change", scheduleRender);
  }

  symbolSelect.addEventListener("change", () => {
    const selected = [...symbolSelect.options].find(
      (option) => option.value === symbolSelect.value,
    );
    if (selected?.textContent?.includes("—")) marketInput.value = "US";
  });

  copyButton.addEventListener("click", async () => {
    if (!lastRendered) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(lastRendered, null, 2));
      setActivity("success", "Strategy JSON copied to clipboard.");
    } catch {
      setActivity("warning", "Clipboard unavailable; select the JSON preview manually.");
    }
  });

  loadTemplates();

  return {
    element,
    destroy() {
      destroyed = true;
      window.clearTimeout(renderTimer);
    },
  };
}
