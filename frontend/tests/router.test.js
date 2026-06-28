import assert from "node:assert/strict";
import test from "node:test";

import { normalizeHashPath } from "../src/core/router.js";

test("normalizeHashPath strips hash and query strings", () => {
  assert.equal(normalizeHashPath("#/backtest-lab?symbol=AAPL"), "/backtest-lab");
});

test("normalizeHashPath falls back to root for empty hashes", () => {
  assert.equal(normalizeHashPath("#"), "/");
  assert.equal(normalizeHashPath(""), "/");
});
