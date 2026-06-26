import assert from "node:assert/strict";
import test from "node:test";

import { createStrategyService } from "../src/services/strategy-service.js";

test("strategy service builds template and validation API contracts", async () => {
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
  const service = createStrategyService(client);

  await service.getTemplates();
  await service.getTemplate("ma_crossover_rsi");
  await service.renderTemplate("ma_crossover_rsi", {
    symbol: "AAPL",
    parameters: { fast_window: 20, slow_window: 60 },
  });
  await service.validate({ dsl_version: "1.0" });

  assert.deepEqual(calls[0], ["GET", "/api/v1/strategies/templates"]);
  assert.deepEqual(calls[1], ["GET", "/api/v1/strategies/templates/ma_crossover_rsi"]);
  assert.deepEqual(calls[2], [
    "POST",
    "/api/v1/strategies/templates/ma_crossover_rsi/render",
    { symbol: "AAPL", parameters: { fast_window: 20, slow_window: 60 } },
  ]);
  assert.deepEqual(calls[3], [
    "POST",
    "/api/v1/strategies/validate",
    { strategy_json: { dsl_version: "1.0" } },
  ]);
});
