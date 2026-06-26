import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function createStrategyService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/strategies`;

  return {
    getTemplates() {
      return client.get(`${basePath}/templates`);
    },
    getTemplate(templateId) {
      return client.get(`${basePath}/templates/${encodeURIComponent(templateId)}`);
    },
    renderTemplate(templateId, payload) {
      return client.post(`${basePath}/templates/${encodeURIComponent(templateId)}/render`, payload);
    },
    validate(strategyJson) {
      return client.post(`${basePath}/validate`, { strategy_json: strategyJson });
    },
  };
}

export const strategyService = createStrategyService();
