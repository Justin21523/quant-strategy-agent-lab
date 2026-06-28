import { createElement } from "../core/dom.js";
import { activateResearchDemo } from "../core/demo-orchestrator.js";
import { demoService } from "../services/demo-service.js";
import { formatCompact, formatInteger } from "../utils/market-formatters.js";

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";
const PLAYBACK_INTERVAL_MS = 1300;

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NAMESPACE, name);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
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

function money(value) {
  return Number.isFinite(Number(value)) ? `$${formatCompact(value)}` : "-";
}

function titleize(value = "") {
  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function metricCard(label, value, meta = "", tone = "") {
  return createElement("article", {
    className: "metric-card",
    dataset: tone ? { tone } : {},
    children: [
      createElement("span", { className: "metric-card__label", text: label }),
      createElement("strong", { className: "metric-card__value", text: String(value) }),
      meta ? createElement("small", { className: "metric-card__meta", text: meta }) : null,
    ],
  });
}

function createSparkline(points = [], key = "equity", { tone = "accent", label = "chart" } = {}) {
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
  const spread = max - min || Math.max(Math.abs(max) * 0.01, 1);
  const xScale = (index) => 8 + (index / Math.max(1, valid.length - 1)) * (width - 16);
  const yScale = (value) => 8 + ((max - value) / spread) * (height - 16);
  const path = valid
    .map((point) => `${xScale(point.index).toFixed(2)},${yScale(point.value).toFixed(2)}`)
    .join(" ");
  const svg = svgElement("svg", {
    class: `demo-sparkline demo-sparkline--${tone}`,
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": label,
    preserveAspectRatio: "none",
  });
  svg.append(svgElement("polyline", { points: path, class: "demo-sparkline__line" }));
  return svg;
}

function timeline(events = [], activeStep = 0) {
  return createElement("ol", {
    className: "demo-timeline",
    attributes: { "data-testid": "demo-timeline" },
    children: events.map((event, index) =>
      createElement("li", {
        className: "demo-timeline__step",
        dataset: {
          state: index < activeStep ? "done" : index === activeStep ? "running" : "pending",
        },
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
  });
}

function loadGrid(symbols = [], activeStep = 0) {
  return createElement("div", {
    className: "demo-symbol-grid",
    attributes: { "data-testid": "demo-symbol-grid" },
    children: symbols.slice(0, 20).map((symbol, index) =>
      createElement("span", {
        className: "demo-symbol-chip",
        dataset: { state: index <= activeStep * 3 ? "synced" : "queued" },
        text: symbol,
      }),
    ),
  });
}

function qualityHeatmap(symbols = []) {
  const rows = symbols.slice(0, 20);
  return createElement("div", {
    className: "quality-heatmap",
    attributes: { "data-testid": "quality-heatmap" },
    children: rows.map((item) => {
      const warningCount = item.warnings?.length ?? 0;
      const tone =
        !item.supports_sma_200 || !item.supports_return_252d
          ? "danger"
          : warningCount || Number(item.missing_weekday_count) > 20
            ? "warning"
            : "success";
      return createElement("div", {
        className: "quality-tile",
        dataset: { tone },
        attributes: { title: `${item.symbol}: ${formatInteger(item.cached_bar_count)} bars` },
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
  const rows = results.slice(0, 10);
  const max = Math.max(...rows.map((item) => Number(item.return_60d_pct) || 0), 1);
  return createElement("div", {
    className: "scanner-ranking",
    attributes: { "data-testid": "scanner-ranking" },
    children: rows.map((item) =>
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
    attributes: { "data-testid": "portfolio-card-grid" },
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
                  createElement("span", {
                    className: "eyebrow",
                    text: item.frequency ?? "rebalance",
                  }),
                  createElement("h3", { text: titleize(item.preset) }),
                ],
              }),
              createElement("strong", { text: signedPct(item.total_return_pct) }),
            ],
          }),
          createElement("div", {
            className: "portfolio-demo-card__charts",
            children: [
              createSparkline(item.equity_curve ?? [], "equity", {
                tone: "accent",
                label: `${item.preset} equity curve`,
              }),
              createSparkline(item.drawdown_curve ?? [], "drawdown_pct", {
                tone: "danger",
                label: `${item.preset} drawdown curve`,
              }),
            ],
          }),
          createElement("div", {
            className: "portfolio-demo-card__stats",
            children: [
              createElement("span", { text: `Final ${money(item.final_equity)}` }),
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
  const rows = items.slice(0, 6);
  const max = Math.max(
    ...rows.map((item) => Math.abs(Number(item.average_total_return_pct) || 0)),
    1,
  );
  return createElement("div", {
    className: "strategy-bars",
    attributes: { "data-testid": "strategy-bars" },
    children: rows.map((item) =>
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

function finalReport(summary = {}) {
  const bestPortfolio = summary.portfolio_matrix?.[0];
  const bestStrategy = summary.strategy_comparison?.[0];
  return createElement("div", {
    className: "demo-report",
    attributes: { "data-testid": "demo-report" },
    children: [
      createElement("article", {
        children: [
          createElement("span", { className: "eyebrow", text: "Best Portfolio" }),
          createElement("strong", { text: titleize(bestPortfolio?.preset ?? "-") }),
          createElement("small", {
            text: `${signedPct(bestPortfolio?.total_return_pct)} return · ${pct(bestPortfolio?.max_drawdown_pct)} max DD`,
          }),
        ],
      }),
      createElement("article", {
        children: [
          createElement("span", { className: "eyebrow", text: "Best Strategy" }),
          createElement("strong", { text: titleize(bestStrategy?.template_id ?? "-") }),
          createElement("small", {
            text: `${signedPct(bestStrategy?.average_total_return_pct)} average return`,
          }),
        ],
      }),
      createElement("div", {
        className: "demo-report__links",
        children: [
          createElement("a", {
            className: "button button--secondary button--small",
            text: "Jobs",
            attributes: { href: "#/jobs" },
          }),
          createElement("a", {
            className: "button button--secondary button--small",
            text: "Scanner",
            attributes: { href: "#/parameter-scanner" },
          }),
          createElement("a", {
            className: "button button--secondary button--small",
            text: "Portfolio",
            attributes: { href: "#/portfolio-rebalance" },
          }),
          createElement("a", {
            className: "button button--secondary button--small",
            text: "Performance",
            attributes: { href: "#/performance-report" },
          }),
        ],
      }),
    ],
  });
}

export function createDashboardPage() {
  let destroyed = false;
  let latestSummary = null;
  let activeStep = 7;
  let playbackTimer = null;
  let isPlaying = false;

  const activity = createElement("div", {
    className: "activity-banner",
    dataset: { status: "loading" },
    attributes: { role: "status", "aria-live": "polite", "data-testid": "demo-status" },
    text: "Loading Demo Studio snapshot...",
  });
  const summaryGrid = createElement("div", { className: "metric-grid" });
  const timelinePanel = createElement("div");
  const loadPanel = createElement("div");
  const heatmapPanel = createElement("div");
  const rankingPanel = createElement("div");
  const portfolioPanel = createElement("div");
  const strategyPanel = createElement("div");
  const reportPanel = createElement("div");

  const activateButton = createElement("button", {
    className: "button button--primary",
    text: "Activate Demo",
    attributes: { type: "button", "data-testid": "activate-demo-button" },
  });
  const playButton = createElement("button", {
    className: "button button--secondary button--small",
    text: "Play",
    attributes: { type: "button", "data-testid": "demo-play-button" },
  });
  const replayButton = createElement("button", {
    className: "button button--secondary button--small",
    text: "Replay",
    attributes: { type: "button" },
  });
  const stepButton = createElement("button", {
    className: "button button--secondary button--small",
    text: "Step",
    attributes: { type: "button" },
  });

  const element = createElement("section", {
    className: "page dashboard-page demo-studio-page",
    children: [
      createElement("section", {
        className: "demo-studio-hero",
        attributes: { "data-guide": "demo-hero" },
        children: [
          createElement("div", {
            className: "demo-studio-hero__copy",
            children: [
              createElement("span", { className: "eyebrow", text: "Phase 9C · Demo Studio" }),
              createElement("h1", { text: "Demo Studio research playback" }),
              createElement("p", {
                text: "A complete quant research workflow is visible on entry: sample universe sync, quality gates, scanner ranking, portfolio rebalance matrix, strategy comparison, and final performance report.",
              }),
              createElement("div", {
                className: "hero__actions",
                children: [
                  activateButton,
                  playButton,
                  replayButton,
                  stepButton,
                  createElement("a", {
                    className: "button button--secondary",
                    text: "Open Jobs",
                    attributes: { href: "#/jobs" },
                  }),
                  createElement("a", {
                    className: "button button--secondary",
                    text: "Open Research Lab",
                    attributes: { href: "#/research-lab" },
                  }),
                ],
              }),
            ],
          }),
          createElement("div", {
            className: "demo-live-board",
            attributes: { "aria-hidden": "true" },
            children: [
              createElement("div", { className: "demo-live-board__pulse" }),
              createElement("span", { text: "LOAD" }),
              createElement("span", { text: "QUALITY" }),
              createElement("span", { text: "SCAN" }),
              createElement("span", { text: "PORTFOLIO" }),
              createElement("span", { text: "REPORT" }),
            ],
          }),
        ],
      }),
      activity,
      summaryGrid,
      createElement("section", {
        className: "demo-studio-layout",
        attributes: { "data-guide": "demo-playback" },
        children: [
          createElement("aside", {
            className: "panel demo-timeline-panel",
            children: [
              createElement("div", {
                className: "panel__header",
                children: [
                  createElement("div", {
                    children: [
                      createElement("span", { className: "eyebrow", text: "Playback" }),
                      createElement("h2", { text: "Research workflow" }),
                    ],
                  }),
                  createElement("span", { className: "phase-chip", text: "Live" }),
                ],
              }),
              timelinePanel,
            ],
          }),
          createElement("div", {
            className: "demo-stage",
            children: [
              createElement("article", {
                className: "panel demo-stage-panel demo-stage-panel--load",
                children: [
                  createElement("div", {
                    className: "panel__header",
                    children: [
                      createElement("div", {
                        children: [
                          createElement("span", { className: "eyebrow", text: "Data Load" }),
                          createElement("h2", { text: "Synthetic universe sync" }),
                        ],
                      }),
                    ],
                  }),
                  loadPanel,
                ],
              }),
              createElement("article", {
                className: "panel demo-stage-panel demo-stage-panel--quality",
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
                  heatmapPanel,
                ],
              }),
              createElement("article", {
                className: "panel demo-stage-panel demo-stage-panel--scanner",
                children: [
                  createElement("div", {
                    className: "panel__header",
                    children: [
                      createElement("div", {
                        children: [
                          createElement("span", { className: "eyebrow", text: "Scanner" }),
                          createElement("h2", { text: "Ranked technical candidates" }),
                        ],
                      }),
                    ],
                  }),
                  rankingPanel,
                ],
              }),
              createElement("article", {
                className: "panel demo-stage-panel demo-stage-panel--portfolio",
                children: [
                  createElement("div", {
                    className: "panel__header",
                    children: [
                      createElement("div", {
                        children: [
                          createElement("span", { className: "eyebrow", text: "Portfolio Matrix" }),
                          createElement("h2", { text: "Preset rebalance comparison" }),
                        ],
                      }),
                    ],
                  }),
                  portfolioPanel,
                ],
              }),
              createElement("article", {
                className: "panel demo-stage-panel demo-stage-panel--strategy",
                children: [
                  createElement("div", {
                    className: "panel__header",
                    children: [
                      createElement("div", {
                        children: [
                          createElement("span", { className: "eyebrow", text: "Strategy Matrix" }),
                          createElement("h2", { text: "Multi-strategy comparison" }),
                        ],
                      }),
                    ],
                  }),
                  strategyPanel,
                ],
              }),
              createElement("article", {
                className: "panel demo-stage-panel demo-stage-panel--report",
                children: [
                  createElement("div", {
                    className: "panel__header",
                    children: [
                      createElement("div", {
                        children: [
                          createElement("span", { className: "eyebrow", text: "Final Report" }),
                          createElement("h2", { text: "Research conclusion" }),
                        ],
                      }),
                    ],
                  }),
                  reportPanel,
                ],
              }),
            ],
          }),
        ],
      }),
      createElement("aside", {
        className: "disclaimer",
        children: [
          createElement("strong", { text: "Research boundary" }),
          createElement("p", {
            text: "The demo uses deterministic synthetic fixtures for product workflow validation. It is not investment advice.",
          }),
        ],
      }),
    ],
  });

  function render(summary) {
    latestSummary = summary;
    const events = summary.events?.length ? summary.events : [];
    const quality = summary.quality ?? {};
    const scanner = summary.scanner ?? {};
    const universe = summary.universe ?? {};
    const symbols = quality.symbols?.length
      ? quality.symbols.map((item) => item.symbol)
      : (universe.symbols ?? []);

    summaryGrid.replaceChildren(
      metricCard(
        "Universe",
        formatInteger(universe.member_count ?? 0),
        universe.universe_id ?? "",
        "accent",
      ),
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
      metricCard(
        "Ready for SMA200",
        `${formatInteger(quality.sma_200_ready_symbols ?? 0)}/${formatInteger(quality.member_count ?? 0)}`,
        "quality gate",
      ),
    );
    timelinePanel.replaceChildren(timeline(events, activeStep));
    loadPanel.replaceChildren(loadGrid(symbols, activeStep));
    heatmapPanel.replaceChildren(qualityHeatmap(quality.symbols ?? []));
    rankingPanel.replaceChildren(scannerRanking(scanner.results ?? []));
    portfolioPanel.replaceChildren(portfolioCards(summary.portfolio_matrix ?? []));
    strategyPanel.replaceChildren(strategyBars(summary.strategy_comparison ?? []));
    reportPanel.replaceChildren(finalReport(summary));

    activity.dataset.status = summary.status === "snapshot" ? "idle" : "success";
    activity.textContent =
      summary.status === "snapshot"
        ? "Showing built-in research snapshot. Activate Demo to rerun the live workflow."
        : `${summary.run_id} loaded from the latest completed research workflow.`;
  }

  function rerenderPlayback() {
    if (latestSummary && !destroyed) render(latestSummary);
  }

  function stopPlayback() {
    if (playbackTimer) globalThis.clearInterval(playbackTimer);
    playbackTimer = null;
    isPlaying = false;
    playButton.textContent = "Play";
  }

  function startPlayback() {
    if (isPlaying) {
      stopPlayback();
      return;
    }
    isPlaying = true;
    playButton.textContent = "Pause";
    playbackTimer = globalThis.setInterval(() => {
      const eventCount = latestSummary?.events?.length || 8;
      activeStep = activeStep >= eventCount - 1 ? 0 : activeStep + 1;
      rerenderPlayback();
    }, PLAYBACK_INTERVAL_MS);
  }

  async function loadLatest() {
    try {
      const response = await demoService.latest();
      activeStep = Math.max(0, (response.summary.events?.length ?? 8) - 1);
      if (!destroyed) render(response.summary);
    } catch (error) {
      activity.dataset.status = "error";
      activity.textContent = error?.message ?? "Unable to load demo summary.";
    }
  }

  activateButton.addEventListener("click", async () => {
    activateButton.disabled = true;
    activeStep = 0;
    activity.dataset.status = "loading";
    activity.textContent = "Activating research demo automation...";
    if (!isPlaying) startPlayback();
    try {
      const summary = await activateResearchDemo({
        onComplete: (nextSummary) => {
          activeStep = Math.max(0, (nextSummary.events?.length ?? 8) - 1);
          if (!destroyed) render(nextSummary);
        },
      });
      if (!destroyed && summary) {
        activeStep = Math.max(0, (summary.events?.length ?? 8) - 1);
        render(summary);
      }
    } catch (error) {
      if (!destroyed) {
        activity.dataset.status = "error";
        activity.textContent = error?.message ?? "Research demo automation failed.";
        if (latestSummary) render(latestSummary);
      }
    } finally {
      stopPlayback();
      if (!destroyed) activateButton.disabled = false;
    }
  });

  playButton.addEventListener("click", startPlayback);
  replayButton.addEventListener("click", () => {
    activeStep = 0;
    rerenderPlayback();
    if (!isPlaying) startPlayback();
  });
  stepButton.addEventListener("click", () => {
    const eventCount = latestSummary?.events?.length || 8;
    activeStep = activeStep >= eventCount - 1 ? 0 : activeStep + 1;
    rerenderPlayback();
  });

  loadLatest();
  return {
    element,
    destroy() {
      destroyed = true;
      stopPlayback();
    },
  };
}
