import "./style.css";
import { AssetRegistry } from "./engine/AssetRegistry";
import { CinematicRuntime } from "./engine/CinematicRuntime";
import type { AssetManifest, ExecutionPlan } from "./types";

function requireElement<T extends Element>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`missing required DOM element: ${selector}`);
  return element;
}

const canvas = requireElement<HTMLCanvasElement>("#viewport");
const status = requireElement<HTMLSpanElement>("#status");
const timeLabel = requireElement<HTMLSpanElement>("#time");
const playButton = requireElement<HTMLButtonElement>("#play");
const restartButton = requireElement<HTMLButtonElement>("#restart");

function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds - minutes * 60;
  return `${String(minutes).padStart(2, "0")}:${rest.toFixed(1).padStart(4, "0")}`;
}

async function loadJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

async function bootstrap(): Promise<void> {
  try {
    const [plan, manifest] = await Promise.all([
      loadJson<ExecutionPlan>("/runtime/execution_plan.json"),
      loadJson<AssetManifest>("/runtime/asset_manifest.json"),
    ]);

    const assets = new AssetRegistry(manifest);
    const runtime = new CinematicRuntime(canvas, plan, assets, (seconds) => {
      timeLabel.textContent = formatTime(seconds);
    });

    await runtime.initialize();
    status.textContent = `${plan.scenario_id} · ${plan.instances.length} actors · ${plan.duration_seconds}s`;
    playButton.addEventListener("click", () => runtime.play());
    restartButton.addEventListener("click", () => runtime.restart());
    runtime.play();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    status.textContent = `Runtime bundle missing: ${message}. Run pipeline/export_web_bundle.py first.`;
    playButton.disabled = true;
    restartButton.disabled = true;
  }
}

void bootstrap();
