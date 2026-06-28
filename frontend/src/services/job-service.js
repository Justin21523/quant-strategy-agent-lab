import { apiClient } from "../core/api-client.js";
import { apiVersionPrefix } from "../core/config.js";

export function createJobService(client = apiClient) {
  const basePath = `${apiVersionPrefix}/jobs`;

  return {
    list({ limit = 50 } = {}) {
      return client.get(`${basePath}?limit=${encodeURIComponent(limit)}`);
    },
    get(jobId) {
      return client.get(`${basePath}/${encodeURIComponent(jobId)}`);
    },
    events(jobId) {
      return client.get(`${basePath}/${encodeURIComponent(jobId)}/events`);
    },
    cancel(jobId) {
      return client.post(`${basePath}/${encodeURIComponent(jobId)}/cancel`, {});
    },
    queueBatchSync(payload) {
      return client.post(`${basePath}/market/batch-sync`, payload, { timeoutMs: 10_000 });
    },
    queueScan(payload) {
      return client.post(`${basePath}/scans/run`, payload, { timeoutMs: 10_000 });
    },
    queuePortfolio(payload) {
      return client.post(`${basePath}/portfolios/rebalance/run`, payload, {
        timeoutMs: 10_000,
      });
    },
    queueResearchDemo() {
      return client.post(`${basePath}/demo/research/run`, {}, { timeoutMs: 10_000 });
    },
    queueResearchPipeline(payload) {
      return client.post(`${basePath}/research/pipeline/run`, payload, { timeoutMs: 10_000 });
    },
  };
}

export const jobService = createJobService();
