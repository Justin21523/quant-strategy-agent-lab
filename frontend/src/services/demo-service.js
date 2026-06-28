import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function createDemoService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/demo/research`;

  return {
    latest() {
      return client.get(`${basePath}/latest`, { timeoutMs: 10_000 });
    },
    get(runId) {
      return client.get(`${basePath}/${encodeURIComponent(runId)}`, { timeoutMs: 10_000 });
    },
  };
}

export const demoService = createDemoService();
