import assert from "node:assert/strict";
import test from "node:test";

import { createStore } from "../src/core/store.js";

test("store updates state and notifies subscribers", () => {
  const store = createStore({ count: 0 });
  const observed = [];
  const unsubscribe = store.subscribe((state) => observed.push(state.count));

  store.setState((state) => ({ ...state, count: state.count + 1 }));
  unsubscribe();
  store.setState({ count: 2 });

  assert.equal(store.getState().count, 2);
  assert.deepEqual(observed, [1]);
});
