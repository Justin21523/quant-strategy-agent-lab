import { createComingSoonPage } from "../components/coming-soon.js";

export function createReportCenterPage() {
  return createComingSoonPage({
    phase: 12,
    title: "Report Center",
    description: "Turn reproducible runs into reviewable research artifacts.",
    deliverables: [
      "Markdown strategy report",
      "Strategy and result JSON export",
      "Trade CSV export",
      "Assumptions and disclaimer section",
    ],
  });
}
