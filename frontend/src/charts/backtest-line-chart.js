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

export function createBacktestLineChart({
  label,
  valueKey,
  formatter = formatPrice,
  area = false,
  zeroLine = false,
}) {
  const empty = createElement("p", {
    className: "chart-empty",
    text: `Run a backtest to inspect ${label}.`,
  });
  const element = createElement("div", { className: "chart-frame", children: [empty] });

  function update(points = []) {
    const valid = points
      .map((point, index) => ({ index, date: point.date, value: Number(point[valueKey]) }))
      .filter((point) => Number.isFinite(point.value));
    if (valid.length < 2) {
      element.replaceChildren(empty);
      return;
    }

    const width = 840;
    const height = 240;
    const padding = { top: 26, right: 34, bottom: 34, left: 58 };
    const minimum = Math.min(...valid.map((point) => point.value));
    const maximum = Math.max(...valid.map((point) => point.value));
    const spread = maximum - minimum || Math.max(Math.abs(maximum) * 0.01, 1);
    const xScale = (index) =>
      padding.left +
      (index / Math.max(1, points.length - 1)) * (width - padding.left - padding.right);
    const yScale = (value) =>
      padding.top + ((maximum - value) / spread) * (height - padding.top - padding.bottom);

    const baselineY = zeroLine && minimum <= 0 && maximum >= 0 ? yScale(0) : yScale(minimum);

    const svg = svgElement("svg", {
      class: "backtest-line-chart",
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-label": label,
      preserveAspectRatio: "none",
    });

    for (let index = 0; index < 5; index += 1) {
      const y = padding.top + (index / 4) * (height - padding.top - padding.bottom);
      svg.append(
        svgElement("line", {
          x1: padding.left,
          x2: width - padding.right,
          y1: y,
          y2: y,
          class: "backtest-line-chart__grid",
        }),
      );
    }

    const linePoints = valid
      .map((point) => `${xScale(point.index).toFixed(2)},${yScale(point.value).toFixed(2)}`)
      .join(" ");
    if (area) {
      const areaPoints = `${linePoints} ${xScale(valid.at(-1).index).toFixed(2)},${baselineY.toFixed(2)} ${xScale(valid[0].index).toFixed(2)},${baselineY.toFixed(2)}`;
      svg.append(svgElement("polygon", { points: areaPoints, class: "backtest-line-chart__area" }));
    }

    if (zeroLine && minimum <= 0 && maximum >= 0) {
      svg.append(
        svgElement("line", {
          x1: padding.left,
          x2: width - padding.right,
          y1: baselineY,
          y2: baselineY,
          class: "backtest-line-chart__zero",
        }),
      );
    }

    svg.append(svgElement("polyline", { points: linePoints, class: "backtest-line-chart__line" }));

    const maxLabel = svgElement("text", { x: 8, y: padding.top + 4, class: "chart-label" });
    maxLabel.textContent = formatter(maximum);
    const minLabel = svgElement("text", {
      x: 8,
      y: height - padding.bottom,
      class: "chart-label",
    });
    minLabel.textContent = formatter(minimum);
    const firstDate = svgElement("text", {
      x: padding.left,
      y: height - 9,
      class: "chart-label",
    });
    firstDate.textContent = points[0].date;
    const lastDate = svgElement("text", {
      x: width - padding.right,
      y: height - 9,
      "text-anchor": "end",
      class: "chart-label",
    });
    lastDate.textContent = points.at(-1).date;
    svg.append(maxLabel, minLabel, firstDate, lastDate);
    element.replaceChildren(svg);
  }

  return { element, update };
}
