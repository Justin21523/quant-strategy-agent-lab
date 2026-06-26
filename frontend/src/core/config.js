const environment = import.meta.env ?? {};

export const apiBaseUrl = (environment.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
export const apiDocsUrl = environment.VITE_API_DOCS_URL ?? "http://127.0.0.1:8000/docs";
export const apiVersionPrefix = "/api/v1";
