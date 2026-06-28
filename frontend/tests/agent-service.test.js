import assert from "node:assert/strict";
import test from "node:test";

import { createAgentService } from "../src/services/agent-service.js";

test("agent service reads canonical backtest workflow metadata", async () => {
  const calls = [];
  const client = {
    get(path) {
      calls.push(path);
      return Promise.resolve({});
    },
  };
  const service = createAgentService(client);

  await service.getBacktestWorkflow();

  assert.deepEqual(calls, ["/api/v1/agent/backtest-workflow"]);
});
