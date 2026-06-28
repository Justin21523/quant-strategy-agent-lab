import assert from "node:assert/strict";
import test from "node:test";

import {
  BACKTEST_WORKFLOW_STEPS,
  mergeAgentSteps,
  normalizeAgentStep,
  summarizeAgentProgress,
} from "../src/components/agent-timeline.js";

test("normalizeAgentStep supports legacy tuple steps", () => {
  assert.deepEqual(normalizeAgentStep(["Load data", "Fetch cached bars"], 2), {
    sequence: 3,
    key: "step_3",
    label: "Load data",
    description: "Fetch cached bars",
    status: "pending",
    message: "Fetch cached bars",
    detail: {},
  });
});

test("mergeAgentSteps overlays runtime steps onto canonical workflow", () => {
  const merged = mergeAgentSteps(BACKTEST_WORKFLOW_STEPS, [
    { key: "validate_strategy", status: "success", message: "valid" },
    { key: "risk_review", status: "warning", message: "fixture data" },
  ]);

  assert.equal(merged.length, BACKTEST_WORKFLOW_STEPS.length);
  assert.equal(merged[1].status, "success");
  assert.equal(merged.at(-1).status, "warning");
});

test("summarizeAgentProgress reports warning and completed counts", () => {
  const summary = summarizeAgentProgress([
    { key: "a", status: "success" },
    { key: "b", status: "warning" },
    { key: "c", status: "pending" },
  ]);

  assert.equal(summary.completed, 2);
  assert.equal(summary.total, 3);
  assert.equal(summary.warning, 1);
  assert.equal(summary.dominantStatus, "warning");
});
