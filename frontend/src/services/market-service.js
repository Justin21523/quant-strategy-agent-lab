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
    getOhlcv({ symbol, start, end, interval = "1d" }) {
      const query = buildQuery({ symbol, start, end, interval });
      return client.get(`${basePath}/ohlcv?${query}`);
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
  };
}

export const marketService = createMarketService();
