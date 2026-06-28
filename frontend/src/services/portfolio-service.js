import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function createPortfolioService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/portfolios`;

  return {
    listRuns({ limit = 20 } = {}) {
      return client.get(`${basePath}/rebalance?limit=${encodeURIComponent(limit)}`);
    },
    getRun(runId) {
      return client.get(`${basePath}/rebalance/${encodeURIComponent(runId)}`);
    },
    listPresets() {
      return client.get(`${basePath}/presets`);
    },
    getPreset(presetId) {
      return client.get(`${basePath}/presets/${encodeURIComponent(presetId)}`);
    },
    savePreset(payload) {
      return client.post(`${basePath}/presets`, payload);
    },
  };
}

export const portfolioService = createPortfolioService();
