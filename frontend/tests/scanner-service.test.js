import assert from "node:assert/strict";
import test from "node:test";

import { createScannerService } from "../src/services/scanner-service.js";

test("scanner service builds capability, run, and read contracts", async () => {
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
  const service = createScannerService(client);
  const payload = {
    universe_id: "us_common_stocks",
    start: "2024-01-01",
    end: "2024-12-31",
  };

  await service.capabilities();
  await service.presets();
  await service.list({ limit: 5 });
  await service.run(payload);
  await service.get("scan_123");

  assert.deepEqual(calls, [
    ["GET", "/api/v1/scans/capabilities"],
    ["GET", "/api/v1/scans/presets"],
    ["GET", "/api/v1/scans?limit=5"],
    ["POST", "/api/v1/scans/run", payload, { timeoutMs: 30_000 }],
    ["GET", "/api/v1/scans/scan_123"],
  ]);
});
