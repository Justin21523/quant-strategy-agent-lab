import { createComingSoonPage } from "../components/coming-soon.js";

export function createStrategyBuilderPage() {
  return createComingSoonPage({
    phase: 3,
    title: "Strategy Builder",
    description:
      "A rule editor and JSON preview for deterministic, validated strategy definitions.",
    deliverables: [
      "Template selector and editable parameters",
      "Entry and exit condition groups",
      "Live Strategy JSON DSL preview",
      "Authoritative backend validation",
    ],
  });
}
