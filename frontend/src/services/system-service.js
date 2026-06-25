export const systemService = {
  getHealth(apiClient) {
    return apiClient.get('/health');
  },
  getInfo(apiClient) {
    return apiClient.get('/system/info');
  },
};
