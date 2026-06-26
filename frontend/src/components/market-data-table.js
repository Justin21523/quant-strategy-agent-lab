import { createElement } from "../core/dom.js";
import { formatInteger, formatPrice } from "../utils/market-formatters.js";

const columns = [
  ["date", "Date"],
  ["open", "Open"],
  ["high", "High"],
  ["low", "Low"],
  ["close", "Close"],
  ["adjusted_close", "Adjusted close"],
  ["volume", "Volume"],
  ["provider", "Provider"],
];

function renderCell(key, value) {
  if (key === "volume") return formatInteger(value);
  if (["open", "high", "low", "close", "adjusted_close"].includes(key)) {
    return formatPrice(value);
  }
  return String(value ?? "—");
}

export function createMarketDataTable({ previewLimit = 40 } = {}) {
  const caption = createElement("p", {
    className: "table-caption",
    text: "No rows loaded.",
  });
  const table = createElement("table", {
    className: "data-table",
    children: [
      createElement("thead", {
        children: [
          createElement("tr", {
            children: columns.map(([, label]) => createElement("th", { text: label })),
          }),
        ],
      }),
      createElement("tbody"),
    ],
  });
  const body = table.querySelector("tbody");
  const element = createElement("div", {
    children: [caption, createElement("div", { className: "table-scroll", children: [table] })],
  });

  function update(bars = []) {
    const visible = bars.slice(-previewLimit).reverse();
    body.replaceChildren(
      ...visible.map((bar) =>
        createElement("tr", {
          children: columns.map(([key]) =>
            createElement("td", {
              text: renderCell(key, bar[key]),
              dataset: { column: key },
            }),
          ),
        }),
      ),
    );
    caption.textContent = bars.length
      ? `Showing newest ${visible.length} of ${bars.length} cached rows. Full rows remain in the API response.`
      : "No rows loaded.";
  }

  return { element, update };
}
