function routeFromHash() {
  const rawHash = window.location.hash.replace(/^#/, "");
  const path = rawHash.split("?")[0] || "/";
  return path.startsWith("/") ? path : `/${path}`;
}

function resolvePage(page) {
  if (page instanceof HTMLElement) {
    return { element: page, destroy: () => {} };
  }
  if (page?.element instanceof HTMLElement) {
    return {
      element: page.element,
      destroy: typeof page.destroy === "function" ? page.destroy : () => {},
    };
  }
  throw new Error("A route must return an HTMLElement or { element, destroy } page object.");
}

export function createRouter({ outlet, routes, notFound, onRouteChange = () => {} }) {
  if (!outlet) throw new Error("Router outlet is required.");
  let activePage = null;

  function render() {
    const path = routeFromHash();
    const pageFactory = routes[path] ?? notFound;
    const nextPage = resolvePage(pageFactory({ path }));
    activePage?.destroy();
    activePage = nextPage;
    outlet.replaceChildren(nextPage.element);
    onRouteChange(path);
    outlet.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "instant" });
  }

  return {
    start() {
      window.addEventListener("hashchange", render);
      render();
    },
    stop() {
      window.removeEventListener("hashchange", render);
      activePage?.destroy();
      activePage = null;
    },
    navigate(path) {
      window.location.hash = path;
    },
  };
}
