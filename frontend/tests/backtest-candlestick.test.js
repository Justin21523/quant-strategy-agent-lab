import assert from "node:assert/strict";
import test from "node:test";

import {
  buildTradeMarkers,
  normalizeBacktestBars,
} from "../src/charts/backtest-candlestick-chart.js";

test("normalizeBacktestBars filters invalid bars", () => {
  assert.deepEqual(
    normalizeBacktestBars([
      {
        date: "x",
        open: 1,
        high: 2,
        low: 0.5,
        close: 1.5,
        volume: 10,
      },
      {
        date: "bad",
        open: "nope",
        high: 2,
        low: 1,
        close: 1,
      },
    ]),
    [
      {
        date: "x",
        open: 1,
        high: 2,
        low: 0.5,
        close: 1.5,
        volume: 10,
        indicators: {},
      },
    ],
  );
});

test("buildTradeMarkers converts closed trades into entry and exit markers", () => {
  assert.equal(
    buildTradeMarkers([
      {
        trade_id: "t1",
        entry_date: "2025-01-02",
        entry_price: 101.5,
        exit_date: "2025-01-08",
        exit_price: 109.25,
      },
    ]).length,
    2,
  );
});
