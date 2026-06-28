import assert from "node:assert/strict";
import test from "node:test";

import { GUIDE_STEPS, resolveGuideTarget } from "../src/core/site-guide.js";

const ROUTES = new Set([
  "/",
  "/research-lab",
  "/market-data",
  "/strategy-builder",
  "/backtest-lab",
  "/agent-workflow",
  "/performance-report",
  "/parameter-scanner",
  "/data-quality",
  "/portfolio-rebalance",
  "/jobs",
  "/comparison",
  "/report-center",
]);

test("site guide defines a complete whole-site tour", () => {
  assert.equal(GUIDE_STEPS.length, 15);
  for (const step of GUIDE_STEPS) {
    assert.ok(ROUTES.has(step.route), `${step.route} should be an app route`);
    assert.ok(step.target.length > 0);
    assert.ok(step.title.length > 0);
    assert.ok(step.description.length > 0);
  }
});

test("site guide target resolver falls back to page header", () => {
  const header = { id: "fallback-header" };
  const root = {
    querySelector(selector) {
      if (selector === ".page-header") return header;
      return null;
    },
  };

  assert.equal(resolveGuideTarget("missing-target", root), header);
});
