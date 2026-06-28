import { createElement } from "../core/dom.js";
import { createSiteGuide } from "../core/site-guide.js";
import { createSidebar } from "./sidebar.js";
import { createStatusBar } from "./status-bar.js";
import { createTopbar } from "./topbar.js";

export function createShellLayout({ apiDocsUrl }) {
  const siteGuide = createSiteGuide();
  const sidebar = createSidebar();
  const topbar = createTopbar({ apiDocsUrl, onGuideClick: () => siteGuide.start() });
  const statusBar = createStatusBar();
  const outlet = createElement("main", {
    className: "page-outlet",
    attributes: { tabindex: "-1", "data-router-outlet": "" },
  });
  const element = createElement("div", {
    className: "app-shell",
    children: [
      sidebar.element,
      createElement("section", {
        className: "workspace",
        children: [topbar.element, outlet, statusBar.element],
      }),
    ],
  });

  return {
    element,
    outlet,
    siteGuide,
    update(state) {
      sidebar.update(state.route);
      topbar.update(state);
      statusBar.update(state);
      siteGuide.refresh();
    },
  };
}
