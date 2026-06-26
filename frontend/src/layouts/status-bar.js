import { createElement } from "../core/dom.js";

export function createStatusBar() {
  const apiMessage = createElement("span", { text: "Checking FastAPI…" });
  const routeMessage = createElement("code", { text: "#/" });
  const element = createElement("footer", {
    className: "status-bar",
    children: [
      createElement("div", {
        className: "status-bar__item",
        children: [createElement("span", { className: "status-dot" }), apiMessage],
      }),
      createElement("div", {
        className: "status-bar__item status-bar__item--right",
        children: [
          createElement("span", { text: "Route" }),
          routeMessage,
          createElement("span", { text: "v0.6.0 · Phase 5" }),
        ],
      }),
    ],
  });

  return {
    element,
    update(state) {
      apiMessage.textContent = state.api.message;
      routeMessage.textContent = `#${state.route}`;
      element.dataset.apiStatus = state.api.status;
    },
  };
}
