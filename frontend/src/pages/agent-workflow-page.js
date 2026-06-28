import { createAgentTimeline } from "../components/agent-timeline.js";
import { createElement } from "../core/dom.js";
import { agentService } from "../services/agent-service.js";

function workflowCard(step) {
  return createElement("article", {
    className: "agent-workflow-card",
    dataset: { status: step.status },
    children: [
      createElement("span", {
        className: "agent-workflow-card__sequence",
        text: String(step.sequence),
      }),
      createElement("div", {
        children: [
          createElement("h3", { text: step.label }),
          createElement("p", { text: step.description }),
          createElement("code", { text: step.key }),
        ],
      }),
    ],
  });
}

export function createAgentWorkflowPage() {
  let destroyed = false;
  const timeline = createAgentTimeline();
  const cards = createElement("div", { className: "agent-workflow-grid" });
  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "loading" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Loading canonical workflow metadata…",
  });

  const element = createElement("section", {
    className: "page agent-workflow-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Phase 6 · Agent Timeline MVP" }),
          createElement("h1", { text: "Backtests are now inspectable Agent workflows." }),
          createElement("p", {
            text: "This page exposes the canonical workflow used by the Backtest Lab. Each run can now show pending, running, success, warning, and failed states with expandable execution details.",
          }),
        ],
      }),
      activity,
      createElement("div", {
        className: "content-grid content-grid--two",
        children: [
          createElement("article", {
            className: "panel",
            attributes: { "data-guide": "agent-timeline" },
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Timeline" }),
                      createElement("h2", { text: "Canonical backtest steps" }),
                    ],
                  }),
                  createElement("span", { className: "phase-chip", text: "Phase 06" }),
                ],
              }),
              timeline,
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
                      createElement("span", { className: "eyebrow", text: "Contract" }),
                      createElement("h2", { text: "Backend workflow metadata" }),
                    ],
                  }),
                ],
              }),
              cards,
            ],
          }),
        ],
      }),
      createElement("aside", {
        className: "disclaimer",
        children: [
          createElement("strong", { text: "No black-box button" }),
          createElement("p", {
            text: "The timeline is intentionally visible so the system shows what data it loaded, what features it computed, which rules produced signals, and which warnings affect interpretation.",
          }),
        ],
      }),
    ],
  });

  async function initialize() {
    try {
      const workflow = await agentService.getBacktestWorkflow();
      if (destroyed) return;
      timeline.update(workflow.steps);
      cards.replaceChildren(...workflow.steps.map(workflowCard));
      activity.dataset.status = "success";
      activity.textContent = `${workflow.label}: ${workflow.total_steps} inspectable steps loaded.`;
    } catch (error) {
      if (destroyed) return;
      activity.dataset.status = "error";
      activity.textContent = error?.message ?? "Unable to load workflow metadata.";
    }
  }

  initialize();

  return {
    element,
    destroy() {
      destroyed = true;
    },
  };
}
