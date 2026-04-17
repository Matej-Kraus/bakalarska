import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const outDir = path.resolve(__dirname, "../docs/screenshots");
fs.mkdirSync(outDir, { recursive: true });

async function shot(page, name) {
  await page.waitForTimeout(1200);
  await page.screenshot({
    path: path.join(outDir, `${name}.png`),
    fullPage: true,
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto("http://127.0.0.1:5173/login", { waitUntil: "networkidle" });
  await page.fill('input[type="password"]', "coach");
  await page.click("button:has-text('Přihlásit')");
  await page.waitForURL("**/players", { timeout: 15000 });
  await shot(page, "players");

  await page.goto("http://127.0.0.1:5173/matches", { waitUntil: "networkidle" });
  await shot(page, "matches");

  await page.goto("http://127.0.0.1:5173/matches/2/lineup", { waitUntil: "networkidle" });
  await shot(page, "lineup");

  await page.goto("http://127.0.0.1:5173/matches/2/live", { waitUntil: "networkidle" });
  await shot(page, "live_match");

  await page.goto("http://127.0.0.1:5173/matches/2/evaluation", { waitUntil: "networkidle" });
  await shot(page, "evaluation");

  await page.goto("http://127.0.0.1:5173/analytics", { waitUntil: "networkidle" });
  await shot(page, "analytics");

  await browser.close();
  console.log("Screenshots saved to:", outDir);
})();

