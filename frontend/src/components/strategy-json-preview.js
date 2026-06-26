import { createElement } from "../core/dom.js";

export function createStrategyJsonPreview() {
  const code = createElement("code", { text: "{}" });
  const element = createElement("pre", {
    className: "strategy-json-preview",
    attributes: { tabindex: "0" },
    children: [code],
  });

  return {
    element,
    update(payload) {
      code.textContent = JSON.stringify(payload ?? {}, null, 2);
    },
  };
}
