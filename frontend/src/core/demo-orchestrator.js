import { createElement } from "./dom.js";
import { demoService } from "../services/demo-service.js";
import { jobService } from "../services/job-service.js";

const TOUR_STEPS = [
  ["/", "Loading research demo snapshot"],
  ["/market-data", "Inspecting synthetic multi-ticker market data"],
  ["/data-quality", "Checking data-quality pass/fail cases"],
  ["/parameter-scanner", "Running scanner workflow"],
  ["/jobs", "Watching long-running job progress"],
  ["/portfolio-rebalance", "Reviewing portfolio preset matrix"],
  ["/comparison", "Comparing strategy templates across symbols"],
  ["/performance-report", "Inspecting final performance report"],
  ["/", "Research demo complete"],
];

let activeRun = null;

function sleep(ms) {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms));
}

function createOverlay() {
  const status = createElement("strong", { text: "Preparing demo..." });
  const detail = createElement("span", { text: "Starting browser-guided research workflow." });
  const progress = createElement("span", { text: "0/0" });
  const stopButton = createElement("button", {
    className: "button button--secondary button--small",
    text: "Stop",
    attributes: { type: "button" },
  });
  const element = createElement("aside", {
    className: "demo-overlay",
    attributes: { "data-testid": "demo-overlay" },
    children: [
      createElement("div", {
        children: [createElement("span", { className: "eyebrow", text: "Auto Demo" }), status],
      }),
      detail,
      createElement("div", {
        className: "demo-overlay__footer",
        children: [progress, stopButton],
      }),
    ],
  });
  document.body.append(element);
  return {
    element,
    stopButton,
    update({ title, message, processed = 0, total = 0 }) {
      status.textContent = title;
      detail.textContent = message;
      progress.textContent = `${processed}/${total}`;
    },
    remove() {
      element.remove();
    },
  };
}

async function pollJob(jobId, overlay, state) {
  const deadline = Date.now() + 120_000;
  while (!state.cancelled && Date.now() < deadline) {
    const job = await jobService.get(jobId);
    overlay.update({
      title: job.status,
      message: job.message,
      processed: job.processed,
      total: job.total,
    });
    if (["success", "failed", "cancelled"].includes(job.status)) return job;
    await sleep(700);
  }
  throw new Error(`Demo job timed out: ${jobId}`);
}

async function runRouteTour(overlay, state) {
  for (const [route, message] of TOUR_STEPS) {
    if (state.cancelled) return;
    overlay.update({ title: "Touring app", message, processed: 0, total: TOUR_STEPS.length });
    globalThis.location.hash = `#${route}`;
    await sleep(950);
  }
}

export async function activateResearchDemo({ onComplete, onError } = {}) {
  if (activeRun) return activeRun;
  const state = { cancelled: false };
  const overlay = createOverlay();
  overlay.stopButton.addEventListener("click", () => {
    state.cancelled = true;
    overlay.update({ title: "Stopped", message: "Demo automation was stopped." });
    activeRun = null;
    globalThis.setTimeout(() => overlay.remove(), 700);
  });

  activeRun = (async () => {
    try {
      overlay.update({ title: "Queued", message: "Queueing full research demo workflow." });
      const job = await jobService.queueResearchDemo();
      const tour = runRouteTour(overlay, state);
      const finishedJob = await pollJob(job.job_id, overlay, state);
      await tour;
      if (state.cancelled) return null;
      if (finishedJob.status !== "success") {
        throw new Error(finishedJob.error ?? `Demo job ended with ${finishedJob.status}`);
      }
      const latest = await demoService.latest();
      overlay.update({
        title: "Complete",
        message: "Research demo completed. Dashboard summary is refreshed.",
        processed: finishedJob.processed,
        total: finishedJob.total,
      });
      globalThis.location.hash = "#/";
      await sleep(900);
      overlay.remove();
      onComplete?.(latest.summary);
      return latest.summary;
    } catch (error) {
      overlay.update({
        title: "Demo failed",
        message: error?.message ?? "Unexpected demo automation error.",
      });
      onError?.(error);
      throw error;
    } finally {
      activeRun = null;
    }
  })();

  return activeRun;
}
