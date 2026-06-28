import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function createUniverseService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/universes`;

  return {
    list() {
      return client.get(basePath);
    },
    get(universeId) {
      return client.get(`${basePath}/${encodeURIComponent(universeId)}`);
    },
    refreshUsCommonStocks() {
      return client.post(`${basePath}/us-common-stocks/refresh`, {}, { timeoutMs: 30_000 });
    },
  };
}

export const universeService = createUniverseService();
