import { createComingSoonPage } from "../components/coming-soon.js";

export function createComparisonPage() {
  return createComingSoonPage({
    phase: 11,
    title: "Multi-Asset Comparison",
    description: "Run one strategy across several assets and compare risk, return, and stability.",
    deliverables: [
      "Batch symbol selection",
      "Risk/return scatter plot",
      "Cross-asset ranking",
      "Failed-run isolation",
    ],
  });
}
