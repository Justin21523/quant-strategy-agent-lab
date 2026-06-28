import { expect, test } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "../..");
const MEDIA_DIR = path.resolve(ROOT, "docs/showcase-media");
const SCREENSHOT_DIR = path.join(MEDIA_DIR, "screenshots");
const VIDEO_DIR = path.join(MEDIA_DIR, "videos");
const BASE_PATH = "/quant-strategy-agent-lab/";

async function ensureMediaDirs() {
  await fs.mkdir(SCREENSHOT_DIR, { recursive: true });
  await fs.mkdir(path.join(VIDEO_DIR, "posters"), { recursive: true });
}

async function gotoApp(page, route = "/") {
  await page.goto(`${BASE_PATH}#${route}`);
  await expect(page.locator("[data-router-outlet]")).toBeVisible();
  await page.waitForLoadState("networkidle");
}

async function dismissAutoGuide(context) {
  await context.addInitScript(() => {
    sessionStorage.setItem("qsa_site_guide_dismissed", "true");
  });
}

async function screenshot(page, filename, route, { fullPage = true } = {}) {
  await gotoApp(page, route);
  await page.addStyleTag({ content: ".status-bar{display:none!important}" });
  await page.waitForTimeout(700);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, filename), fullPage });
}

test("captures portfolio showcase screenshots and site-guide demo video", async ({ browser }) => {
  await ensureMediaDirs();

  const screenshotContext = await browser.newContext({
    viewport: { width: 1440, height: 1050 },
    deviceScaleFactor: 1,
  });
  await dismissAutoGuide(screenshotContext);
  const page = await screenshotContext.newPage();

  await screenshot(page, "01-overview.png", "/");
  await screenshot(page, "03-research-lab.png", "/research-lab");
  await screenshot(page, "04-report-center.png", "/report-center");
  await screenshot(page, "05-market-data.png", "/market-data");
  await screenshot(page, "06-scanner.png", "/parameter-scanner");
  await screenshot(page, "07-portfolio.png", "/portfolio-rebalance");
  await screenshot(page, "08-performance.png", "/performance-report");
  await screenshot(page, "09-jobs.png", "/jobs");

  await page.goto(`${BASE_PATH}#/research-lab`);
  await page.getByTestId("run-research-pipeline").click();
  await expect(page.getByTestId("research-status")).toContainText(/completed|job_static/i, {
    timeout: 15_000,
  });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, "10-research-pipeline-run.png"),
    fullPage: true,
  });
  await screenshotContext.close();

  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    deviceScaleFactor: 2,
  });
  await dismissAutoGuide(mobileContext);
  const mobile = await mobileContext.newPage();
  await screenshot(mobile, "11-mobile-dashboard.png", "/");
  await mobileContext.close();

  const guideContext = await browser.newContext({
    viewport: { width: 1440, height: 1050 },
    recordVideo: {
      dir: VIDEO_DIR,
      size: { width: 1440, height: 1050 },
    },
  });
  const guide = await guideContext.newPage();
  await gotoApp(guide, "/");
  await guide.addStyleTag({ content: ".status-bar{display:none!important}" });
  await expect(guide.getByTestId("site-guide-card")).toContainText("Shell Navigation");
  await guide.screenshot({ path: path.join(SCREENSHOT_DIR, "02-site-guide.png"), fullPage: true });

  for (let index = 0; index < 8; index += 1) {
    await guide.getByTestId("site-guide-next").click();
    await guide.waitForTimeout(850);
  }
  await guide.getByTestId("open-site-guide").click();
  await guide.waitForTimeout(900);
  await guide.getByTestId("site-guide-next").click();
  await guide.waitForTimeout(900);
  await guide.screenshot({
    path: path.join(VIDEO_DIR, "posters/playwright-external-live-demo.png"),
    fullPage: true,
  });

  const video = guide.video();
  await guideContext.close();
  const videoPath = await video.path();
  await fs.copyFile(videoPath, path.join(VIDEO_DIR, "playwright-external-live-demo.webm"));
  await fs.rm(videoPath, { force: true });
});
