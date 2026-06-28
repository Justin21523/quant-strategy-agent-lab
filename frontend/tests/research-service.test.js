import assert from "node:assert/strict";
import test from "node:test";

import { createResearchService } from "../src/services/research-service.js";

test("research service reads latest, list, and specific pipeline summaries", async () => {
  const calls = [];
  const client = {
    get(path, options) {
      calls.push(["GET", path, options]);
      return Promise.resolve({});
    },
    post(path, body, options) {
      calls.push(["POST", path, body, options]);
      return Promise.resolve({});
    },
  };
  const service = createResearchService(client);

  await service.latest();
  await service.list({ limit: 5 });
  await service.get("rp_123");
  await service.listPresets();
  await service.getPreset("demo_quick_research");
  await service.savePreset({ preset_id: "x", name: "X", description: "", config: {} });
  await service.report("rp_123");
  await service.export("rp_123", { artifact: "scanner", format: "csv" });

  assert.deepEqual(calls, [
    ["GET", "/api/v1/research/runs/latest", { timeoutMs: 10_000 }],
    ["GET", "/api/v1/research/runs?limit=5", { timeoutMs: 10_000 }],
    ["GET", "/api/v1/research/runs/rp_123", { timeoutMs: 10_000 }],
    ["GET", "/api/v1/research/presets", { timeoutMs: 10_000 }],
    ["GET", "/api/v1/research/presets/demo_quick_research", { timeoutMs: 10_000 }],
    [
      "POST",
      "/api/v1/research/presets",
      { preset_id: "x", name: "X", description: "", config: {} },
      { timeoutMs: 10_000 },
    ],
    ["GET", "/api/v1/research/runs/rp_123/report?format=markdown", { timeoutMs: 10_000 }],
    [
      "GET",
      "/api/v1/research/runs/rp_123/export?artifact=scanner&format=csv",
      { timeoutMs: 10_000 },
    ],
  ]);
});
