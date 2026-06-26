import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export const healthService = {
  getHealth() {
    return apiClient.get(`${apiVersionPrefix}/health`);
  },
  getReadiness() {
    return apiClient.get(`${apiVersionPrefix}/ready`);
  },
};
