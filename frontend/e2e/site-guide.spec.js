import { expect, test } from "@playwright/test";

test("shows the animated site guide and moves across routed steps", async ({ page }) => {
  await page.goto("/#/");

  await expect(page.getByTestId("site-guide-card")).toBeVisible();
  await expect(page.getByTestId("site-guide-card")).toContainText("Shell Navigation");
  await expect(page.getByTestId("site-guide-card")).toContainText("01 / 15");

  await page.getByTestId("site-guide-next").click();
  await expect(page.getByTestId("site-guide-card")).toContainText("API + Docs");

  await page.getByTestId("site-guide-next").click();
  await expect(page.getByTestId("site-guide-card")).toContainText("Demo Dashboard");

  await page.getByTestId("site-guide-next").click();
  await expect(page.getByTestId("site-guide-card")).toContainText("Demo Playback");

  await page.getByTestId("site-guide-next").click();
  await expect(page).toHaveURL(/#\/research-lab$/);
  await expect(page.getByTestId("site-guide-card")).toContainText("Research Lab Builder");
  await expect(page.locator('[data-guide="research-builder"]')).toBeVisible();

  await page.getByTestId("site-guide-skip").click();
  await expect(page.getByTestId("site-guide-card")).toHaveCount(0);

  await page.getByTestId("open-site-guide").click();
  await expect(page.getByTestId("site-guide-card")).toBeVisible();
  await expect(page.getByTestId("site-guide-card")).toContainText("Research Lab Builder");
});
