import { createElement } from "../core/dom.js";

const defaultSteps = [
  ["Strategy received", "Natural language or template input"],
  ["Strategy parsed", "Validated Strategy JSON DSL"],
  ["Indicators built", "SMA, RSI, MACD, and more"],
  ["Backtest executed", "Fees, slippage, and positions"],
  ["Risk explained", "Metrics and failure-mode narrative"],
];

export function createAgentTimeline(steps = defaultSteps) {
  return createElement("ol", {
    className: "agent-timeline",
    children: steps.map(([title, description], index) =>
      createElement("li", {
        className: "agent-step",
        children: [
          createElement("span", { className: "agent-step__index", text: String(index + 1) }),
          createElement("div", {
            children: [
              createElement("strong", { text: title }),
              createElement("p", { text: description }),
            ],
          }),
        ],
      }),
    ),
  });
}
