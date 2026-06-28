import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";
import { buildQuery } from "./market-service.js";

export function createDataQualityService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/data-quality`;

  return {
    universeReport({ universeId, start, end, limit = 500 }) {
      const query = buildQuery({ start, end, limit });
      return client.get(`${basePath}/universes/${encodeURIComponent(universeId)}?${query}`, {
        timeoutMs: 30_000,
      });
    },
  };
}

export const dataQualityService = createDataQualityService();
