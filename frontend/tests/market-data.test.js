import assert from "node:assert/strict";
import test from "node:test";

import { createMarketService, buildQuery } from "../src/services/market-service.js";
import {
  formatCompact,
  formatInteger,
  formatPrice,
  formatTimestamp,
} from "../src/utils/market-formatters.js";

test("buildQuery includes defined parameters and omits empty values", () => {
  assert.equal(
    buildQuery({ symbol: "BRK B", start: "2025-01-01", end: "", interval: "1d" }),
    "symbol=BRK+B&start=2025-01-01&interval=1d",
  );
});

test("market service builds read and synchronization contracts", async () => {
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
  const service = createMarketService(client);

  await service.getOhlcv({
    symbol: "SPY",
    start: "2025-01-01",
    end: "2025-12-31",
    includeIndicators: true,
  });
  await service.getIndicatorCatalog();
  await service.sync({
    symbols: ["SPY"],
    provider: "auto",
    start: "2025-01-01",
    end: "2025-12-31",
    allowFallback: true,
  });

  assert.deepEqual(calls[0], [
    "GET",
    "/api/v1/market/ohlcv?symbol=SPY&start=2025-01-01&end=2025-12-31&interval=1d&include_indicators=true",
  ]);
  assert.deepEqual(calls[1], ["GET", "/api/v1/indicators/catalog"]);
  assert.deepEqual(calls[2][2], {
    symbols: ["SPY"],
    provider: "auto",
    start: "2025-01-01",
    end: "2025-12-31",
    allow_fallback: true,
  });
  assert.equal(calls[2][3].timeoutMs, 20_000);
});

test("market formatters provide stable display fallbacks", () => {
  assert.equal(formatPrice(123.45678), "123.4568");
  assert.equal(formatInteger(1234567), "1,234,567");
  assert.match(formatCompact(1_250_000), /1\.3M|1\.2M/);
  assert.equal(formatPrice(undefined), "—");
  assert.equal(formatTimestamp("not-a-date"), "not-a-date");
});
