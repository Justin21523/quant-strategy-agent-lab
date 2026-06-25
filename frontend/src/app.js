import { createRouter } from './core/router.js';
import { createStore } from './core/store.js';
import { createShellLayout } from './layouts/shell-layout.js';
import { routes } from './routes.js';

export function createApp({ root }) {
  const store = createStore({
    backend: {
      status: 'checking',
      checkedAt: null,
      detail: null,
    },
  });

  const shell = createShellLayout({ store });
  const router = createRouter({
    routes,
    outlet: shell.outlet,
    onRouteChange: ({ route }) => shell.setActiveRoute(route.path),
    context: { store },
  });

  function start() {
    root.replaceChildren(shell.element);
    shell.bind();
    router.start();
  }

  function stop() {
    router.stop();
    shell.destroy();
    root.replaceChildren();
  }

  return { start, stop, store, router };
}
