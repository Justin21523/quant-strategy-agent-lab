import assert from "node:assert/strict";
import test from "node:test";

import { createDemoService } from "../src/services/demo-service.js";

test("demo service reads latest and specific research summaries", async () => {
  const calls = [];
  const client = {
    get(path, options) {
      calls.push(["GET", path, options]);
      return Promise.resolve({});
    },
  };
  const service = createDemoService(client);

  await service.latest();
  await service.get("demo_123");

  assert.deepEqual(calls, [
    ["GET", "/api/v1/demo/research/latest", { timeoutMs: 10_000 }],
    ["GET", "/api/v1/demo/research/demo_123", { timeoutMs: 10_000 }],
  ]);
});
