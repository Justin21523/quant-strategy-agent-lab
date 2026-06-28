import assert from "node:assert/strict";
import test from "node:test";

import { createDataQualityService } from "../src/services/data-quality-service.js";

test("data-quality service builds universe report contract", async () => {
  const calls = [];
  const client = {
    get(path, options) {
      calls.push(["GET", path, options]);
      return Promise.resolve({});
    },
  };
  const service = createDataQualityService(client);

  await service.universeReport({
    universeId: "us_common_stocks",
    start: "2025-01-01",
    end: "2025-12-31",
    limit: 250,
  });

  assert.deepEqual(calls, [
    [
      "GET",
      "/api/v1/data-quality/universes/us_common_stocks?start=2025-01-01&end=2025-12-31&limit=250",
      { timeoutMs: 30_000 },
    ],
  ]);
});
