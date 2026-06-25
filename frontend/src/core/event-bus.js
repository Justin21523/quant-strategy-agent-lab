export function createEventBus() {
  const target = new EventTarget();

  return {
    emit(type, detail) {
      target.dispatchEvent(new CustomEvent(type, { detail }));
    },
    on(type, listener) {
      const handler = (event) => listener(event.detail);
      target.addEventListener(type, handler);
      return () => target.removeEventListener(type, handler);
    },
  };
}
