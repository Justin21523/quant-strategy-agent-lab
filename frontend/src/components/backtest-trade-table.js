import { createElement } from "../core/dom.js";
import { formatInteger, formatPrice } from "../utils/market-formatters.js";

function cell(text) {
  return createElement("td", { text });
}

function formatTradeId(trade) {
  if (typeof trade.trade_id === "string") return trade.trade_id;
  if (typeof trade.legacy_trade_id === "number")
    return `trade_${String(trade.legacy_trade_id).padStart(4, "0")}`;
  if (typeof trade.trade_id === "number") return `trade_${String(trade.trade_id).padStart(4, "0")}`;
  return "—";
}

function formatQuantity(trade) {
  const quantity = trade.shares ?? trade.quantity;
  if (Number.isInteger(quantity)) return formatInteger(quantity);
  return formatPrice(quantity);
}

export function createBacktestTradeTable() {
  const empty = createElement("p", {
    className: "empty-copy",
    text: "No closed trades yet. Run a strategy to populate the ledger.",
  });
  const element = createElement("div", { className: "table-scroll", children: [empty] });

  function update(trades = []) {
    if (!trades.length) {
      element.replaceChildren(empty);
      return;
    }
    const table = createElement("table", {
      className: "data-table trade-table",
      children: [
        createElement("thead", {
          children: [
            createElement("tr", {
              children: [
                "Trade",
                "Entry",
                "Exit",
                "Entry px",
                "Exit px",
                "Qty",
                "Net PnL",
                "Return %",
                "Reason",
              ].map((label) => createElement("th", { text: label })),
            }),
          ],
        }),
        createElement("tbody", {
          children: trades.map((trade) =>
            createElement("tr", {
              children: [
                cell(formatTradeId(trade)),
                cell(trade.entry_date),
                cell(trade.exit_date),
                cell(formatPrice(trade.entry_price)),
                cell(formatPrice(trade.exit_price)),
                cell(formatQuantity(trade)),
                cell(formatPrice(trade.net_pnl)),
                cell(formatPrice(trade.return_pct)),
                cell(`${trade.entry_reason ?? "entry"} → ${trade.exit_reason}`),
              ],
            }),
          ),
        }),
      ],
    });
    element.replaceChildren(table);
  }

  return { element, update };
}
