import { expect, test } from "@playwright/test";

const TERMINAL_STATUSES = new Set(["success", "failed", "cancelled"]);

async function waitForJob(request, jobId) {
  const deadline = Date.now() + 25_000;
  let latest = null;

  while (Date.now() < deadline) {
    const response = await request.get(`/api/v1/jobs/${jobId}`);
    expect(response.ok()).toBeTruthy();
    latest = await response.json();
    if (TERMINAL_STATUSES.has(latest.status)) return latest;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }

  throw new Error(`Timed out waiting for ${jobId}. Last status: ${latest?.status ?? "unknown"}`);
}

async function extractQueuedJobId(page) {
  await expect(page.locator("body")).toContainText(/job_[a-f0-9]{12}/);
  const bodyText = await page.locator("body").textContent();
  return bodyText.match(/job_[a-f0-9]{12}/)?.[0];
}

async function createPermissiveScanRun(request) {
  const response = await request.post("/api/v1/scans/run", {
    data: {
      universe_id: "us_common_stocks",
      start: "2023-01-03",
      end: "2025-12-31",
      rules: {
        enable_close_above_sma_200: false,
        enable_sma_20_above_sma_60: false,
        enable_rsi_range: false,
        enable_volume_ratio_20d: false,
        enable_return_60d: false,
      },
      quality_gate: {
        min_bars: 200,
        allow_fixture_data: true,
        max_missing_weekdays: 1000,
      },
      result_limit: 10,
    },
  });
  expect(response.ok()).toBeTruthy();
  return response.json();
}

test("runs the browser-driven scanner to portfolio research pipeline", async ({
  page,
  request,
}, testInfo) => {
  const health = await request.get("/api/v1/health");
  expect(await health.json()).toMatchObject({ phase: "phase-9f", version: "0.15.0" });

  const bars = await request.get(
    "/api/v1/market/ohlcv?symbol=AAPL&start=2023-01-03&end=2025-12-31&include_indicators=true",
  );
  expect(bars.ok()).toBeTruthy();

  await page.goto("/#/parameter-scanner");
  await expect(page.getByRole("heading", { name: /Scanner operations/i })).toBeVisible();
  await expect(page.getByTestId("queue-scanner-button")).toBeEnabled();
  await page.getByTestId("queue-scanner-button").click();
  const scannerJobId = await extractQueuedJobId(page);
  const scannerJob = await waitForJob(request, scannerJobId);
  expect(scannerJob.status).toBe("success");
  expect(scannerJob.result_type).toBe("scan");

  const scanRun = await createPermissiveScanRun(request);
  expect(scanRun.matched_symbols).toBeGreaterThan(0);

  await page.goto("/#/portfolio-rebalance");
  await expect(
    page.getByRole("heading", { name: /Scanner-driven portfolio rebalance/i }),
  ).toBeVisible();
  await expect(page.getByTestId("queue-portfolio-button")).toBeEnabled();
  await page.getByTestId("portfolio-selection-mode").selectOption("fixed_scan_run");
  await page.locator("select").filter({ hasText: scanRun.run_id }).selectOption(scanRun.run_id);
  await page.getByTestId("portfolio-frequency-select").selectOption("monthly");
  await page.getByTestId("portfolio-top-n-input").fill("1");
  await page.getByTestId("portfolio-start-input").fill("2023-01-03");
  await page.getByTestId("portfolio-end-input").fill("2023-06-30");
  await page.getByTestId("portfolio-min-bars-input").fill("0");
  await page.getByTestId("queue-portfolio-button").click();

  const portfolioJobId = await extractQueuedJobId(page);
  const portfolioJob = await waitForJob(request, portfolioJobId);
  expect(portfolioJob.status).toBe("success");
  expect(portfolioJob.result_type).toBe("portfolio_rebalance");
  expect(portfolioJob.result_id).toMatch(/^pf_/);

  await page.goto("/#/jobs");
  await expect(page.getByTestId("jobs-table")).toContainText(portfolioJobId);
  await expect(page.getByTestId("jobs-table")).toContainText("success");

  await page.goto("/#/performance-report");
  await expect(page.getByRole("heading", { name: /performance analyzer/i })).toBeVisible();
  await page.getByTestId("performance-run-select").selectOption(portfolioJob.result_id);
  await page.getByTestId("load-performance-report-button").click();
  await expect(page.getByTestId("performance-summary")).toContainText("CAGR");
  await expect(page.getByTestId("performance-summary")).toContainText("Benchmark");
  await page.screenshot({
    path: testInfo.outputPath("research-pipeline-result.png"),
    fullPage: true,
  });
});

test("runs the configurable Research Lab pipeline end to end", async ({ page }, testInfo) => {
  await page.goto("/#/research-lab");
  await expect(
    page.getByRole("heading", { name: /One-click quant research pipeline/i }),
  ).toBeVisible();
  await expect(page.getByTestId("run-research-pipeline")).toBeEnabled();
  await page.getByTestId("research-run-label-input").fill("E2E Research Pipeline");
  await page.getByTestId("research-portfolio-topns-input").fill("3,4,5");
  await page.getByTestId("save-research-preset").click();
  await expect(page.getByTestId("research-status")).toContainText(/saved/i);

  await page.getByTestId("run-research-pipeline").click();
  await expect(page.getByTestId("research-status")).toContainText(/completed/i, {
    timeout: 60_000,
  });

  await expect(page.getByTestId("research-quality-heatmap")).toBeVisible();
  await expect(page.getByTestId("research-scanner-ranking")).toBeVisible();
  await expect(page.getByTestId("research-portfolio-matrix")).toContainText(/Trend Momentum/i);
  await expect(page.getByTestId("research-strategy-matrix")).toContainText(/Buy And Hold/i);

  const chartBox = await page.locator(".demo-sparkline").first().boundingBox();
  expect(chartBox?.width ?? 0).toBeGreaterThan(40);
  expect(chartBox?.height ?? 0).toBeGreaterThan(30);

  await page.goto("/#/report-center");
  await expect(page.getByRole("heading", { name: /Research report center/i })).toBeVisible();
  await page.getByTestId("load-research-report").click();
  await expect(page.getByTestId("research-report-preview")).toContainText(
    /E2E Research Pipeline|Demo Quick Research/i,
  );
  await expect(page.getByTestId("research-report-preview")).toContainText(/Portfolio Matrix/i);

  await page.screenshot({
    path: testInfo.outputPath("research-lab-pipeline-result.png"),
    fullPage: true,
  });
});
