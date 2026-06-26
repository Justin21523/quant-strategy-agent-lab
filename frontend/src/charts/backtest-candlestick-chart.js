import { createElement } from "../core/dom.js";
import { formatInteger, formatPrice } from "../utils/market-formatters.js";

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NAMESPACE, name);
  for (const [key, value] of Object.entries(attributes)) {
    if (value !== undefined && value !== null) element.setAttribute(key, String(value));
  }
  return element;
}

function addTitle(element, text) {
  const title = svgElement("title");
  title.textContent = text;
  element.append(title);
  return element;
}

function finiteNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function normalizeBacktestBars(bars = []) {
  return bars
    .map((bar) => ({
      date: bar.date,
      open: finiteNumber(bar.open),
      high: finiteNumber(bar.high),
      low: finiteNumber(bar.low),
      close: finiteNumber(bar.close),
      volume: finiteNumber(bar.volume) ?? 0,
      indicators: bar.indicators ?? {},
    }))
    .filter((bar) => [bar.open, bar.high, bar.low, bar.close].every(Number.isFinite));
}

export function buildTradeMarkers(trades = []) {
  return trades.flatMap((trade) => [
    {
      date: trade.entry_date,
      price: finiteNumber(trade.entry_price),
      side: "buy",
      label: `${trade.trade_id ?? "trade"} entry ${formatPrice(trade.entry_price)}`,
    },
    {
      date: trade.exit_date,
      price: finiteNumber(trade.exit_price),
      side: "sell",
      label: `${trade.trade_id ?? "trade"} exit ${formatPrice(trade.exit_price)}`,
    },
  ]);
}

function indicatorPolyline(bars, key, xScale, yScale) {
  return bars
    .map((bar, index) => {
      const value = finiteNumber(bar.indicators?.[key]);
      return value === null ? null : `${xScale(index).toFixed(2)},${yScale(value).toFixed(2)}`;
    })
    .filter(Boolean)
    .join(" ");
}

function markerPath(x, y, side) {
  if (side === "buy") {
    return `M ${x.toFixed(2)} ${(y + 8).toFixed(2)} L ${(x - 7).toFixed(2)} ${(y + 19).toFixed(2)} L ${(x + 7).toFixed(2)} ${(y + 19).toFixed(2)} Z`;
  }

  return `M ${x.toFixed(2)} ${(y - 8).toFixed(2)} L ${(x - 7).toFixed(2)} ${(y - 19).toFixed(2)} L ${(x + 7).toFixed(2)} ${(y - 19).toFixed(2)} Z`;
}

export function createBacktestCandlestickChart() {
  const empty = createElement("p", {
    className: "chart-empty",
    text: "Run a backtest to inspect OHLC candles and buy/sell markers.",
  });

  const element = createElement("div", {
    className: "chart-frame",
    children: [empty],
  });

  function update({ bars = [], trades = [] } = {}) {
    const normalized = normalizeBacktestBars(bars);

    if (normalized.length < 2) {
      element.replaceChildren(empty);
      return;
    }

    const width = 1040;
    const height = 420;
    const padding = { top: 30, right: 42, bottom: 44, left: 62 };
    const volumeHeight = 62;
    const priceBottom = height - padding.bottom - volumeHeight - 16;
    const priceHeight = priceBottom - padding.top;
    const plotWidth = width - padding.left - padding.right;
    const slot = plotWidth / normalized.length;
    const candleWidth = Math.max(2, Math.min(10, slot * 0.58));

    const markers = buildTradeMarkers(trades);
    const markerPrices = markers.map((marker) => marker.price).filter(Number.isFinite);
    const indicatorPrices = normalized.flatMap((bar) =>
      [bar.indicators.sma_20, bar.indicators.sma_60].map(finiteNumber).filter(Number.isFinite),
    );

    const prices = normalized
      .flatMap((bar) => [bar.low, bar.high])
      .concat(markerPrices, indicatorPrices);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const spread = max - min || Math.max(Math.abs(max) * 0.01, 1);
    const minPrice = min - spread * 0.06;
    const maxPrice = max + spread * 0.06;
    const maxVolume = Math.max(...normalized.map((bar) => bar.volume), 1);

    const xScale = (index) => padding.left + slot * index + slot / 2;
    const yScale = (value) =>
      padding.top + ((maxPrice - value) / (maxPrice - minPrice || 1)) * priceHeight;
    const volumeScale = (value) =>
      height - padding.bottom - (Math.max(0, value) / maxVolume) * volumeHeight;
    const byDate = new Map(normalized.map((bar, index) => [bar.date, index]));

    const svg = svgElement("svg", {
      class: "backtest-candlestick-chart",
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-label": "Backtest candlestick chart with trade markers",
      preserveAspectRatio: "none",
    });

    addTitle(svg, "Backtest candles with SMA overlays and executed trade markers.");

    for (let index = 0; index < 5; index += 1) {
      const y = padding.top + (index / 4) * priceHeight;
      svg.append(
        svgElement("line", {
          x1: padding.left,
          x2: width - padding.right,
          y1: y,
          y2: y,
          class: "backtest-candlestick-chart__grid",
        }),
      );
    }

    normalized.forEach((bar, index) => {
      const x = xScale(index);
      const tone = bar.close >= bar.open ? "up" : "down";
      const bodyTop = Math.min(yScale(bar.open), yScale(bar.close));
      const bodyBottom = Math.max(yScale(bar.open), yScale(bar.close));

      const volume = svgElement("rect", {
        x: x - candleWidth / 2,
        y: volumeScale(bar.volume),
        width: candleWidth,
        height: Math.max(1, height - padding.bottom - volumeScale(bar.volume)),
        class: "backtest-volume-bar",
        "data-tone": tone,
      });

      const wick = svgElement("line", {
        x1: x,
        x2: x,
        y1: yScale(bar.high),
        y2: yScale(bar.low),
        class: "backtest-candle__wick",
        "data-tone": tone,
      });

      const body = svgElement("rect", {
        x: x - candleWidth / 2,
        y: bodyTop,
        width: candleWidth,
        height: Math.max(1.4, bodyBottom - bodyTop),
        rx: 0.8,
        class: "backtest-candle__body",
        "data-tone": tone,
      });

      addTitle(
        body,
        `${bar.date} O ${formatPrice(bar.open)} H ${formatPrice(bar.high)} L ${formatPrice(bar.low)} C ${formatPrice(bar.close)} Vol ${formatInteger(bar.volume)}`,
      );

      svg.append(volume, wick, body);
    });

    const sma20 = indicatorPolyline(normalized, "sma_20", xScale, yScale);
    const sma60 = indicatorPolyline(normalized, "sma_60", xScale, yScale);

    if (sma20) {
      svg.append(
        svgElement("polyline", {
          points: sma20,
          class: "backtest-overlay-line backtest-overlay-line--fast",
        }),
      );
    }

    if (sma60) {
      svg.append(
        svgElement("polyline", {
          points: sma60,
          class: "backtest-overlay-line backtest-overlay-line--slow",
        }),
      );
    }

    for (const marker of markers) {
      if (!Number.isFinite(marker.price) || !byDate.has(marker.date)) continue;

      const shape = svgElement("path", {
        d: markerPath(xScale(byDate.get(marker.date)), yScale(marker.price), marker.side),
        class: "backtest-trade-marker",
        "data-side": marker.side,
      });

      addTitle(shape, `${marker.date} ${marker.label}`);
      svg.append(shape);
    }

    const maxLabel = svgElement("text", {
      x: 8,
      y: padding.top + 4,
      class: "chart-label",
    });
    maxLabel.textContent = formatPrice(maxPrice);

    const minLabel = svgElement("text", {
      x: 8,
      y: priceBottom,
      class: "chart-label",
    });
    minLabel.textContent = formatPrice(minPrice);

    const firstDate = svgElement("text", {
      x: padding.left,
      y: height - 12,
      class: "chart-label",
    });
    firstDate.textContent = normalized[0].date;

    const lastDate = svgElement("text", {
      x: width - padding.right,
      y: height - 12,
      "text-anchor": "end",
      class: "chart-label",
    });
    lastDate.textContent = normalized.at(-1).date;

    svg.append(maxLabel, minLabel, firstDate, lastDate);
    element.replaceChildren(svg);
  }

  return { element, update };
}
