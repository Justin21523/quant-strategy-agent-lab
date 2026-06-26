import { createElement } from "../core/dom.js";

export function createMetricCard({ label, value, meta, tone = "neutral" }) {
  return createElement("article", {
    className: "metric-card",
    dataset: { tone },
    children: [
      createElement("span", { className: "metric-card__label", text: label }),
      createElement("strong", { className: "metric-card__value", text: value }),
      createElement("span", { className: "metric-card__meta", text: meta }),
    ],
  });
}
