import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function buildQuery(parameters = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(parameters)) {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  }
  return query.toString();
}

export function createMarketService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/market`;

  return {
    getProviders() {
      return client.get(`${basePath}/providers`);
    },
    getSymbols(filters = {}) {
      const query = buildQuery(filters);
      return client.get(`${basePath}/symbols${query ? `?${query}` : ""}`);
    },
    getOhlcv({ symbol, start, end, interval = "1d", includeIndicators = false }) {
      const query = buildQuery({
        symbol,
        start,
        end,
        interval,
        include_indicators: includeIndicators ? true : undefined,
      });
      return client.get(`${basePath}/ohlcv?${query}`);
    },
    getIndicatorCatalog() {
      return client.get(`${apiVersionPrefix}/indicators/catalog`);
    },
    sync({ symbols, provider, start, end, allowFallback = true }) {
      return client.post(
        `${basePath}/sync`,
        {
          symbols,
          provider,
          start,
          end,
          allow_fallback: allowFallback,
        },
        { timeoutMs: 20_000 },
      );
    },
    batchSync({
      universeId,
      provider = "yfinance",
      start,
      end,
      chunkSize = 50,
      cursor = 0,
      allowFallback = false,
      mode = "all",
      staleAfter,
      failedRunId,
    }) {
      const payload = {
        universe_id: universeId,
        provider,
        start,
        end,
        chunk_size: chunkSize,
        cursor,
        allow_fallback: allowFallback,
      };
      if (mode !== "all") payload.mode = mode;
      if (staleAfter) payload.stale_after = staleAfter;
      if (failedRunId) payload.failed_run_id = failedRunId;
      return client.post(`${basePath}/batch-sync`, payload, { timeoutMs: 60_000 });
    },
    getBatchSyncRuns({ universeId, limit = 20 } = {}) {
      const query = buildQuery({ universe_id: universeId, limit });
      return client.get(`${basePath}/batch-sync/runs${query ? `?${query}` : ""}`);
    },
    getSyncRuns({ runId, limit = 100 } = {}) {
      const query = buildQuery({ run_id: runId, limit });
      return client.get(`${basePath}/sync-runs${query ? `?${query}` : ""}`);
    },
  };
}

export const marketService = createMarketService();
