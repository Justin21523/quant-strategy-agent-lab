import { appBasePath, apiVersionPrefix } from "./config.js";

const SNAPSHOT_URL = `${appBasePath.replace(/\/?$/, "/")}demo-data/research-demo-latest.json`;
const NOW = "2026-01-01T09:34:00Z";

let snapshotPromise = null;
const staticJobs = new Map();
const savedResearchPresets = new Map();

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

async function snapshot() {
  snapshotPromise ??= fetch(SNAPSHOT_URL).then((response) => {
    if (!response.ok) throw new Error(`Unable to load static demo data: ${response.status}`);
    return response.json();
  });
  return clone(await snapshotPromise);
}

function splitPath(path) {
  const [pathname, queryString = ""] = path.split("?");
  return {
    pathname,
    query: new URLSearchParams(queryString),
  };
}

function staticJob({
  jobId,
  kind,
  resultId,
  resultType,
  message = "Static demo job completed.",
  total = 7,
}) {
  return {
    job_id: jobId,
    kind,
    status: "success",
    processed: total,
    total,
    message,
    result_id: resultId,
    result_type: resultType,
    error: null,
    started_at: NOW,
    finished_at: NOW,
  };
}

function makeSymbols(summary) {
  const qualitySymbols = summary.quality?.symbols ?? [];
  const scannerSymbols = summary.scanner?.results ?? [];
  const seen = new Set();
  return [...qualitySymbols, ...scannerSymbols]
    .filter((item) => {
      if (seen.has(item.symbol)) return false;
      seen.add(item.symbol);
      return true;
    })
    .map((item, index) => ({
      symbol: item.symbol,
      name: item.name ?? `${item.symbol} Synthetic Equity`,
      market: "US",
      asset_type: "equity",
      exchange: item.exchange ?? (index % 2 ? "NYSE" : "NASDAQ"),
      currency: "USD",
      timezone: "America/New_York",
      default_provider: "csv",
      supported_providers: ["csv"],
      is_demo: true,
      cached_bar_count: item.cached_bar_count ?? 736,
      first_cached_date: item.first_cached_date ?? "2023-01-03",
      last_cached_date: item.last_cached_date ?? "2025-12-31",
      cached_providers: ["csv"],
    }));
}

function providers() {
  return [
    {
      provider: "csv",
      status: "available",
      notes: "Deterministic synthetic fixture data for offline demos.",
      supports_sync: true,
    },
    {
      provider: "yfinance",
      status: "disabled",
      notes: "Live data sync is disabled in the GitHub Pages static demo.",
      supports_sync: false,
    },
  ];
}

function barSeries(symbol = "AAPL") {
  const seed = [...symbol].reduce((total, char) => total + char.charCodeAt(0), 0);
  const bars = [];
  let close = 80 + (seed % 45);
  for (let index = 0; index < 180; index += 1) {
    const date = new Date(Date.UTC(2023, 0, 3 + index));
    const drift = 0.08 + Math.sin((index + seed) / 11) * 0.28;
    close = Math.max(20, close + drift);
    const open = close - Math.sin(index / 5) * 0.8;
    const high = Math.max(open, close) + 1.2 + (index % 5) * 0.12;
    const low = Math.min(open, close) - 1.1 - (index % 3) * 0.1;
    bars.push({
      date: date.toISOString().slice(0, 10),
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      adjusted_close: Number(close.toFixed(2)),
      volume: 1_000_000 + ((seed + index * 17_123) % 1_500_000),
    });
  }
  return bars;
}

function average(values) {
  const valid = values.filter(Number.isFinite);
  if (!valid.length) return null;
  return valid.reduce((sum, value) => sum + value, 0) / valid.length;
}

function makeIndicatorBundle(bars) {
  const closes = bars.map((bar) => Number(bar.close));
  const values = bars.map((bar, index) => {
    const sma20 = average(closes.slice(Math.max(0, index - 19), index + 1));
    const sma60 = average(closes.slice(Math.max(0, index - 59), index + 1));
    const rsi = 48 + Math.sin(index / 9) * 14 + Math.min(index, 30) * 0.12;
    return {
      date: bar.date,
      values: {
        sma_20: Number((sma20 ?? bar.close).toFixed(2)),
        sma_60: Number((sma60 ?? bar.close).toFixed(2)),
        rsi_14: Number(Math.max(20, Math.min(82, rsi)).toFixed(2)),
      },
    };
  });
  return {
    count: 3,
    series: [
      { key: "sma_20", label: "SMA 20", values },
      { key: "sma_60", label: "SMA 60", values },
      { key: "rsi_14", label: "RSI 14", values },
    ],
  };
}

function makeOhlcv(summary, query) {
  const symbolId = query.get("symbol") ?? "AAPL";
  const symbol =
    makeSymbols(summary).find((item) => item.symbol === symbolId) ?? makeSymbols(summary)[0];
  const bars = barSeries(symbolId);
  return {
    symbol,
    count: bars.length,
    bars,
    effective_range: { start: bars[0]?.date, end: bars.at(-1)?.date },
    source: {
      providers: ["csv"],
      datasets: ["static-demo-fixture"],
      source_timezone: "America/New_York",
      currency: "USD",
      adjustment: "adjusted_ohlc_snapshot",
      served_from_cache: true,
      retrieved_at: NOW,
      contains_fixture_data: true,
    },
    indicators: query.get("include_indicators") === "true" ? makeIndicatorBundle(bars) : null,
    warnings: [
      {
        code: "synthetic_fixture_data",
        severity: "info",
        message: "Static GitHub Pages demo uses deterministic synthetic fixture data.",
      },
    ],
  };
}

function scannerRun(summary) {
  const results = (summary.scanner?.results ?? []).map((item) => ({
    ...item,
    metrics: {
      close: 90 + item.rank * 7,
      rsi_14: item.rsi_14,
      atr_pct: item.atr_pct,
      volume_ratio_20d: item.volume_ratio_20d,
      return_20d_pct: item.return_20d_pct,
      return_60d_pct: item.return_60d_pct,
      return_252d_pct: item.return_252d_pct,
      volume: 1_200_000 + item.rank * 130_000,
    },
  }));
  return {
    run_id: summary.scanner?.run_id ?? "scan_static_demo",
    status: "success",
    universe_id: summary.universe?.universe_id ?? "demo_research_sample",
    start: "2023-01-03",
    end: "2025-12-31",
    analyzed_symbols: results.length + (summary.scanner?.skipped?.length ?? 0),
    matched_symbols: summary.scanner?.matched_symbols ?? results.length,
    skipped_symbols: summary.scanner?.skipped_symbols ?? 0,
    sort_key: "return_60d_pct",
    sort_direction: "desc",
    results,
    skipped: (summary.scanner?.skipped ?? []).map((item) => ({
      name: `${item.symbol} Synthetic Equity`,
      details: { static_demo: true },
      ...item,
    })),
    created_at: NOW,
  };
}

function scannerPresets() {
  const baseRules = {
    enable_close_above_sma_200: true,
    enable_sma_20_above_sma_60: true,
    enable_rsi_range: true,
    enable_volume_ratio_20d: true,
    enable_return_20d: false,
    enable_return_60d: true,
    enable_return_252d: true,
    enable_atr_pct_max: false,
    close_above_sma_200: true,
    sma_20_above_sma_60: true,
    rsi_min: 45,
    rsi_max: 75,
    volume_ratio_20d_min: 1,
    return_20d_min_pct: 0,
    return_60d_min_pct: 5,
    return_252d_min_pct: 10,
    atr_pct_max: 12,
  };
  return [
    ["trend_momentum", "Trend Momentum"],
    ["pullback_in_uptrend", "Pullback in Uptrend"],
    ["volume_breakout", "Volume Breakout"],
    ["low_volatility_trend", "Low Volatility Trend"],
    ["oversold_watchlist", "Oversold Watchlist"],
  ].map(([preset_id, name], index) => ({
    preset_id,
    name,
    description: `${name} static demo scanner preset.`,
    rules: {
      ...baseRules,
      enable_atr_pct_max: preset_id === "low_volatility_trend",
      rsi_min: preset_id === "oversold_watchlist" ? 25 : 45,
      rsi_max: preset_id === "oversold_watchlist" ? 45 : 75 + index,
    },
  }));
}

function portfolioRuns(summary) {
  return (summary.portfolio_matrix ?? []).map((item) => ({
    run_id: item.run_id,
    status: "success",
    selection_mode: "fixed_scan_run",
    frequency: item.frequency,
    aggregate: {
      final_equity: item.final_equity,
      rebalance_count: item.rebalance_count,
      skipped_period_count: item.skipped_period_count,
      turnover_pct: item.turnover_pct,
    },
    performance: {
      total_return_pct: item.total_return_pct,
      annual_return_pct: item.annual_return_pct,
      annual_volatility_pct: item.annual_volatility_pct,
      cagr_pct: item.annual_return_pct,
      sharpe_ratio: item.sharpe_ratio,
      sortino_ratio: item.sharpe_ratio + 0.22,
      calmar_ratio: Math.abs(item.annual_return_pct / item.max_drawdown_pct),
      max_drawdown_pct: item.max_drawdown_pct,
      monthly_returns: item.equity_curve.map((point, index) => ({
        year: Number(point.date.slice(0, 4)),
        month: Number(point.date.slice(5, 7)),
        return_pct:
          index === 0
            ? 1.2
            : Number(((point.equity / item.equity_curve[index - 1].equity - 1) * 100).toFixed(2)),
      })),
    },
    benchmark: {
      symbol: "SPY",
      total_return_pct: Number((item.total_return_pct * 0.72).toFixed(2)),
    },
    equity_curve: item.equity_curve,
    drawdown_curve: item.drawdown_curve,
    holdings: [],
    skipped_periods: [],
    created_at: NOW,
  }));
}

function portfolioPresets() {
  return [
    [
      "trend_momentum_monthly_top20",
      "Trend Momentum monthly top 20",
      "trend_momentum",
      "monthly",
      20,
    ],
    [
      "low_volatility_monthly_top30",
      "Low Volatility Trend monthly top 30",
      "low_volatility_trend",
      "monthly",
      30,
    ],
    [
      "oversold_weekly_top10",
      "Oversold Watchlist weekly top 10",
      "oversold_watchlist",
      "weekly",
      10,
    ],
  ].map(([preset_id, name, scannerPresetId, frequency, topN]) => ({
    preset_id,
    name,
    description: `${name} static demo portfolio preset.`,
    config: {
      selection_mode: "rescan_each_period",
      scanner_preset_id: scannerPresetId,
      frequency,
      top_n: topN,
      lookback_days: 365,
    },
  }));
}

function strategyTemplates() {
  return [
    ["buy_and_hold", "Buy and Hold", "baseline"],
    ["ma_crossover", "MA Crossover", "trend_following"],
    ["ma_crossover_rsi", "MA Crossover + RSI", "trend_following"],
    ["rsi_mean_reversion", "RSI Mean Reversion", "mean_reversion"],
    ["macd_trend_following", "MACD Trend Following", "trend_following"],
  ].map(([id, name, category]) => ({
    id,
    name,
    category,
    description: `${name} deterministic static demo template.`,
    summary: `${name} sample Strategy JSON DSL template.`,
    parameters: [
      {
        key: "max_position_pct",
        label: "Max position",
        kind: "float",
        default: 1,
        description: "Portfolio fraction",
        minimum: 0.01,
        maximum: 1,
        step: 0.01,
        unit: "fraction",
        options: [],
      },
    ],
    tags: [category],
    indicator_kinds: id === "buy_and_hold" ? [] : ["sma", "rsi"],
    risk_notes: ["Static demo data is synthetic and for workflow review only."],
    default_parameters: { max_position_pct: 1 },
    parameter_count: 1,
    research_notes: "Static GitHub Pages demo template.",
  }));
}

function renderedStrategy(body = {}) {
  const payload = typeof body === "string" ? JSON.parse(body || "{}") : body;
  return {
    id: `static_${payload.template_id ?? "strategy"}`,
    name: `Static ${payload.template_id ?? "Strategy"}`,
    symbol: payload.symbol ?? "AAPL",
    market: payload.market ?? "US",
    start: payload.start ?? "2023-01-03",
    end: payload.end ?? "2025-12-31",
    initial_cash: payload.initial_cash ?? 100000,
    commission: payload.commission ?? 0.001,
    slippage: payload.slippage ?? 0.0005,
    rules: {
      entry: [{ type: "always_in" }],
      exit: [{ type: "final_bar" }],
    },
    parameters: payload.parameters ?? {},
  };
}

function backtestResult(body = {}) {
  const strategy =
    typeof body === "string" ? JSON.parse(body || "{}").strategy_json : body.strategy_json;
  const symbol = strategy?.symbol ?? "AAPL";
  const bars = barSeries(symbol).slice(0, 90);
  const equityCurve = bars
    .filter((_, index) => index % 9 === 0)
    .map((bar, index) => ({
      date: bar.date,
      equity: 100000 + index * 1900 + Math.sin(index) * 1100,
    }));
  const drawdownCurve = equityCurve.map((point, index) => ({
    date: point.date,
    drawdown_pct: index % 4 === 0 ? 0 : -1.2 - index * 0.25,
  }));
  return {
    run_id: "bt_static_demo",
    strategy_name: strategy?.name ?? "Static Strategy",
    symbol,
    data: { start: bars[0].date, end: bars.at(-1).date, contains_fixture_data: true },
    metrics: {
      total_return_pct: 12.8,
      annual_return_pct: 16.4,
      sharpe_ratio: 1.22,
      max_drawdown_pct: -5.4,
      win_rate_pct: 58.3,
      profit_factor: 1.44,
      trade_count: 4,
    },
    trades: [
      {
        entry_date: bars[8].date,
        exit_date: bars[38].date,
        entry_price: bars[8].close,
        exit_price: bars[38].close,
        quantity: 100,
        pnl: 860,
      },
      {
        entry_date: bars[44].date,
        exit_date: bars[80].date,
        entry_price: bars[44].close,
        exit_price: bars[80].close,
        quantity: 100,
        pnl: 1420,
      },
    ],
    equity_curve: equityCurve,
    drawdown_curve: drawdownCurve,
    agent_steps: agentWorkflow().steps.map((step) => ({ ...step, status: "success" })),
    warnings: [
      {
        code: "static_demo_fixture",
        severity: "info",
        message: "This backtest is served from static synthetic demo data.",
      },
    ],
  };
}

function multiBacktestRun(summary, body = {}) {
  const payload = typeof body === "string" ? JSON.parse(body || "{}") : body;
  const rows = (summary.scanner?.results ?? []).slice(0, Number(payload.top_n ?? 6));
  const results = rows.map((row, index) => ({
    symbol: row.symbol,
    status: "success",
    metrics: {
      total_return_pct: Number((row.return_60d_pct * 0.65 - index).toFixed(2)),
      max_drawdown_pct: Number((-3.2 - index * 0.8).toFixed(2)),
      sharpe_ratio: Number((1.25 - index * 0.06).toFixed(2)),
      win_rate_pct: 52 + index,
      trade_count: 2 + index,
    },
    warnings: index > 3 ? ["fixture_data"] : [],
  }));
  return {
    run_id: "mb_static_demo",
    status: "success",
    requested_symbols: results.length,
    successful_symbols: results.length,
    failed_symbols: 0,
    aggregate: {
      average_total_return_pct: Number(
        (
          results.reduce((sum, item) => sum + item.metrics.total_return_pct, 0) / results.length
        ).toFixed(2),
      ),
      average_max_drawdown_pct: -5.4,
      best_symbol: results[0]?.symbol,
      worst_symbol: results.at(-1)?.symbol,
    },
    results,
  };
}

function agentWorkflow() {
  return {
    workflow_key: "backtest_workflow",
    label: "Backtest Agent Timeline",
    phase: "phase-6",
    total_steps: 8,
    steps: [
      ["strategy_received", "Strategy received"],
      ["validate_strategy", "Strategy validated"],
      ["fetch_market_data", "Market data loaded"],
      ["compute_indicators", "Indicators computed"],
      ["generate_signals", "Signals generated"],
      ["run_backtest", "Backtest executed"],
      ["analyze_performance", "Performance analyzed"],
      ["risk_review", "Risk notes reviewed"],
    ].map(([key, label], index) => ({
      sequence: index + 1,
      key,
      label,
      description: `${label} in the static demo workflow.`,
      status: "pending",
    })),
  };
}

function researchReport(summary) {
  return [
    `# ${summary.run_id} Research Report`,
    "",
    "## Portfolio Matrix",
    ...(summary.portfolio_matrix ?? []).map(
      (item) =>
        `- ${item.preset}: ${item.total_return_pct}% return, ${item.max_drawdown_pct}% max drawdown.`,
    ),
    "",
    "## Scanner",
    `Matched ${summary.scanner?.matched_symbols ?? 0} symbols and skipped ${summary.scanner?.skipped_symbols ?? 0}.`,
    "",
    "Static GitHub Pages demo uses deterministic fixture data for workflow review.",
  ].join("\n");
}

export async function handleStaticDemoRequest(path, options = {}) {
  const { pathname, query } = splitPath(path);
  const method = options.method ?? "GET";
  const { summary } = await snapshot();
  const symbols = makeSymbols(summary);
  const scans = [scannerRun(summary)];
  const portfolios = portfolioRuns(summary);
  const jobs = [
    staticJob({
      jobId: "job_static_demo_research",
      kind: "research_pipeline",
      resultId: summary.run_id,
      resultType: "research_run",
      message: "Static research pipeline completed.",
    }),
    staticJob({
      jobId: "job_static_demo_scan",
      kind: "scanner",
      resultId: scans[0].run_id,
      resultType: "scan",
      message: "Static scanner job completed.",
      total: 20,
    }),
    staticJob({
      jobId: "job_static_demo_portfolio",
      kind: "portfolio_rebalance",
      resultId: portfolios[0]?.run_id,
      resultType: "portfolio_rebalance",
      message: "Static portfolio job completed.",
      total: 8,
    }),
    ...staticJobs.values(),
  ];

  if (pathname === `${apiVersionPrefix}/health`) {
    return {
      status: "ok",
      service: "Quant Strategy Agent Lab API",
      version: "0.15.0",
      environment: "static-demo",
      phase: "phase-9f",
      timestamp: NOW,
    };
  }
  if (pathname === `${apiVersionPrefix}/ready`) {
    return { status: "ready", checks: { api: "ok", "static-demo": "ok" } };
  }
  if (pathname === `${apiVersionPrefix}/demo/research/latest`) return { summary };
  if (pathname.startsWith(`${apiVersionPrefix}/demo/research/`)) return { summary };
  if (pathname === `${apiVersionPrefix}/research/runs/latest`) return { summary };
  if (pathname === `${apiVersionPrefix}/research/runs`) return { total: 1, runs: [summary] };
  if (pathname.startsWith(`${apiVersionPrefix}/research/runs/`) && pathname.endsWith("/report")) {
    return researchReport(summary);
  }
  if (pathname.startsWith(`${apiVersionPrefix}/research/runs/`) && pathname.endsWith("/export")) {
    return { summary };
  }
  if (pathname.startsWith(`${apiVersionPrefix}/research/runs/`)) return { summary };
  if (pathname === `${apiVersionPrefix}/research/presets`) {
    return {
      total: savedResearchPresets.size + 1,
      presets: [
        {
          preset_id: "demo_quick_research",
          name: "Demo Quick Research",
          description: "Static sample research workflow.",
          config: {},
        },
        ...savedResearchPresets.values(),
      ],
    };
  }
  if (pathname.startsWith(`${apiVersionPrefix}/research/presets/`) && method === "GET") {
    const presetId = pathname.split("/").at(-1);
    return (
      savedResearchPresets.get(presetId) ?? {
        preset_id: "demo_quick_research",
        name: "Demo Quick Research",
        description: "Static sample research workflow.",
        config: {},
      }
    );
  }
  if (pathname === `${apiVersionPrefix}/research/presets` && method === "POST") {
    const body = JSON.parse(options.body ?? "{}");
    savedResearchPresets.set(body.preset_id, body);
    return body;
  }

  if (pathname === `${apiVersionPrefix}/market/providers`) return { providers: providers() };
  if (pathname === `${apiVersionPrefix}/market/symbols`) {
    return { total: symbols.length, symbols, providers: providers() };
  }
  if (pathname === `${apiVersionPrefix}/market/ohlcv`) return makeOhlcv(summary, query);
  if (pathname === `${apiVersionPrefix}/market/sync` && method === "POST") {
    return {
      run_id: "sync_static_demo",
      results: [
        {
          symbol: "AAPL",
          status: "success",
          bars_stored: 180,
          provider_used: "csv",
          fallback_used: false,
          attempts: ["csv"],
        },
      ],
    };
  }
  if (pathname === `${apiVersionPrefix}/market/batch-sync` && method === "POST") {
    return {
      run_id: "batch_static_demo",
      child_sync_run_id: "sync_static_demo",
      cursor_start: 0,
      cursor_end: 20,
      next_cursor: null,
      complete: true,
      processed: 20,
      successful: 20,
      failed: 0,
    };
  }
  if (pathname === `${apiVersionPrefix}/market/batch-sync/runs`) {
    return {
      total: 1,
      runs: [
        {
          run_id: "batch_static_demo",
          child_sync_run_id: "sync_static_demo",
          cursor_start: 0,
          cursor_end: 20,
          processed: 20,
          successful: 20,
          failed: 0,
          next_cursor: null,
          complete: true,
        },
      ],
    };
  }
  if (pathname === `${apiVersionPrefix}/indicators/catalog`) {
    return { indicators: ["sma", "ema", "rsi", "macd", "bollinger_bands", "atr"] };
  }

  if (pathname === `${apiVersionPrefix}/universes`) {
    return {
      total: 1,
      universes: [
        {
          universe_id: summary.universe?.universe_id ?? "demo_research_sample",
          name: "Demo Research Sample",
          description: "Static 20-stock synthetic sample universe.",
          market: "US",
          asset_type: "equity",
          source: "static-demo-fixture",
          source_url: "frontend/public/demo-data",
          member_count: summary.universe?.member_count ?? symbols.length,
          refreshed_at: NOW,
        },
      ],
    };
  }
  if (pathname.endsWith("/us-common-stocks/refresh")) {
    return {
      universe: { universe_id: "demo_research_sample", name: "Demo Research Sample" },
      member_count: symbols.length,
    };
  }
  if (pathname.startsWith(`${apiVersionPrefix}/universes/`)) {
    return {
      universe: {
        universe_id: "demo_research_sample",
        name: "Demo Research Sample",
        refreshed_at: NOW,
      },
      member_count: symbols.length,
      members: symbols,
    };
  }
  if (pathname.startsWith(`${apiVersionPrefix}/data-quality/universes/`)) {
    return {
      universe_id: summary.universe?.universe_id ?? "demo_research_sample",
      generated_at: NOW,
      ...summary.quality,
    };
  }

  if (pathname === `${apiVersionPrefix}/scans/capabilities`)
    return { sort_keys: ["return_60d_pct", "rsi_14", "atr_pct"] };
  if (pathname === `${apiVersionPrefix}/scans/presets`) {
    const presets = scannerPresets();
    return { total: presets.length, presets };
  }
  if (pathname === `${apiVersionPrefix}/scans`) return { total: scans.length, runs: scans };
  if (pathname === `${apiVersionPrefix}/scans/run` && method === "POST") return scans[0];
  if (pathname.startsWith(`${apiVersionPrefix}/scans/`)) return scans[0];

  if (pathname === `${apiVersionPrefix}/portfolios/presets`) {
    const presets = portfolioPresets();
    return { total: presets.length, presets };
  }
  if (pathname.startsWith(`${apiVersionPrefix}/portfolios/presets/`)) {
    return portfolioPresets()[0];
  }
  if (pathname === `${apiVersionPrefix}/portfolios/rebalance`) {
    return { total: portfolios.length, runs: portfolios };
  }
  if (pathname.startsWith(`${apiVersionPrefix}/portfolios/rebalance/`)) {
    return portfolios.find((item) => pathname.endsWith(item.run_id)) ?? portfolios[0];
  }

  if (pathname === `${apiVersionPrefix}/multi-backtests`) {
    return {
      total: summary.strategy_comparison?.length ?? 0,
      runs: summary.strategy_comparison ?? [],
    };
  }
  if (pathname === `${apiVersionPrefix}/multi-backtests/run` && method === "POST") {
    return multiBacktestRun(summary, options.body);
  }
  if (pathname.startsWith(`${apiVersionPrefix}/multi-backtests/`)) return multiBacktestRun(summary);

  if (pathname === `${apiVersionPrefix}/strategies/templates`) {
    const templates = strategyTemplates();
    return { total: templates.length, templates };
  }
  if (
    pathname.startsWith(`${apiVersionPrefix}/strategies/templates/`) &&
    pathname.endsWith("/render")
  ) {
    return renderedStrategy(options.body);
  }
  if (pathname.startsWith(`${apiVersionPrefix}/strategies/templates/`)) {
    const templateId = pathname.split("/").at(-1);
    return strategyTemplates().find((item) => item.id === templateId) ?? strategyTemplates()[0];
  }
  if (pathname === `${apiVersionPrefix}/strategies/validate`) {
    return { valid: true, issues: [] };
  }
  if (pathname === `${apiVersionPrefix}/backtests/run` && method === "POST")
    return backtestResult(options.body);
  if (pathname === `${apiVersionPrefix}/agent/backtest-workflow`) return agentWorkflow();

  if (pathname === `${apiVersionPrefix}/jobs`) return { total: jobs.length, jobs };
  if (pathname.endsWith("/events")) return { events: [] };
  if (pathname.startsWith(`${apiVersionPrefix}/jobs/`) && method === "GET") {
    const jobId = pathname.split("/").at(-1);
    return jobs.find((job) => job.job_id === jobId) ?? jobs[0];
  }
  if (pathname.startsWith(`${apiVersionPrefix}/jobs/`) && method === "POST") {
    const kind = pathname.split("/").slice(-2).join("_").replace("run", "job");
    const job = staticJob({
      jobId: `job_static_${Date.now()}`,
      kind,
      resultId: pathname.includes("portfolio")
        ? portfolios[0]?.run_id
        : pathname.includes("scan")
          ? scans[0].run_id
          : summary.run_id,
      resultType: pathname.includes("portfolio")
        ? "portfolio_rebalance"
        : pathname.includes("scan")
          ? "scan"
          : "research_run",
      message: "Static demo job completed.",
    });
    staticJobs.set(job.job_id, job);
    return job;
  }

  throw new Error(`Static demo endpoint is not implemented: ${method} ${pathname}`);
}
