export function createStore(initialState) {
  let state = structuredClone(initialState);
  const listeners = new Set();

  return {
    getState() {
      return structuredClone(state);
    },
    setState(patch) {
      state = { ...state, ...patch };
      for (const listener of listeners) listener(structuredClone(state));
    },
    subscribe(listener) {
      listeners.add(listener);
      listener(structuredClone(state));
      return () => listeners.delete(listener);
    },
  };
}

export const store = createStore({
  route: "/",
  api: { status: "checking", message: "Checking FastAPI…", latencyMs: null },
});
