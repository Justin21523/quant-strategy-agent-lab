import { createElement } from "../core/dom.js";

export function createDataQualityList() {
  const list = createElement("ul", { className: "quality-list" });
  const element = createElement("div", {
    className: "quality-panel",
    children: [list],
  });

  function update(warnings = []) {
    if (!warnings.length) {
      list.replaceChildren(
        createElement("li", {
          className: "quality-item",
          dataset: { severity: "info" },
          children: [
            createElement("strong", { text: "No quality warnings" }),
            createElement("p", { text: "The requested cached range passed Phase 1 validation." }),
          ],
        }),
      );
      return;
    }
    list.replaceChildren(
      ...warnings.map((warning) =>
        createElement("li", {
          className: "quality-item",
          dataset: { severity: warning.severity },
          children: [
            createElement("div", {
              className: "quality-item__header",
              children: [
                createElement("strong", { text: warning.code }),
                createElement("span", { text: warning.severity }),
              ],
            }),
            createElement("p", { text: warning.message }),
          ],
        }),
      ),
    );
  }

  update([]);
  return { element, update };
}
