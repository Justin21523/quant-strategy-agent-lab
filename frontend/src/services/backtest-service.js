import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function createBacktestService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/backtests`;

  return {
    run(strategyJson) {
      return client.post(`${basePath}/run`, { strategy_json: strategyJson }, { timeoutMs: 30_000 });
    },
  };
}

export const backtestService = createBacktestService();
