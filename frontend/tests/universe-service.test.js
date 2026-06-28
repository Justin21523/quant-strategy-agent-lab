import assert from "node:assert/strict";
import test from "node:test";

import { createUniverseService } from "../src/services/universe-service.js";

test("universe service builds list, detail, and refresh contracts", async () => {
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
  const service = createUniverseService(client);

  await service.list();
  await service.get("us_common_stocks");
  await service.refreshUsCommonStocks();

  assert.deepEqual(calls, [
    ["GET", "/api/v1/universes"],
    ["GET", "/api/v1/universes/us_common_stocks"],
    ["POST", "/api/v1/universes/us-common-stocks/refresh", {}, { timeoutMs: 30_000 }],
  ]);
});
