import { apiBaseUrl, staticDemoMode } from "./config.js";
import { handleStaticDemoRequest } from "./static-demo-api.js";

export class ApiError extends Error {
  constructor(message, { status = 0, details = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function createApiClient({ baseUrl = apiBaseUrl, timeoutMs = 6000 } = {}) {
  async function request(path, requestOptions = {}) {
    const { timeoutMs: requestTimeout = timeoutMs, ...options } = requestOptions;
    if (staticDemoMode) {
      return handleStaticDemoRequest(path, options);
    }

    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => controller.abort(), requestTimeout);

    try {
      const response = await fetch(`${baseUrl}${path}`, {
        ...options,
        headers: {
          Accept: "application/json",
          ...(options.body ? { "Content-Type": "application/json" } : {}),
          ...options.headers,
        },
        signal: options.signal ?? controller.signal,
      });
      const contentType = response.headers.get("content-type") ?? "";
      const payload = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

      if (!response.ok) {
        const apiMessage = payload?.error?.message;
        throw new ApiError(apiMessage ?? `API request failed with status ${response.status}.`, {
          status: response.status,
          details: payload,
        });
      }
      return payload;
    } catch (error) {
      if (error.name === "AbortError") {
        throw new ApiError(`API request timed out after ${requestTimeout} ms.`);
      }
      if (error instanceof ApiError) throw error;
      throw new ApiError("Unable to reach the API.", { details: error });
    } finally {
      globalThis.clearTimeout(timeoutId);
    }
  }

  return {
    get(path, options) {
      return request(path, { ...options, method: "GET" });
    },
    post(path, body, options) {
      return request(path, { ...options, method: "POST", body: JSON.stringify(body) });
    },
  };
}

export const apiClient = createApiClient();
