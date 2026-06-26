import assert from "node:assert/strict";
import test from "node:test";

import { matchRoute } from "../src/core/router.js";

const routes = [
  { path: "/", label: "Home" },
  { path: "/backtest-lab", label: "Backtest" },
];

test("matchRoute normalizes hash paths", () => {
  assert.equal(matchRoute(routes, "#/backtest-lab").label, "Backtest");
});

test("matchRoute falls back to the first route", () => {
  assert.equal(matchRoute(routes, "#/unknown").label, "Home");
});
