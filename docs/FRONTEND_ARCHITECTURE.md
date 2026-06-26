# Frontend Architecture

## Goal

The frontend intentionally uses HTML, CSS, and Vanilla JavaScript so the project exercises browser fundamentals without collapsing into one global script.

## Module map

| Directory | Responsibility |
|---|---|
| `core/` | Router, store, event bus, API client, configuration, DOM helper |
| `layouts/` | Persistent shell, sidebar, topbar, status bar |
| `pages/` | Route-level composition and transient page state |
| `components/` | Reusable DOM units with small update methods |
| `charts/` | Visualization adapters; chart-specific DOM stays isolated |
| `services/` | API-facing use cases and endpoint construction |
| `utils/` | Pure formatting and transformation helpers |
| `styles/` | Tokens, shell, components, pages, feature styles, responsiveness |

## Market Data page state

The page owns:

- catalog response;
- selected symbol;
- start/end inputs;
- provider and fallback inputs;
- current OHLCV response;
- current request status.

The global store owns only shell-level state such as route and API connectivity. This prevents large market series from triggering unrelated application re-renders.

## DOM rules

- Dynamic API values are assigned through `textContent`.
- User/provider values are not interpolated into `innerHTML`.
- Components return an element or `{ element, update }` object.
- Route pages may return `{ element, destroy }` for cleanup.
- API paths are constructed by services, not pages.
- Chart-specific SVG creation stays under `charts/`.

## Current Market Data components

```text
MarketDataPage
├── symbol/date/provider controls
├── activity banner
├── metric cards
├── PricePreviewChart (native SVG)
├── source metadata list
├── DataQualityList
├── provider capability cards
└── MarketDataTable
```

## Why native SVG in Phase 1

The first preview intentionally avoids a chart framework. It practices:

- SVG namespaces;
- coordinate scaling;
- path/polyline construction;
- responsive `viewBox` behavior;
- accessible chart labeling;
- keeping drawing code out of page event handlers.

A later financial chart library can replace the adapter without changing the page's API response handling.
