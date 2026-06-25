import { createCapabilityCard } from '../components/capability-card.js';
import { createPhaseCard } from '../components/phase-card.js';
import { createApiClient } from '../core/api-client.js';
import { systemService } from '../services/system-service.js';

const phasePreview = [
  {
    number: '0',
    title: 'Foundation',
    description: 'Module boundaries, development workflow, API contracts, and runnable shells.',
    status: 'complete',
  },
  {
    number: '1',
    title: 'Market Data Layer',
    description: 'Verified OHLCV ingestion, local fallback data, caching, and provenance.',
    status: 'next',
  },
  {
    number: '2',
    title: 'Indicator Engine',
    description: 'Tested SMA, EMA, RSI, MACD, Bollinger Bands, and ATR calculations.',
    status: 'planned',
  },
];

export function createDashboardPage({ store }) {
  const element = document.createElement('section');
  element.className = 'page dashboard-page';
  element.innerHTML = `
    <div class="hero-panel">
      <div>
        <p class="eyebrow">Quant research workbench</p>
        <h1>Build the laboratory before running the experiment.</h1>
        <p class="hero-panel__copy">
          Phase 0 gives every future strategy, metric, chart, and agent step a clean place to live.
          The empty areas are intentional—not suspiciously profitable placeholders.
        </p>
        <div class="hero-panel__actions">
          <a class="button button--primary" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">Open API docs</a>
          <a class="button button--secondary" href="#/strategy-builder">Explore roadmap pages</a>
        </div>
      </div>
      <div class="system-card">
        <span class="system-card__label">Backend handshake</span>
        <strong data-system-status>Checking FastAPI…</strong>
        <p data-system-detail>The frontend is calling the versioned health endpoint.</p>
      </div>
    </div>
    <section class="content-section" aria-labelledby="capabilities-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Honest capability map</p>
          <h2 id="capabilities-title">Ready now versus planned later</h2>
        </div>
        <button class="button button--ghost" type="button" data-refresh-health>Refresh status</button>
      </div>
      <div class="capability-grid" data-capability-grid><p class="muted">Loading system metadata…</p></div>
    </section>
    <section class="content-section" aria-labelledby="roadmap-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Implementation sequence</p>
          <h2 id="roadmap-title">The next three phases</h2>
        </div>
      </div>
      <div class="phase-grid" data-phase-grid></div>
    </section>`;

  const apiClient = createApiClient();
  const statusElement = element.querySelector('[data-system-status]');
  const detailElement = element.querySelector('[data-system-detail]');
  const capabilityGrid = element.querySelector('[data-capability-grid]');
  const refreshButton = element.querySelector('[data-refresh-health]');
  const phaseGrid = element.querySelector('[data-phase-grid]');
  let isDestroyed = false;

  phasePreview.forEach((phase) => phaseGrid.append(createPhaseCard(phase)));

  async function loadSystemStatus() {
    refreshButton.disabled = true;
    statusElement.textContent = 'Checking FastAPI…';
    detailElement.textContent = 'Calling /api/v1/health and /api/v1/system/info.';
    store.setState((state) => ({
      ...state,
      backend: { status: 'checking', checkedAt: null, detail: null },
    }));

    try {
      const [health, info] = await Promise.all([
        systemService.getHealth(apiClient),
        systemService.getInfo(apiClient),
      ]);
      if (isDestroyed) return;
      statusElement.textContent = `${health.service} is online`;
      detailElement.textContent = `Version ${health.version} · ${info.phase_name} · ${health.environment}`;
      capabilityGrid.replaceChildren(
        ...info.capabilities.map((capability) => createCapabilityCard(capability)),
      );
      store.setState((state) => ({
        ...state,
        backend: { status: 'online', checkedAt: health.timestamp, detail: health },
      }));
    } catch (error) {
      if (isDestroyed) return;
      statusElement.textContent = 'FastAPI is not reachable';
      detailElement.textContent = 'Start the backend with make backend-dev or ./scripts/dev.sh.';
      const errorPanel = document.createElement('article');
      errorPanel.className = 'error-panel';
      const errorTitle = document.createElement('strong');
      errorTitle.textContent = 'Connection failed';
      const errorDetail = document.createElement('p');
      errorDetail.textContent = error.message;
      errorPanel.append(errorTitle, errorDetail);
      capabilityGrid.replaceChildren(errorPanel);
      store.setState((state) => ({
        ...state,
        backend: { status: 'offline', checkedAt: null, detail: error.message },
      }));
    } finally {
      if (!isDestroyed) refreshButton.disabled = false;
    }
  }

  refreshButton.addEventListener('click', loadSystemStatus);
  loadSystemStatus();

  return {
    element,
    destroy() {
      isDestroyed = true;
      refreshButton.removeEventListener('click', loadSystemStatus);
    },
  };
}
