import { createElement } from "../core/dom.js";
import { formatPrice } from "../utils/market-formatters.js";

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NAMESPACE, name);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
  return element;
}

export function createPricePreviewChart() {
  const empty = createElement("p", {
    className: "chart-empty",
    text: "Load a cached series to inspect its close-price shape.",
  });
  const svg = svgElement("svg", {
    class: "price-preview-chart",
    viewBox: "0 0 840 260",
    role: "img",
    "aria-label": "Close price preview",
    preserveAspectRatio: "none",
  });
  const element = createElement("div", {
    className: "chart-frame",
    children: [empty],
  });

  function update(bars = []) {
    svg.replaceChildren();
    if (!bars.length) {
      element.replaceChildren(empty);
      return;
    }

    const width = 840;
    const height = 260;
    const padding = { top: 26, right: 34, bottom: 34, left: 54 };
    const prices = bars.map((bar) => Number(bar.close)).filter(Number.isFinite);
    const minimum = Math.min(...prices);
    const maximum = Math.max(...prices);
    const spread = maximum - minimum || Math.max(maximum * 0.01, 1);
    const xScale = (index) =>
      padding.left +
      (index / Math.max(1, bars.length - 1)) * (width - padding.left - padding.right);
    const yScale = (value) =>
      padding.top + ((maximum - value) / spread) * (height - padding.top - padding.bottom);

    for (let index = 0; index < 5; index += 1) {
      const y = padding.top + (index / 4) * (height - padding.top - padding.bottom);
      svg.append(
        svgElement("line", {
          x1: padding.left,
          x2: width - padding.right,
          y1: y,
          y2: y,
          class: "price-preview-chart__grid",
        }),
      );
    }

    const points = bars
      .map((bar, index) => `${xScale(index).toFixed(2)},${yScale(Number(bar.close)).toFixed(2)}`)
      .join(" ");
    const polygonPoints = [
      `${padding.left},${height - padding.bottom}`,
      points,
      `${width - padding.right},${height - padding.bottom}`,
    ].join(" ");
    svg.append(
      svgElement("polygon", { points: polygonPoints, class: "price-preview-chart__area" }),
      svgElement("polyline", { points, class: "price-preview-chart__line" }),
    );

    const labels = [
      [formatPrice(maximum), padding.top + 4],
      [formatPrice(minimum), height - padding.bottom],
    ];
    for (const [text, y] of labels) {
      const label = svgElement("text", {
        x: 8,
        y,
        class: "price-preview-chart__label",
      });
      label.textContent = text;
      svg.append(label);
    }

    const firstDate = svgElement("text", {
      x: padding.left,
      y: height - 9,
      class: "price-preview-chart__label",
    });
    firstDate.textContent = bars[0].date;
    const lastDate = svgElement("text", {
      x: width - padding.right,
      y: height - 9,
      "text-anchor": "end",
      class: "price-preview-chart__label",
    });
    lastDate.textContent = bars.at(-1).date;
    svg.append(firstDate, lastDate);
    element.replaceChildren(svg);
  }

  return { element, update };
}
