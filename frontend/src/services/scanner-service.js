import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function createScannerService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/scans`;

  return {
    capabilities() {
      return client.get(`${basePath}/capabilities`);
    },
    presets() {
      return client.get(`${basePath}/presets`);
    },
    list({ limit = 20 } = {}) {
      return client.get(`${basePath}?limit=${encodeURIComponent(limit)}`);
    },
    run(payload) {
      return client.post(`${basePath}/run`, payload, { timeoutMs: 30_000 });
    },
    get(runId) {
      return client.get(`${basePath}/${encodeURIComponent(runId)}`);
    },
  };
}

export const scannerService = createScannerService();
