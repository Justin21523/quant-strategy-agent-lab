import { ApiError } from "../core/api-client.js";
import { createElement } from "../core/dom.js";
import { jobService } from "../services/job-service.js";
import { formatInteger } from "../utils/market-formatters.js";

function errorMessage(error) {
  if (error instanceof ApiError) return error.details?.error?.message ?? error.message;
  return error?.message ?? "Unexpected job error.";
}

export function createJobsPage() {
  let destroyed = false;
  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "idle" },
    attributes: { role: "status", "aria-live": "polite" },
    text: "Polling queued and running jobs.",
  });
  const refreshButton = createElement("button", {
    className: "button button--secondary",
    text: "Refresh",
    attributes: { type: "button", "data-testid": "jobs-refresh-button" },
  });
  const tableBody = createElement("tbody");
  const summary = createElement("div", {
    className: "metric-grid",
    attributes: { "data-testid": "jobs-summary" },
  });

  const element = createElement("section", {
    className: "page jobs-page",
    children: [
      createElement("header", {
        className: "page-header page-header--wide",
        children: [
          createElement("span", { className: "eyebrow", text: "Jobs" }),
          createElement("h1", { text: "Long-running task queue." }),
          createElement("p", {
            text: "Monitor queued market syncs, scanner runs, and portfolio rebalance jobs.",
          }),
        ],
      }),
      activity,
      createElement("div", { className: "form-actions", children: [refreshButton] }),
      summary,
      createElement("section", {
        className: "panel",
        attributes: { "data-guide": "jobs-monitor" },
        children: [
          createElement("div", {
            className: "panel__header",
            children: [
              createElement("div", {
                children: [
                  createElement("span", { className: "eyebrow", text: "Queue" }),
                  createElement("h2", { text: "Recent jobs" }),
                ],
              }),
            ],
          }),
          createElement("div", {
            className: "table-scroll",
            children: [
              createElement("table", {
                className: "data-table",
                attributes: { "data-testid": "jobs-table" },
                children: [
                  createElement("thead", {
                    children: [
                      createElement("tr", {
                        children: [
                          "Job",
                          "Kind",
                          "Status",
                          "Progress",
                          "Message",
                          "Result",
                          "Error",
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

  function metricCard(label, value) {
    return createElement("article", {
      className: "metric-card",
      children: [
        createElement("span", { className: "metric-card__label", text: label }),
        createElement("strong", { text: String(value) }),
      ],
    });
  }

  function jobRow(job) {
    return createElement("tr", {
      children: [
        createElement("td", { text: job.job_id }),
        createElement("td", { text: job.kind }),
        createElement("td", { text: job.status }),
        createElement("td", {
          text: `${formatInteger(job.processed)}/${formatInteger(job.total)}`,
        }),
        createElement("td", { text: job.message }),
        createElement("td", {
          text: job.result_id ? `${job.result_type}: ${job.result_id}` : "-",
        }),
        createElement("td", { text: job.error ?? "-" }),
      ],
    });
  }

  async function loadJobs() {
    try {
      const response = await jobService.list({ limit: 50 });
      if (destroyed) return;
      const running = response.jobs.filter((job) => job.status === "running").length;
      const pending = response.jobs.filter((job) => job.status === "pending").length;
      summary.replaceChildren(
        metricCard("Jobs", formatInteger(response.total)),
        metricCard("Running", formatInteger(running)),
        metricCard("Pending", formatInteger(pending)),
        metricCard("Latest", response.jobs[0]?.status ?? "-"),
      );
      tableBody.replaceChildren(...response.jobs.map(jobRow));
      setActivity("success", "Jobs loaded.");
    } catch (error) {
      if (!destroyed) setActivity("error", errorMessage(error));
    }
  }

  refreshButton.addEventListener("click", loadJobs);
  const interval = globalThis.setInterval(loadJobs, 2500);
  loadJobs();

  return {
    element,
    destroy() {
      destroyed = true;
      globalThis.clearInterval(interval);
    },
  };
}
