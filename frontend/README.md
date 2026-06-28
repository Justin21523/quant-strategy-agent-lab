# Frontend

Framework-free browser application using HTML, CSS, Vanilla JavaScript, ES modules, Fetch API, a hash router, a small observable store, and native SVG.

```bash
npm ci
npm run dev
npm run lint
npm run test
npm run e2e
npm run build
```

`npm run e2e` runs the Playwright browser smoke test for the research pipeline. It starts its own backend/frontend servers, seeds a deterministic local universe, queues scanner and portfolio jobs, and verifies the Performance Report page.

## Module rules

- `core/`: framework-like primitives, never financial features;
- `layouts/`: shell, navigation, top/status bars;
- `pages/`: route-level composition and lifecycle;
- `components/`: reusable DOM components;
- `charts/`: visualization adapters with `element` and `update` contracts;
- `services/`: HTTP-facing use cases, never DOM manipulation;
- `styles/`: tokens, layout, components, pages, and responsiveness.

The Phase 1 Market Data Lab is implemented in `src/pages/market-data-page.js` and consumes only the versioned FastAPI contract.
