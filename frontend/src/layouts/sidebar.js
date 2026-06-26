import { createElement } from "../core/dom.js";

const navigation = [
  ["/", "Overview", "00"],
  ["/market-data", "Market Data", "01"],
  ["/strategy-builder", "Strategy Builder", "03"],
  ["/backtest-lab", "Backtest Lab", "04"],
  ["/performance-report", "Performance", "07"],
  ["/parameter-scanner", "Parameter Scan", "10"],
  ["/comparison", "Comparison", "11"],
  ["/report-center", "Report Center", "12"],
];

export function createSidebar() {
  const links = navigation.map(([path, label, phase]) =>
    createElement("a", {
      className: "nav-link",
      attributes: { href: `#${path}` },
      dataset: { route: path },
      children: [
        createElement("span", { className: "nav-link__phase", text: phase }),
        createElement("span", { text: label }),
      ],
    }),
  );

  const element = createElement("aside", {
    className: "sidebar",
    children: [
      createElement("a", {
        className: "brand",
        attributes: { href: "#/", "aria-label": "Quant Strategy Agent Lab home" },
        children: [
          createElement("span", { className: "brand__mark", text: "Q" }),
          createElement("span", {
            className: "brand__copy",
            children: [
              createElement("strong", { text: "Quant Lab" }),
              createElement("small", { text: "Agent Research OS" }),
            ],
          }),
        ],
      }),
      createElement("nav", {
        className: "sidebar__nav",
        attributes: { "aria-label": "Primary navigation" },
        children: links,
      }),
      createElement("div", {
        className: "sidebar__footer",
        children: [
          createElement("span", { className: "eyebrow", text: "Research mode" }),
          createElement("p", { text: "Educational use only. Not investment advice." }),
        ],
      }),
    ],
  });

  return {
    element,
    update(route) {
      for (const link of links) {
        const active = link.dataset.route === route;
        link.classList.toggle("is-active", active);
        if (active) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
      }
    },
  };
}
