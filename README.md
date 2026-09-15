# Dinosaur Cinematic Simulator

AI-assisted dinosaur cinematic simulation and video-production pipeline built around Three.js, Blender, deterministic scenario specifications, and specialized AI agents.

The project is designed primarily as a cinematic/video factory rather than a park-management game.

## Architecture principle

**Deterministic when possible; AI only when necessary.**

Normal production should not ask an LLM to spawn actors, apply known weather, play known animations, choose registered assets, apply known camera presets, or run playback. AI is reserved for story/shot design, genuinely missing reusable assets or animations, and visual criticism/repair.

See `AGENTS.md` for repository-wide agent rules.

## Primary stack

- Three.js + TypeScript + Vite: primary realtime runtime and fast preview engine.
- Blender 5.2.1: reusable dinosaur/environment master assets exported as GLB/GLTF.
- Python standard library: deterministic scenario compiler, preflight, asset resolution and bundle export.
- System Chrome/Chromium + `playwright-core`: deterministic shot-preview capture.
- `agents/*.md`: specialized AI role contracts.
- `knowledge/*.md`: reusable dinosaur/cinematic knowledge.
- `schemas/*.json`: machine contracts.
- `scenarios/*`: executable cinematic specifications.

Unreal Engine is optional future infrastructure, not a requirement for normal development.

## First vertical slice

`scenarios/raptor_hunt_001/scenario.json`

A pack of eight Velociraptors hunts a Triceratops through a rainforest into open grassland. A T-Rex enters and attacks the pack. Target duration: 3 minutes, documentary cinematic style.

## 1. Deterministic preflight

From the repository root:

```bash
python3 pipeline/preflight.py scenarios/raptor_hunt_001/scenario.json
```

This validates the scenario, expands actor groups into stable instance IDs, compiles the execution plan, and resolves required logical assets.

During bootstrap the asset catalog is intentionally incomplete, so `missing_assets` is expected until real master assets are registered.

## 2. Export the web runtime bundle

```bash
python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json
```

This writes:

```text
web/public/runtime/execution_plan.json
web/public/runtime/asset_manifest.json
```

## 3. Run the simulator

```bash
cd web
npm install
npm run dev
```

Open the Vite URL in a browser.

The runtime now supports:

- deterministic execution-plan playback
- stable actor/group instance IDs
- GLB master loading with skinned cloning
- `THREE.AnimationMixer` playback from embedded or separate animation GLBs
- cross-fading and one-shot/loop animation policy
- dinosaur behavior states such as idle/stalk/chase/flee/attack/defend/react/roar
- deterministic raptor-pack surround spacing and local separation
- smooth tracking/aerial/telephoto/threat-reveal camera transitions
- rain, fog, lighting and time-of-day presets
- placeholder world/dinosaurs when real GLBs are missing
- automatic removal of the placeholder world when an approved environment GLB exists
- Play/Pause/Restart/frame-step/timeline seek controls
- fixed-step deterministic seek at scenario FPS
- machine-readable runtime snapshots
- canvas PNG capture API

The browser exposes the running instance as:

```js
window.dinosaurRuntime
```

Useful methods include:

```js
window.dinosaurRuntime.pause()
window.dinosaurRuntime.seek(42.5)
window.dinosaurRuntime.stepFrame()
window.dinosaurRuntime.renderFrameAt(90)
window.dinosaurRuntime.snapshot()
window.dinosaurRuntime.captureDataUrl()
```

This browser API is intended for headless capture and visual-critic automation.

## 4. Capture one preview frame per shot

With Google Chrome/Chromium installed:

```bash
cd web
npm run capture:preview
```

The capture script starts Vite, opens the simulator headlessly, seeks deterministically to the midpoint of every camera shot, and writes PNGs under:

```text
build/preview/<scenario_id>/
```

If Chrome is installed in a non-standard location, set `CHROME_BIN` to the executable path.

## Blender asset workflow

See `docs/BLENDER_ASSET_CONTRACT.md` for scale, orientation, skeleton, animation naming and GLB conventions.

A repeatable Blender 5.2.1 export helper is included:

```bash
blender --background blender/dinosaurs/trex/trex_master.blend \
  --python blender/export_glb.py -- \
  --output web/public/assets/dinosaurs/trex_master.glb
```

After Blender exports an approved GLB, register it through the catalog CLI rather than hard-coding filenames in the scenario:

```bash
python3 pipeline/register_asset.py dino_trex_master \
  --type dinosaur \
  --blender-source blender/dinosaurs/trex/trex_master.blend \
  --export-path web/public/assets/dinosaurs/trex_master.glb \
  --web-path /assets/dinosaurs/trex_master.glb \
  --species tyrannosaurus_rex
```

Then export the web bundle again.

## AI work requests

When preflight reports missing assets:

```bash
python3 pipeline/build_agent_requests.py \
  build/preflight/raptor_hunt_001/preflight.json \
  --output build/preflight/raptor_hunt_001/agent_requests.json
```

The missing work is routed to specialized agents instead of sending every production run through Astra.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions validates the deterministic Python layer and performs a strict TypeScript + Vite production build.

## Runtime contract

See:

- `docs/THREEJS_EXECUTION_CONTRACT.md`
- `docs/PRODUCTION_WORKFLOW.md`
- `docs/ARCHITECTURE.md`
- `docs/BLENDER_ASSET_CONTRACT.md`

## Astra bootstrap

After cloning this repository on the workstation with Blender 5.2.1, give Astra the complete instructions in:

`ASTRA_BOOTSTRAP_PROMPT.md`

Astra should now focus primarily on visual factory-building: create and refine reusable dinosaur/environment masters, rigs, textures and missing animations, export/register GLBs, run the existing browser runtime, inspect captured shot previews and iterate visual quality. The deterministic engine/runtime should be extended only when an actual reusable capability is missing.

## IP policy

The project may take genre/workflow inspiration from dinosaur simulation games, but repository assets must be original or properly licensed. Do not copy Jurassic World/JWE proprietary models, logos, audio, UI, or other protected game assets.
