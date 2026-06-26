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

function indicatorSeries(bundle, key) {
  return bundle?.series?.find((item) => item.key === key) ?? null;
}

function valueAt(series, index, key = series?.key) {
  const value = series?.values?.[index]?.values?.[key];
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function linePoints(values, xScale, yScale) {
  const segments = [];
  let current = [];
  values.forEach((value, index) => {
    if (value === null || !Number.isFinite(value)) {
      if (current.length) segments.push(current);
      current = [];
      return;
    }
    current.push(`${xScale(index).toFixed(2)},${yScale(value).toFixed(2)}`);
  });
  if (current.length) segments.push(current);
  return segments;
}

function renderLineChart({ bars, lines, yDomain, label, guideLines = [] }) {
  const width = 840;
  const height = 230;
  const padding = { top: 26, right: 34, bottom: 34, left: 54 };
  const svg = svgElement("svg", {
    class: "indicator-chart",
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": label,
    preserveAspectRatio: "none",
  });
  const [minimum, maximum] = yDomain;
  const spread = maximum - minimum || Math.max(Math.abs(maximum) * 0.01, 1);
  const xScale = (index) =>
    padding.left + (index / Math.max(1, bars.length - 1)) * (width - padding.left - padding.right);
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
        class: "indicator-chart__grid",
      }),
    );
  }

  for (const guide of guideLines) {
    if (guide.value < minimum || guide.value > maximum) continue;
    const y = yScale(guide.value);
    const text = svgElement("text", {
      x: width - padding.right - 6,
      y: y - 6,
      "text-anchor": "end",
      class: "indicator-chart__label",
    });
    text.textContent = guide.label;
    svg.append(
      svgElement("line", {
        x1: padding.left,
        x2: width - padding.right,
        y1: y,
        y2: y,
        class: "indicator-chart__guide",
      }),
      text,
    );
  }

  for (const line of lines) {
    for (const segment of linePoints(line.values, xScale, yScale)) {
      if (segment.length < 2) continue;
      svg.append(
        svgElement("polyline", {
          points: segment.join(" "),
          class: `indicator-chart__line indicator-chart__line--${line.key}`,
        }),
      );
    }
  }

  const labels = [
    [formatPrice(maximum), padding.top + 4],
    [formatPrice(minimum), height - padding.bottom],
  ];
  for (const [text, y] of labels) {
    const labelElement = svgElement("text", {
      x: 8,
      y,
      class: "indicator-chart__label",
    });
    labelElement.textContent = text;
    svg.append(labelElement);
  }

  const firstDate = svgElement("text", {
    x: padding.left,
    y: height - 9,
    class: "indicator-chart__label",
  });
  firstDate.textContent = bars[0]?.date ?? "";
  const lastDate = svgElement("text", {
    x: width - padding.right,
    y: height - 9,
    "text-anchor": "end",
    class: "indicator-chart__label",
  });
  lastDate.textContent = bars.at(-1)?.date ?? "";
  svg.append(firstDate, lastDate);

  return svg;
}

function renderLegend(items) {
  return createElement("div", {
    className: "indicator-legend",
    children: items.map((item) =>
      createElement("span", {
        className: `indicator-legend__item indicator-legend__item--${item.key}`,
        text: item.label,
      }),
    ),
  });
}

export function createIndicatorPreviewChart() {
  const priceFrame = createElement("div", { className: "chart-frame chart-frame--compact" });
  const rsiFrame = createElement("div", { className: "chart-frame chart-frame--compact" });
  const empty = createElement("p", {
    className: "chart-empty",
    text: "Enable indicators and load a cached series to draw SMA and RSI overlays.",
  });
  const element = createElement("div", {
    className: "indicator-stack",
    children: [empty],
  });

  function update(series) {
    const bars = series?.bars ?? [];
    const indicators = series?.indicators;
    if (!bars.length || !indicators?.series?.length) {
      element.replaceChildren(empty);
      return;
    }

    const sma20 = indicatorSeries(indicators, "sma_20");
    const sma60 = indicatorSeries(indicators, "sma_60");
    const rsi14 = indicatorSeries(indicators, "rsi_14");
    const closeValues = bars.map((bar) => Number(bar.close));
    const sma20Values = bars.map((_, index) => valueAt(sma20, index));
    const sma60Values = bars.map((_, index) => valueAt(sma60, index));
    const priceValues = [...closeValues, ...sma20Values, ...sma60Values].filter(Number.isFinite);
    const priceMinimum = Math.min(...priceValues);
    const priceMaximum = Math.max(...priceValues);
    const pricePadding = Math.max((priceMaximum - priceMinimum) * 0.06, 1);
    const rsiValues = bars.map((_, index) => valueAt(rsi14, index));

    priceFrame.replaceChildren(
      renderLineChart({
        bars,
        label: "Close price with SMA overlays",
        yDomain: [priceMinimum - pricePadding, priceMaximum + pricePadding],
        lines: [
          { key: "close", label: "Close", values: closeValues },
          { key: "sma20", label: "SMA 20", values: sma20Values },
          { key: "sma60", label: "SMA 60", values: sma60Values },
        ],
      }),
      renderLegend([
        { key: "close", label: "Close" },
        { key: "sma20", label: "SMA 20" },
        { key: "sma60", label: "SMA 60" },
      ]),
    );

    rsiFrame.replaceChildren(
      renderLineChart({
        bars,
        label: "RSI oscillator",
        yDomain: [0, 100],
        guideLines: [
          { value: 70, label: "70" },
          { value: 30, label: "30" },
        ],
        lines: [{ key: "rsi", label: "RSI 14", values: rsiValues }],
      }),
      renderLegend([{ key: "rsi", label: "RSI 14" }]),
    );

    element.replaceChildren(priceFrame, rsiFrame);
  }

  return { element, update };
}
