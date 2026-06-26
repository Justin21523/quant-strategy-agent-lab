# Frontend Architecture — Phase 4

The frontend remains pure Vanilla JavaScript with ES modules. Vite is used only for development server, proxying, and production bundling.

## Module layout

```text
frontend/src/
├── charts/
│   ├── backtest-line-chart.js
│   ├── indicator-preview-chart.js
│   └── price-preview-chart.js
├── components/
│   ├── backtest-trade-table.js
│   ├── strategy-json-preview.js
│   └── strategy-validation-list.js
├── core/
│   ├── api-client.js
│   ├── router.js
│   ├── store.js
│   └── event-bus.js
├── pages/
│   ├── market-data-page.js
│   ├── strategy-builder-page.js
│   └── backtest-lab-page.js
├── services/
│   ├── backtest-service.js
│   ├── market-service.js
│   └── strategy-service.js
└── styles/
    ├── backtest-lab.css
    ├── market-data.css
    └── strategy-builder.css
```

## Page lifecycle

Pages may return:

```javascript
{
  element,
  destroy() {
    // release listeners, pending requests, chart instances, and timers
  },
}
```

This is important for future Agent streaming and long-running scans.

## Backtest Lab

The route is:

```text
/#/backtest-lab
```

It currently supports:

```text
strategy template selection
symbol selection
market/date/capital/commission/slippage controls
typed template parameters
rendered Strategy JSON preview
POST /api/v1/backtests/run
equity SVG chart
drawdown SVG chart
metric cards
trade table
warnings
Agent-style execution steps
```

Phase 4 Backtest Lab is intentionally minimal. The richer K-line chart, markers, and polished dashboard belong to Phase 5.

## API proxy

The Vite proxy targets the dynamic backend port selected by `./scripts/dev.sh`. API proxy tests must use the printed frontend port:

```bash
curl 'http://127.0.0.1:<frontend-port>/api/v1/backtests/run'
```

Do not assume `5173`.
