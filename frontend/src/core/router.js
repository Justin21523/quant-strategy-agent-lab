function normalizePath(rawPath) {
  if (!rawPath || rawPath === '#') return '/';
  const withoutHash = rawPath.startsWith('#') ? rawPath.slice(1) : rawPath;
  const withLeadingSlash = withoutHash.startsWith('/') ? withoutHash : `/${withoutHash}`;
  return withLeadingSlash.length > 1 ? withLeadingSlash.replace(/\/$/, '') : withLeadingSlash;
}

export function matchRoute(routes, rawPath) {
  const path = normalizePath(rawPath);
  return routes.find((route) => route.path === path) ?? routes[0];
}

export function createRouter({ routes, outlet, context = {}, onRouteChange = () => {} }) {
  if (!(outlet instanceof HTMLElement)) {
    throw new TypeError('Router outlet must be an HTMLElement.');
  }

  let currentCleanup = null;

  function render() {
    const route = matchRoute(routes, window.location.hash);

    if (typeof currentCleanup === 'function') {
      currentCleanup();
      currentCleanup = null;
    }

    const page = route.render({ ...context, route });
    const element = page instanceof HTMLElement ? page : page.element;

    if (!(element instanceof HTMLElement)) {
      throw new TypeError(`Route ${route.path} did not render an HTMLElement.`);
    }

    outlet.replaceChildren(element);
    currentCleanup = page.destroy ?? null;
    document.title = `${route.label} · Quant Strategy Agent Lab`;
    onRouteChange({ route });
  }

  function start() {
    window.addEventListener('hashchange', render);
    render();
  }

  function stop() {
    window.removeEventListener('hashchange', render);
    if (typeof currentCleanup === 'function') currentCleanup();
  }

  function navigate(path) {
    window.location.hash = normalizePath(path);
  }

  return { start, stop, navigate, render };
}
