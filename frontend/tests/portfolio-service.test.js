import assert from "node:assert/strict";
import test from "node:test";

import { createPortfolioService } from "../src/services/portfolio-service.js";

test("portfolio service builds run and preset contracts", async () => {
  const calls = [];
  const client = {
    get(path) {
      calls.push(["GET", path]);
      return Promise.resolve({});
    },
    post(path, body) {
      calls.push(["POST", path, body]);
      return Promise.resolve({});
    },
  };
  const service = createPortfolioService(client);
  const preset = {
    preset_id: "custom",
    name: "Custom",
    description: "Custom preset",
    config: { top_n: 10 },
  };

  await service.listRuns({ limit: 5 });
  await service.getRun("pf_123");
  await service.listPresets();
  await service.getPreset("trend_momentum_monthly_top20");
  await service.savePreset(preset);

  assert.deepEqual(calls, [
    ["GET", "/api/v1/portfolios/rebalance?limit=5"],
    ["GET", "/api/v1/portfolios/rebalance/pf_123"],
    ["GET", "/api/v1/portfolios/presets"],
    ["GET", "/api/v1/portfolios/presets/trend_momentum_monthly_top20"],
    ["POST", "/api/v1/portfolios/presets", preset],
  ]);
});
