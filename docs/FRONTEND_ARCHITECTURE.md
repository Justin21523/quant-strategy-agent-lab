# Frontend Architecture

## Objective

Practice browser-native HTML, CSS, JavaScript, DOM events, modules, state, network calls, and rendering without allowing the codebase to collapse into one global script.

## Layer responsibilities

| Layer | Owns | Must not own |
|---|---|---|
| `core/` | router, store, event bus, API transport, configuration | page-specific UI |
| `layouts/` | persistent shell, navigation, top/status bars | quantitative logic |
| `pages/` | route-level orchestration and page lifecycle | raw URL construction |
| `components/` | reusable DOM output with explicit inputs | data fetching |
| `services/` | use-case-oriented API calls | DOM mutation |
| `charts/` | future vendor chart adapters | page state |
| `utils/` | pure reusable helpers | global mutable state |
| `styles/` | design tokens, base, layout, components, pages | inline business rules |

## Page contract

A route renderer returns either an `HTMLElement` or this lifecycle object:

```js
{
  element: HTMLElement,
  destroy() {
    // remove listeners, timers, observers, and chart instances
  },
}
```

The router invokes `destroy()` before replacing a page. This matters later because financial charts and long-running Agent event streams otherwise leak listeners and memory.

## State policy

Global state is reserved for information shared across routes, such as API availability and a selected run identifier. A strategy form draft, fetched OHLCV array, or chart instance stays local to the owning page until a demonstrated cross-route need exists.

## Rendering and security

- dynamic server values should be assigned with `textContent`;
- `innerHTML` is limited to trusted static templates;
- API errors become visible UI states rather than silent console failures;
- every async page task must tolerate the page being destroyed before completion;
- buttons expose disabled/loading states during requests.

## Future chart integration

Each vendor receives one adapter module. For example:

```text
Backtest page → equity-curve-chart.js → ECharts
Backtest page → candlestick-chart.js → Lightweight Charts
```

Pages receive stable methods such as `render`, `resize`, and `destroy`, not the full third-party API.
