import assert from "node:assert/strict";
import test from "node:test";

import { createMultiBacktestService } from "../src/services/multi-backtest-service.js";

test("multi-backtest service builds list, run, and read contracts", async () => {
  const calls = [];
  const client = {
    get(path) {
      calls.push(["GET", path]);
      return Promise.resolve({});
    },
    post(path, body, options) {
      calls.push(["POST", path, body, options]);
      return Promise.resolve({});
    },
  };
  const service = createMultiBacktestService(client);
  const payload = {
    scan_run_id: "scan_123",
    template_id: "buy_and_hold",
    top_n: 10,
    start: "2025-01-01",
    end: "2025-12-31",
  };

  await service.list({ limit: 3 });
  await service.run(payload);
  await service.get("mbt_123");

  assert.deepEqual(calls, [
    ["GET", "/api/v1/multi-backtests?limit=3"],
    ["POST", "/api/v1/multi-backtests/run", payload, { timeoutMs: 120_000 }],
    ["GET", "/api/v1/multi-backtests/mbt_123"],
  ]);
});
