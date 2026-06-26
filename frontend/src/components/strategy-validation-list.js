import { createElement } from "../core/dom.js";

export function createStrategyValidationList() {
  const element = createElement("ul", { className: "strategy-validation-list" });

  function update(report) {
    const issues = report?.issues ?? [];
    if (!issues.length) {
      element.replaceChildren(
        createElement("li", {
          className: "strategy-validation-item",
          dataset: { severity: "info" },
          children: [
            createElement("strong", { text: "valid" }),
            createElement("p", {
              text: "Strategy JSON DSL passes structural validation and is ready for backtesting.",
            }),
          ],
        }),
      );
      return;
    }
    element.replaceChildren(
      ...issues.map((issue) =>
        createElement("li", {
          className: "strategy-validation-item",
          dataset: { severity: issue.severity },
          children: [
            createElement("strong", { text: issue.code }),
            createElement("p", { text: issue.message }),
            issue.path ? createElement("small", { text: issue.path }) : null,
          ],
        }),
      ),
    );
  }

  return { element, update };
}
