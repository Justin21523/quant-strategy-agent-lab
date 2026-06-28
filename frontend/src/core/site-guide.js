import { createElement } from "./dom.js";

export const GUIDE_STEPS = [
  {
    route: "/",
    target: "shell-sidebar",
    title: "Shell Navigation",
    description: "Use the left navigation to move across the research workflow modules.",
  },
  {
    route: "/",
    target: "shell-topbar",
    title: "API + Docs",
    description: "Check API health, latency, documentation, and restart this guide from here.",
  },
  {
    route: "/",
    target: "demo-hero",
    title: "Demo Dashboard",
    description: "Start with the complete sample research playback on the dashboard.",
  },
  {
    route: "/",
    target: "demo-playback",
    title: "Demo Playback",
    description: "Review the visual research stages: load, quality, scan, portfolio, and report.",
  },
  {
    route: "/research-lab",
    target: "research-builder",
    title: "Research Lab Builder",
    description: "Edit pipeline inputs, scanner settings, portfolio matrix, and reusable presets.",
  },
  {
    route: "/research-lab",
    target: "research-progress",
    title: "Research Pipeline Run",
    description:
      "Watch sync, quality, scanner, portfolio, and strategy jobs finish as one pipeline.",
  },
  {
    route: "/report-center",
    target: "report-preview",
    title: "Report Center",
    description: "Preview Markdown and export JSON or CSV artifacts from completed research runs.",
  },
  {
    route: "/market-data",
    target: "market-indicators",
    title: "Market + Indicators",
    description: "Inspect cached OHLCV, SMA overlays, RSI, provenance, and quality warnings.",
  },
  {
    route: "/strategy-builder",
    target: "strategy-editor",
    title: "Strategy Builder",
    description: "Turn deterministic templates into validated Strategy JSON DSL.",
  },
  {
    route: "/backtest-lab",
    target: "backtest-chart",
    title: "Backtest Lab",
    description:
      "Run single-strategy backtests with candles, trades, equity, drawdown, and metrics.",
  },
  {
    route: "/agent-workflow",
    target: "agent-timeline",
    title: "Agent Workflow",
    description:
      "Open the transparent execution timeline for data, indicator, signal, and risk steps.",
  },
  {
    route: "/parameter-scanner",
    target: "scanner-workbench",
    title: "Scanner",
    description:
      "Rank many symbols with configurable technical filters and skipped-symbol reasons.",
  },
  {
    route: "/data-quality",
    target: "data-quality-report",
    title: "Data Quality",
    description: "Check cached bars, missing dates, fixture flags, and indicator readiness.",
  },
  {
    route: "/portfolio-rebalance",
    target: "portfolio-workbench",
    title: "Portfolio Rebalance",
    description: "Build weekly or monthly equal-weight portfolios from scanner selections.",
  },
  {
    route: "/jobs",
    target: "jobs-monitor",
    title: "Jobs + Performance",
    description:
      "Monitor long tasks, then use performance and comparison pages to evaluate results.",
  },
];

const GUIDE_AUTO_SESSION_KEY = "qsa_site_guide_dismissed";

function sleep(ms) {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms));
}

function routeFromHash() {
  const raw = globalThis.location.hash.replace(/^#/, "");
  const path = raw.split("?")[0] || "/";
  return path.startsWith("/") ? path : `/${path}`;
}

function targetSelector(target) {
  return `[data-guide="${target}"]`;
}

export function resolveGuideTarget(target, root = document) {
  return (
    root.querySelector(targetSelector(target)) ||
    root.querySelector(".page-header") ||
    root.querySelector("[data-router-outlet]")
  );
}

export function createSiteGuide({ steps = GUIDE_STEPS, autoDelayMs = 500 } = {}) {
  let active = false;
  let index = 0;
  let resizeHandler = null;
  let scrollHandler = null;
  let targetElement = null;

  const masks = ["top", "right", "bottom", "left"].map((part) =>
    createElement("div", { className: `site-guide-mask site-guide-mask--${part}` }),
  );
  const ring = createElement("div", { className: "site-guide-ring" });
  const particles = createElement("div", {
    className: "site-guide-particles",
    attributes: { "aria-hidden": "true" },
    children: Array.from({ length: 14 }, (_, particleIndex) =>
      createElement("span", {
        attributes: {
          style: `--i: ${particleIndex}; --x: ${((particleIndex * 37) % 100).toFixed(0)}%;`,
        },
      }),
    ),
  });
  const eyebrow = createElement("span", { className: "eyebrow", text: "Site Guide" });
  const title = createElement("strong", { text: "Guide" });
  const description = createElement("p", { text: "" });
  const progress = createElement("span", { className: "site-guide-card__progress", text: "0 / 0" });
  const backButton = createElement("button", {
    className: "button button--secondary button--small",
    text: "Back",
    attributes: { type: "button" },
  });
  const nextButton = createElement("button", {
    className: "button button--primary button--small",
    text: "Next",
    attributes: { type: "button", "data-testid": "site-guide-next" },
  });
  const restartButton = createElement("button", {
    className: "button button--secondary button--small",
    text: "Restart",
    attributes: { type: "button" },
  });
  const skipButton = createElement("button", {
    className: "button button--secondary button--small",
    text: "Skip",
    attributes: { type: "button", "data-testid": "site-guide-skip" },
  });
  const card = createElement("aside", {
    className: "site-guide-card",
    attributes: {
      role: "dialog",
      "aria-live": "polite",
      "aria-label": "Site guide",
      "data-testid": "site-guide-card",
    },
    children: [
      createElement("div", {
        className: "site-guide-card__header",
        children: [createElement("div", { children: [eyebrow, title] }), progress],
      }),
      description,
      createElement("div", {
        className: "site-guide-card__actions",
        children: [backButton, nextButton, restartButton, skipButton],
      }),
    ],
  });
  const layer = createElement("div", {
    className: "site-guide",
    attributes: { "data-testid": "site-guide" },
    children: [...masks, ring, particles, card],
  });

  async function update() {
    if (!active) return;
    const step = steps[index];
    if (!step) return;
    if (routeFromHash() !== step.route) {
      globalThis.location.hash = `#${step.route}`;
      await sleep(180);
    }
    await sleep(80);
    targetElement = resolveGuideTarget(step.target);
    title.textContent = step.title;
    description.textContent = step.description;
    progress.textContent = `${String(index + 1).padStart(2, "0")} / ${steps.length}`;
    backButton.disabled = index === 0;
    nextButton.textContent = index === steps.length - 1 ? "Done" : "Next";
    targetElement?.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" });
    await sleep(160);
    position();
  }

  function refresh() {
    if (!active) return;
    const step = steps[index];
    if (!step || routeFromHash() !== step.route) return;
    targetElement = resolveGuideTarget(step.target);
    position();
  }

  function position() {
    if (!active || !targetElement?.isConnected) return;
    const rect = targetElement.getBoundingClientRect();
    const margin = 10;
    const top = Math.max(0, rect.top - margin);
    const left = Math.max(0, rect.left - margin);
    const right = Math.min(globalThis.innerWidth, rect.right + margin);
    const bottom = Math.min(globalThis.innerHeight, rect.bottom + margin);

    masks[0].style.cssText = `left:0;top:0;width:100vw;height:${top}px;`;
    masks[1].style.cssText = `left:${right}px;top:${top}px;width:${globalThis.innerWidth - right}px;height:${bottom - top}px;`;
    masks[2].style.cssText = `left:0;top:${bottom}px;width:100vw;height:${globalThis.innerHeight - bottom}px;`;
    masks[3].style.cssText = `left:0;top:${top}px;width:${left}px;height:${bottom - top}px;`;
    ring.style.cssText = `left:${left}px;top:${top}px;width:${right - left}px;height:${bottom - top}px;`;
    particles.style.cssText = ring.style.cssText;
  }

  function start({ auto = false } = {}) {
    if (auto && sessionStorage.getItem(GUIDE_AUTO_SESSION_KEY) === "true") return;
    if (active) return;
    active = true;
    index = Math.max(
      0,
      steps.findIndex((step) => step.route === routeFromHash()),
    );
    document.body.append(layer);
    resizeHandler = () => position();
    scrollHandler = () => position();
    globalThis.addEventListener("resize", resizeHandler);
    globalThis.addEventListener("scroll", scrollHandler, true);
    update();
  }

  function stop({ remember = true } = {}) {
    if (!active) return;
    active = false;
    if (remember) sessionStorage.setItem(GUIDE_AUTO_SESSION_KEY, "true");
    globalThis.removeEventListener("resize", resizeHandler);
    globalThis.removeEventListener("scroll", scrollHandler, true);
    layer.remove();
  }

  nextButton.addEventListener("click", () => {
    if (index >= steps.length - 1) {
      stop();
      return;
    }
    index += 1;
    update();
  });
  backButton.addEventListener("click", () => {
    index = Math.max(0, index - 1);
    update();
  });
  restartButton.addEventListener("click", () => {
    index = 0;
    update();
  });
  skipButton.addEventListener("click", () => stop());

  return {
    start,
    stop,
    update,
    refresh,
    scheduleAutoStart() {
      globalThis.setTimeout(() => start({ auto: true }), autoDelayMs);
    },
  };
}
