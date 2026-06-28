import { expect, test } from "@playwright/test";

test("activates the in-app research demo and returns to dashboard summary", async ({
  page,
  request,
}, testInfo) => {
  const health = await request.get("/api/v1/health");
  expect(await health.json()).toMatchObject({ phase: "phase-9f", version: "0.15.0" });

  await page.goto("/#/");
  await expect(page.getByRole("heading", { name: /Demo Studio research playback/i })).toBeVisible();
  await expect(page.getByTestId("demo-status")).toContainText(/snapshot|loaded/i);
  await expect(page.getByTestId("demo-timeline")).toBeVisible();
  await expect(page.getByTestId("quality-heatmap")).toBeVisible();
  await expect(page.getByTestId("scanner-ranking")).toBeVisible();
  await expect(page.getByTestId("portfolio-card-grid")).toBeVisible();
  await expect(page.getByTestId("strategy-bars")).toBeVisible();
  await expect(page.getByTestId("demo-report")).toBeVisible();

  const heatmapTiles = page.locator(".quality-tile");
  expect(await heatmapTiles.count()).toBeGreaterThanOrEqual(14);
  const sparklineBox = await page.locator(".demo-sparkline").first().boundingBox();
  expect(sparklineBox?.width ?? 0).toBeGreaterThan(40);
  expect(sparklineBox?.height ?? 0).toBeGreaterThan(30);

  await page.getByTestId("activate-demo-button").click();
  await expect(page.getByTestId("demo-overlay")).toBeVisible();
  await expect(page.getByTestId("demo-overlay")).toContainText(/Auto Demo/i);
  await expect(page.getByTestId("demo-overlay")).toContainText(/Complete/i, { timeout: 90_000 });

  await expect(page).toHaveURL(/#\/$/);
  await expect(page.getByTestId("demo-status")).toContainText(/demo_/i);
  await expect(page.getByTestId("portfolio-card-grid")).toContainText(/Trend Momentum/i);
  await expect(page.getByTestId("strategy-bars")).toContainText(/Buy And Hold/i);
  await page.screenshot({
    path: testInfo.outputPath("demo-studio-final.png"),
    fullPage: true,
  });
});
