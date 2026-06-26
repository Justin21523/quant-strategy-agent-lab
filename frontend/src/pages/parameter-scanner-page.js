import { createComingSoonPage } from "../components/coming-soon.js";

export function createParameterScannerPage() {
  return createComingSoonPage({
    phase: 10,
    title: "Parameter Scanner",
    description: "Explore parameter sensitivity without treating the best cell as a crystal ball.",
    deliverables: [
      "Parameter-grid configuration",
      "Objective selection with guardrails",
      "Heatmap and ranked results",
      "Overfitting and sample-size warnings",
    ],
  });
}
