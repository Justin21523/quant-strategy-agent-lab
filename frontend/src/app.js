import { apiDocsUrl } from "./core/config.js";
import { eventBus, EVENTS } from "./core/event-bus.js";
import { createRouter } from "./core/router.js";
import { store } from "./core/store.js";
import { createShellLayout } from "./layouts/shell-layout.js";
import { createAgentWorkflowPage } from "./pages/agent-workflow-page.js";
import { createBacktestLabPage } from "./pages/backtest-lab-page.js";
import { createComparisonPage } from "./pages/comparison-page.js";
import { createDataQualityPage } from "./pages/data-quality-page.js";
import { createDashboardPage } from "./pages/dashboard-page.js";
import { createJobsPage } from "./pages/jobs-page.js";
import { createMarketDataPage } from "./pages/market-data-page.js";
import { createNotFoundPage } from "./pages/not-found-page.js";
import { createParameterScannerPage } from "./pages/parameter-scanner-page.js";
import { createPerformanceReportPage } from "./pages/performance-report-page.js";
import { createPortfolioRebalancePage } from "./pages/portfolio-rebalance-page.js";
import { createReportCenterPage } from "./pages/report-center-page.js";
import { createResearchLabPage } from "./pages/research-lab-page.js";
import { createStrategyBuilderPage } from "./pages/strategy-builder-page.js";
import { healthService } from "./services/health-service.js";

const routes = {
  "/": createDashboardPage,
  "/research-lab": createResearchLabPage,
  "/market-data": createMarketDataPage,
  "/strategy-builder": createStrategyBuilderPage,
  "/backtest-lab": createBacktestLabPage,
  "/agent-workflow": createAgentWorkflowPage,
  "/performance-report": createPerformanceReportPage,
  "/parameter-scanner": createParameterScannerPage,
  "/data-quality": createDataQualityPage,
  "/portfolio-rebalance": createPortfolioRebalancePage,
  "/jobs": createJobsPage,
  "/comparison": createComparisonPage,
  "/report-center": createReportCenterPage,
};

export function createApp(root) {
  const shell = createShellLayout({ apiDocsUrl });
  root.replaceChildren(shell.element);

  const router = createRouter({
    outlet: shell.outlet,
    routes,
    notFound: createNotFoundPage,
    onRouteChange(path) {
      store.setState({ route: path });
      eventBus.emit(EVENTS.ROUTE_CHANGED, { path });
    },
  });

  const unsubscribe = store.subscribe((state) => shell.update(state));
  window.addEventListener(
    "beforeunload",
    () => {
      unsubscribe();
      router.stop();
    },
    { once: true },
  );

  router.start();
  shell.siteGuide.scheduleAutoStart();
  refreshApiHealth();
}

async function refreshApiHealth() {
  const startedAt = performance.now();
  store.setState({
    api: { status: "checking", message: "Checking FastAPI…", latencyMs: null },
  });

  try {
    const health = await healthService.getHealth();
    store.setState({
      api: {
        status: "online",
        message: `${health.service} ${health.version}`,
        latencyMs: Math.round(performance.now() - startedAt),
      },
    });
  } catch (error) {
    console.warn("Backend health check failed", error);
    store.setState({
      api: {
        status: "offline",
        message: "FastAPI offline — run make dev",
        latencyMs: null,
      },
    });
  }
}
