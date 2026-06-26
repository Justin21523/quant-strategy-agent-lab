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

## Phase 2 update — Indicator preview modules

The Market Data Lab now composes one more chart adapter:

```text
market-data-page.js
  ├── market-service.js
  ├── price-preview-chart.js
  └── indicator-preview-chart.js
```

`indicator-preview-chart.js` is still plain DOM/SVG code. It renders:

- close price with SMA 20 and SMA 60 overlays;
- RSI 14 oscillator with 70 and 30 guide lines;
- legends generated from the indicator keys in the API bundle.

The page requests indicator data only through the service layer:

```text
marketService.getOhlcv({ includeIndicators: true })
```

Local development URLs are dynamic. The `API Docs` link is provided through `VITE_API_DOCS_URL` by `scripts/dev.sh`, and the `/api` proxy receives the same backend port through `BACKEND_PORT`.

## Phase 3 update — Strategy Builder modules

The Strategy Builder route is now implemented at `/#/strategy-builder`.

```text
strategy-builder-page.js
  ├── strategy-service.js
  ├── market-service.js
  ├── strategy-json-preview.js
  └── strategy-validation-list.js
```

State ownership:

- the page owns selected template, typed parameter values, context fields, current validation report, and last rendered JSON;
- the backend owns template rules and Strategy JSON rendering;
- the frontend never constructs rule operators or indicator dependencies locally.

The page uses dynamic controls generated from the backend template metadata. Every input/change event schedules a short debounced render call to:

```text
POST /api/v1/strategies/templates/{template_id}/render
```

The JSON preview uses `textContent`, not `innerHTML`, and displays the exact backend-rendered object.
