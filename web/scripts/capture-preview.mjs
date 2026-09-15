import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const HERE = dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = resolve(HERE, "..");
const REPO_ROOT = resolve(WEB_ROOT, "..");
const PLAN_PATH = resolve(WEB_ROOT, "public/runtime/execution_plan.json");
const PORT = Number(process.env.DINO_PREVIEW_PORT ?? 5173);
const BASE_URL = `http://127.0.0.1:${PORT}`;

function chromeExecutable() {
  const candidates = [
    process.env.CHROME_BIN,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
  ].filter(Boolean);
  return candidates.find((path) => existsSync(path));
}

async function waitForServer(url, timeoutMs = 15000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Vite is still starting.
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 150));
  }
  throw new Error(`Vite did not become ready at ${url}`);
}

const plan = JSON.parse(readFileSync(PLAN_PATH, "utf8"));
const shots = plan.events.filter((event) => event.type === "camera");
const outputDir = resolve(REPO_ROOT, "build", "preview", plan.scenario_id);
mkdirSync(outputDir, { recursive: true });

const executablePath = chromeExecutable();
if (!executablePath) {
  throw new Error("Google Chrome/Chromium not found. Set CHROME_BIN to the browser executable.");
}

const vite = spawn(
  process.platform === "win32" ? "npm.cmd" : "npm",
  ["run", "dev", "--", "--host", "127.0.0.1", "--port", String(PORT)],
  { cwd: WEB_ROOT, stdio: ["ignore", "pipe", "pipe"] },
);

let browser;
try {
  await waitForServer(BASE_URL);
  browser = await chromium.launch({ executablePath, headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  await page.goto(BASE_URL, { waitUntil: "networkidle" });
  await page.waitForFunction(() => Boolean(window.dinosaurRuntime));

  for (const shot of shots) {
    const captureTime = shot.time + Math.max(0, shot.end_time - shot.time) * 0.5;
    await page.evaluate((time) => window.dinosaurRuntime.renderFrameAt(time), captureTime);
    await page.locator("#viewport").screenshot({ path: resolve(outputDir, `${shot.shot_id}.png`) });
    process.stdout.write(`CAPTURED ${shot.shot_id} @ ${captureTime.toFixed(3)}s\n`);
  }

  process.stdout.write(`WROTE ${shots.length} preview frames to ${outputDir}\n`);
} finally {
  await browser?.close();
  vite.kill("SIGTERM");
}
