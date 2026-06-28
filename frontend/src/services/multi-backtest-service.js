import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function createMultiBacktestService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/multi-backtests`;

  return {
    list({ limit = 20 } = {}) {
      return client.get(`${basePath}?limit=${encodeURIComponent(limit)}`);
    },
    run(payload) {
      return client.post(`${basePath}/run`, payload, { timeoutMs: 120_000 });
    },
    get(runId) {
      return client.get(`${basePath}/${encodeURIComponent(runId)}`);
    },
  };
}

export const multiBacktestService = createMultiBacktestService();
