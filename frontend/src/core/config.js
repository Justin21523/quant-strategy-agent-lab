const environment = import.meta.env ?? {};

export const apiBaseUrl = (environment.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
export const apiDocsUrl = environment.VITE_API_DOCS_URL ?? "/docs";
export const apiVersionPrefix = "/api/v1";
export const staticDemoMode = environment.VITE_STATIC_DEMO === "true";
export const appBasePath = environment.BASE_URL ?? "/";
