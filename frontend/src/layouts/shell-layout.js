import { APP_NAME, CURRENT_PHASE } from '../core/config.js';
import { routes } from '../routes.js';

export function createShellLayout({ store }) {
  const element = document.createElement('div');
  element.className = 'app-shell';
  element.innerHTML = `
    <aside class="sidebar" aria-label="Primary navigation">
      <a class="brand" href="#/" aria-label="${APP_NAME} home">
        <span class="brand__mark" aria-hidden="true">Q</span>
        <span><strong>Quant Strategy</strong><small>Agent Lab</small></span>
      </a>
      <nav class="sidebar__nav">
        ${routes
          .map(
            (route) => `
              <a class="nav-link" data-route="${route.path}" href="#${route.path}">
                <span>${route.label}</span><small>${route.eyebrow}</small>
              </a>`,
          )
          .join('')}
      </nav>
      <div class="sidebar__disclaimer">
        <strong>Research only</strong>
        <p>Historical results do not guarantee future performance.</p>
      </div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <div>
          <p class="topbar__eyebrow">${CURRENT_PHASE}</p>
          <p class="topbar__title">Architecture before algorithms.</p>
        </div>
        <div class="topbar__status" aria-live="polite">
          <span class="status-dot" data-backend-dot></span>
          <span data-backend-label>Checking API</span>
        </div>
      </header>
      <main class="page-outlet" data-router-outlet tabindex="-1"></main>
      <footer class="statusbar">
        <span>Vanilla JavaScript · ES Modules</span>
        <span>FastAPI · OpenAPI</span>
        <span>v0.1.0</span>
      </footer>
    </div>`;

  const outlet = element.querySelector('[data-router-outlet]');
  const backendDot = element.querySelector('[data-backend-dot]');
  const backendLabel = element.querySelector('[data-backend-label]');
  let unsubscribe = null;

  function updateBackendStatus(state) {
    const { status } = state.backend;
    backendDot.dataset.status = status;
    backendLabel.textContent =
      status === 'online' ? 'API online' : status === 'offline' ? 'API offline' : 'Checking API';
  }

  function bind() {
    updateBackendStatus(store.getState());
    unsubscribe = store.subscribe(updateBackendStatus);
  }

  function setActiveRoute(path) {
    element.querySelectorAll('[data-route]').forEach((link) => {
      const isActive = link.dataset.route === path;
      link.classList.toggle('is-active', isActive);
      if (isActive) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    outlet.focus({ preventScroll: true });
  }

  function destroy() {
    unsubscribe?.();
  }

  return { element, outlet, bind, setActiveRoute, destroy };
}
