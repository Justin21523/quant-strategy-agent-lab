import { createElement } from "../core/dom.js";

const navigation = [
  ["/", "Demo", "9C"],
  ["/research-lab", "Research Lab", "9E"],
  ["/market-data", "Market + Indicators", "02"],
  ["/strategy-builder", "Strategy Builder", "03"],
  ["/backtest-lab", "Backtest Lab", "05"],
  ["/agent-workflow", "Agent Workflow", "06"],
  ["/performance-report", "Performance", "07"],
  ["/parameter-scanner", "Scanner", "7A"],
  ["/data-quality", "Data Quality", "8A"],
  ["/portfolio-rebalance", "Portfolio", "9A"],
  ["/jobs", "Jobs", "9A"],
  ["/comparison", "Comparison", "8A"],
  ["/report-center", "Report Center", "9E"],
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
    attributes: { "data-guide": "shell-sidebar" },
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
