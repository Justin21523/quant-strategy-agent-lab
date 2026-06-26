import { createElement } from "../core/dom.js";

export function createStatusPill({ status, label }) {
  const labelElement = createElement("span", { text: label });
  const element = createElement("span", {
    className: "status-pill",
    dataset: { status },
    children: [createElement("span", { className: "status-pill__dot" }), labelElement],
  });

  return {
    element,
    update(next) {
      element.dataset.status = next.status;
      labelElement.textContent = next.label;
    },
  };
}
