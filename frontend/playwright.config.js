import { defineConfig, devices } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(currentDir, "..");
const backendPort = process.env.E2E_BACKEND_PORT ?? "8765";
const frontendPort = process.env.E2E_FRONTEND_PORT ?? "8766";
const e2eDatabasePath =
  process.env.QSA_MARKET_DATABASE_PATH ??
  path.join(rootDir, "backend", "data", "cache", "e2e_market.sqlite3");

const backendEnv = {
  ...process.env,
  QSA_ENVIRONMENT: "e2e",
  QSA_MARKET_DATABASE_PATH: e2eDatabasePath,
  QSA_MARKET_SEED_DEMO_DATA: "true",
  QSA_MARKET_YFINANCE_ENABLED: "false",
};

export default defineConfig({
  testDir: "./e2e",
  testIgnore: /showcase-capture\.spec\.js/,
  fullyParallel: false,
  workers: 1,
  timeout: 75_000,
  expect: { timeout: 10_000 },
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command:
        "PYTHONPATH=../backend ../.venv/bin/python ../scripts/seed_e2e_universe.py && " +
        `../.venv/bin/uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port ${backendPort}`,
      cwd: currentDir,
      env: backendEnv,
      url: `http://127.0.0.1:${backendPort}/api/v1/health`,
      timeout: 30_000,
      reuseExistingServer: false,
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort} --strictPort`,
      cwd: currentDir,
      env: {
        ...process.env,
        BACKEND_PORT: backendPort,
        FRONTEND_PORT: frontendPort,
        VITE_API_DOCS_URL: `http://127.0.0.1:${backendPort}/docs`,
      },
      url: `http://127.0.0.1:${frontendPort}`,
      timeout: 30_000,
      reuseExistingServer: false,
    },
  ],
});
