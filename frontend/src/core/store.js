export function createStore(initialState) {
  let state = structuredClone(initialState);
  const listeners = new Set();

  return {
    getState() {
      return structuredClone(state);
    },
    setState(patch) {
      const nextPatch = typeof patch === "function" ? patch(structuredClone(state)) : patch;
      state = { ...state, ...nextPatch };
      for (const listener of listeners) listener(structuredClone(state));
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

export const store = createStore({
  route: "/",
  api: { status: "checking", message: "Checking FastAPI…", latencyMs: null },
});
