import { createElement } from "../core/dom.js";

export function createNotFoundPage({ path }) {
  return createElement("section", {
    className: "page page--not-found",
    children: [
      createElement("span", { className: "eyebrow", text: "404" }),
      createElement("h1", { text: "Route not found" }),
      createElement("p", { text: `No module is registered for ${path}.` }),
      createElement("a", {
        className: "button button--primary",
        text: "Return to overview",
        attributes: { href: "#/" },
      }),
    ],
  });
}
