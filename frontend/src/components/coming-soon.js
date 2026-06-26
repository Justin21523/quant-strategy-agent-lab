import { createElement } from "../core/dom.js";

export function createComingSoonPage({ phase, title, description, deliverables }) {
  return createElement("section", {
    className: "page page--coming-soon",
    children: [
      createElement("header", {
        className: "page-header",
        children: [
          createElement("span", { className: "eyebrow", text: `Planned Phase ${phase}` }),
          createElement("h1", { text: title }),
          createElement("p", { text: description }),
        ],
      }),
      createElement("article", {
        className: "panel locked-panel",
        children: [
          createElement("span", { className: "locked-panel__icon", text: "◇" }),
          createElement("h2", { text: "Module boundary reserved" }),
          createElement("p", {
            text: "The route already exists. Business behavior will be added only in its planned phase so the codebase stays teachable and reviewable.",
          }),
          createElement("ul", {
            className: "check-list",
            children: deliverables.map((item) => createElement("li", { text: item })),
          }),
        ],
      }),
    ],
  });
}
