import assert from "node:assert/strict";
import test from "node:test";

import { createJobService } from "../src/services/job-service.js";

test("job service builds queue and polling contracts", async () => {
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
  const service = createJobService(client);
  const payload = { universe_id: "us_common_stocks", start: "2025-01-01", end: "2025-12-31" };

  await service.list({ limit: 10 });
  await service.get("job_123");
  await service.events("job_123");
  await service.cancel("job_123");
  await service.queueBatchSync(payload);
  await service.queueScan(payload);
  await service.queuePortfolio(payload);
  await service.queueResearchDemo();
  await service.queueResearchPipeline(payload);

  assert.deepEqual(calls[0], ["GET", "/api/v1/jobs?limit=10"]);
  assert.deepEqual(calls[1], ["GET", "/api/v1/jobs/job_123"]);
  assert.deepEqual(calls[2], ["GET", "/api/v1/jobs/job_123/events"]);
  assert.deepEqual(calls[3], ["POST", "/api/v1/jobs/job_123/cancel", {}, undefined]);
  assert.deepEqual(calls[4], [
    "POST",
    "/api/v1/jobs/market/batch-sync",
    payload,
    { timeoutMs: 10_000 },
  ]);
  assert.deepEqual(calls[5], ["POST", "/api/v1/jobs/scans/run", payload, { timeoutMs: 10_000 }]);
  assert.deepEqual(calls[6], [
    "POST",
    "/api/v1/jobs/portfolios/rebalance/run",
    payload,
    { timeoutMs: 10_000 },
  ]);
  assert.deepEqual(calls[7], ["POST", "/api/v1/jobs/demo/research/run", {}, { timeoutMs: 10_000 }]);
  assert.deepEqual(calls[8], [
    "POST",
    "/api/v1/jobs/research/pipeline/run",
    payload,
    { timeoutMs: 10_000 },
  ]);
});
