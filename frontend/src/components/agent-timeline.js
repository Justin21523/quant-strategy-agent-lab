import { createElement } from "../core/dom.js";

export const BACKTEST_WORKFLOW_STEPS = [
  {
    sequence: 1,
    key: "strategy_received",
    label: "Strategy received",
    description: "Capture the rendered Strategy JSON DSL and execution assumptions.",
    status: "pending",
  },
  {
    sequence: 2,
    key: "validate_strategy",
    label: "Strategy validated",
    description: "Validate DSL structure, indicator references, and supported rule types.",
    status: "pending",
  },
  {
    sequence: 3,
    key: "fetch_market_data",
    label: "Market data loaded",
    description: "Load normalized OHLCV bars from the market data layer.",
    status: "pending",
  },
  {
    sequence: 4,
    key: "compute_indicators",
    label: "Indicators computed",
    description: "Build the technical indicator feature frame required by the strategy.",
    status: "pending",
  },
  {
    sequence: 5,
    key: "generate_signals",
    label: "Signals generated",
    description: "Evaluate entry and exit rules on completed bars without look-ahead.",
    status: "pending",
  },
  {
    sequence: 6,
    key: "run_backtest",
    label: "Backtest executed",
    description: "Apply deterministic long-only order execution, fees, and slippage.",
    status: "pending",
  },
  {
    sequence: 7,
    key: "analyze_performance",
    label: "Performance analyzed",
    description: "Compute returns, Sharpe, drawdown, exposure, and trade metrics.",
    status: "pending",
  },
  {
    sequence: 8,
    key: "risk_review",
    label: "Risk notes reviewed",
    description: "Summarize data, sample-size, and execution warnings for the run.",
    status: "pending",
  },
];

const STATUS_PRIORITY = {
  failed: 6,
  error: 6,
  warning: 5,
  running: 4,
  success: 3,
  cancelled: 2,
  pending: 1,
};

function titleCase(value) {
  return String(value ?? "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusOrPending(value) {
  return Object.hasOwn(STATUS_PRIORITY, value) ? value : "pending";
}

export function normalizeAgentStep(step, index = 0) {
  if (Array.isArray(step)) {
    return {
      sequence: index + 1,
      key: `step_${index + 1}`,
      label: step[0] ?? `Step ${index + 1}`,
      description: step[1] ?? "",
      status: "pending",
      message: step[1] ?? "",
      detail: {},
    };
  }

  const key = step?.key ?? `step_${index + 1}`;
  return {
    sequence: Number(step?.sequence) || index + 1,
    key,
    label: step?.label ?? titleCase(key),
    description: step?.description ?? "",
    status: statusOrPending(step?.status),
    message: step?.message ?? step?.description ?? "Pending execution.",
    detail: step?.detail ?? {},
    duration_ms: step?.duration_ms ?? null,
  };
}

export function mergeAgentSteps(baseSteps = BACKTEST_WORKFLOW_STEPS, actualSteps = []) {
  const merged = baseSteps.map((step, index) => normalizeAgentStep(step, index));
  const byKey = new Map(merged.map((step, index) => [step.key, index]));

  for (const rawStep of actualSteps) {
    const normalized = normalizeAgentStep(rawStep, merged.length);
    if (byKey.has(normalized.key)) {
      const index = byKey.get(normalized.key);
      merged[index] = { ...merged[index], ...normalized, sequence: merged[index].sequence };
    } else {
      byKey.set(normalized.key, merged.length);
      merged.push(normalized);
    }
  }

  return merged.sort((left, right) => left.sequence - right.sequence);
}

export function summarizeAgentProgress(steps = []) {
  const normalized = steps.map((step, index) => normalizeAgentStep(step, index));
  const counts = normalized.reduce(
    (summary, step) => {
      summary[step.status] = (summary[step.status] ?? 0) + 1;
      return summary;
    },
    { pending: 0, running: 0, success: 0, warning: 0, failed: 0, error: 0, cancelled: 0 },
  );
  const completed = counts.success + counts.warning;
  const failed = counts.failed + counts.error;
  const total = normalized.length;
  const progressPct = total ? Math.round(((completed + failed) / total) * 100) : 0;
  const dominantStatus = normalized.reduce(
    (current, step) =>
      STATUS_PRIORITY[step.status] > STATUS_PRIORITY[current] ? step.status : current,
    "pending",
  );

  return { ...counts, completed, failed, total, progressPct, dominantStatus };
}

function formatDuration(durationMs) {
  const value = Number(durationMs);
  if (!Number.isFinite(value)) return "";
  if (value < 1000) return `${Math.round(value)} ms`;
  return `${(value / 1000).toFixed(2)} s`;
}

function detailBlock(detail) {
  if (!detail || Object.keys(detail).length === 0) return null;
  return createElement("pre", {
    className: "agent-step__detail",
    text: JSON.stringify(detail, null, 2),
  });
}

function renderStep(step) {
  const detail = createElement("details", {
    className: "agent-step__body",
    children: [
      createElement("summary", {
        children: [
          createElement("strong", { text: step.label }),
          createElement("span", { className: "agent-step__status", text: step.status }),
        ],
      }),
      createElement("p", { text: step.message || step.description }),
      step.description && step.message !== step.description
        ? createElement("small", { className: "agent-step__description", text: step.description })
        : null,
      step.duration_ms !== null
        ? createElement("small", {
            className: "agent-step__duration",
            text: formatDuration(step.duration_ms),
          })
        : null,
      detailBlock(step.detail),
    ],
  });

  return createElement("li", {
    className: "agent-step",
    dataset: { status: step.status, key: step.key },
    children: [
      createElement("span", { className: "agent-step__index", text: String(step.sequence) }),
      detail,
    ],
  });
}

function coerceTimelineInput(input) {
  if (Array.isArray(input)) return input;
  return input?.steps ?? BACKTEST_WORKFLOW_STEPS;
}

export function createAgentTimeline(input = {}) {
  let steps = mergeAgentSteps(BACKTEST_WORKFLOW_STEPS, coerceTimelineInput(input));

  const summaryText = createElement("strong", { text: "Waiting for execution" });
  const summaryMeta = createElement("span", { text: "0 / 8 completed" });
  const progressFill = createElement("span", { className: "agent-timeline-progress__fill" });
  const list = createElement("ol", { className: "agent-timeline" });
  const element = createElement("div", {
    className: "agent-timeline-shell",
    children: [
      createElement("div", {
        className: "agent-timeline-summary",
        children: [summaryText, summaryMeta],
      }),
      createElement("div", {
        className: "agent-timeline-progress",
        attributes: { "aria-hidden": "true" },
        children: [progressFill],
      }),
      list,
    ],
  });

  function render(nextSteps = steps) {
    steps = nextSteps.map((step, index) => normalizeAgentStep(step, index));
    const summary = summarizeAgentProgress(steps);
    element.dataset.status = summary.dominantStatus;
    summaryText.textContent =
      summary.failed > 0
        ? `${summary.failed} step(s) failed`
        : summary.running > 0
          ? `${summary.running} step(s) running`
          : summary.warning > 0
            ? `${summary.warning} warning step(s)`
            : summary.completed === summary.total
              ? "Workflow completed"
              : "Workflow pending";
    summaryMeta.textContent = `${summary.completed + summary.failed} / ${summary.total} finished`;
    progressFill.style.width = `${summary.progressPct}%`;
    list.replaceChildren(...steps.map(renderStep));
  }

  element.update = (actualSteps = [], { baseSteps = BACKTEST_WORKFLOW_STEPS } = {}) => {
    render(mergeAgentSteps(baseSteps, actualSteps));
  };

  element.markRunning = (key = "strategy_received", message = "Running step…") => {
    element.update([{ key, status: "running", message }]);
  };

  element.markFailed = (message = "Workflow failed before the engine returned steps.") => {
    element.update([
      {
        key: "strategy_received",
        status: "success",
        message: "Strategy execution was requested.",
      },
      { key: "validate_strategy", status: "failed", message },
    ]);
  };

  render(steps);
  return element;
}
