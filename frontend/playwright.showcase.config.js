import { defineConfig, devices } from "@playwright/test";

const port = process.env.SHOWCASE_FRONTEND_PORT ?? "8899";

export default defineConfig({
  testDir: "./e2e",
  testMatch: /showcase-capture\.spec\.js/,
  timeout: 120_000,
  fullyParallel: false,
  workers: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: "../docs/showcase-media/playwright-report", open: "never" }],
  ],
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    trace: "on",
    screenshot: "on",
    video: "off",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: `npm run build:pages && SHOWCASE_FRONTEND_PORT=${port} node scripts/serve-pages-preview.mjs`,
    url: `http://127.0.0.1:${port}/quant-strategy-agent-lab/`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
