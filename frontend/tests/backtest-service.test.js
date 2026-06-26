import assert from "node:assert/strict";
import test from "node:test";

import { createBacktestService } from "../src/services/backtest-service.js";

test("backtest service posts Strategy JSON DSL to run endpoint", async () => {
  const calls = [];
  const client = {
    post(path, body, options) {
      calls.push([path, body, options]);
      return Promise.resolve({});
    },
  };
  const service = createBacktestService(client);

  await service.run({ dsl_version: "1.0", strategy_id: "buy_and_hold" });

  assert.deepEqual(calls[0], [
    "/api/v1/backtests/run",
    { strategy_json: { dsl_version: "1.0", strategy_id: "buy_and_hold" } },
    { timeoutMs: 30_000 },
  ]);
});
