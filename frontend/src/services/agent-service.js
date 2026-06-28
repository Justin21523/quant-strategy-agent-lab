import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function createAgentService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/agent`;

  return {
    getBacktestWorkflow() {
      return client.get(`${basePath}/backtest-workflow`);
    },
  };
}

export const agentService = createAgentService();
