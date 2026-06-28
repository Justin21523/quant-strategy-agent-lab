import { apiClient } from "../core/api-client.js";
import { apiBaseUrl, apiVersionPrefix } from "../core/config.js";

export function createResearchService(client = apiClient) {
  const researchPath = `${apiVersionPrefix}/research`;
  const basePath = `${researchPath}/runs`;

  return {
    latest() {
      return client.get(`${basePath}/latest`, { timeoutMs: 10_000 });
    },
    list({ limit = 20 } = {}) {
      return client.get(`${basePath}?limit=${encodeURIComponent(limit)}`, { timeoutMs: 10_000 });
    },
    get(runId) {
      return client.get(`${basePath}/${encodeURIComponent(runId)}`, { timeoutMs: 10_000 });
    },
    listPresets() {
      return client.get(`${researchPath}/presets`, { timeoutMs: 10_000 });
    },
    getPreset(presetId) {
      return client.get(`${researchPath}/presets/${encodeURIComponent(presetId)}`, {
        timeoutMs: 10_000,
      });
    },
    savePreset(payload) {
      return client.post(`${researchPath}/presets`, payload, { timeoutMs: 10_000 });
    },
    report(runId) {
      return client.get(`${basePath}/${encodeURIComponent(runId)}/report?format=markdown`, {
        timeoutMs: 10_000,
      });
    },
    export(runId, { artifact = "summary", format = "json" } = {}) {
      return client.get(
        `${basePath}/${encodeURIComponent(runId)}/export?artifact=${encodeURIComponent(
          artifact,
        )}&format=${encodeURIComponent(format)}`,
        { timeoutMs: 10_000 },
      );
    },
    reportUrl(runId) {
      return `${apiBaseUrl}${apiVersionPrefix}/research/runs/${encodeURIComponent(
        runId,
      )}/report?format=markdown`;
    },
    exportUrl(runId, { artifact = "summary", format = "json" } = {}) {
      return `${apiBaseUrl}${apiVersionPrefix}/research/runs/${encodeURIComponent(
        runId,
      )}/export?artifact=${encodeURIComponent(artifact)}&format=${encodeURIComponent(format)}`;
    },
  };
}

export const researchService = createResearchService();
