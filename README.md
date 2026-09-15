# Dinosaur Cinematic Simulator

AI-assisted dinosaur cinematic simulation and video-production pipeline built around Three.js, Blender, deterministic scenario specifications, and specialized AI agents.

The project is designed primarily as a cinematic/video factory rather than a park-management game.

## Architecture principle

**Deterministic when possible; AI only when necessary.**

Normal production should not ask an LLM to spawn actors, apply known weather, play known animations, choose registered assets, apply known camera presets, or run playback. AI is reserved for story/shot design, genuinely missing reusable assets or animations, visual look-development, and visual criticism/repair.

See `AGENTS.md` for repository-wide agent rules.

## Primary stack

- Three.js + TypeScript + Vite: primary realtime runtime and fast preview engine.
- Blender 5.2.1: reusable dinosaur/environment master assets exported as GLB/GLTF and future final cinematic rendering.
- Ollama + FLUX Klein: optional local photorealistic look-development targets from deterministic shot previews.
- Python standard library: deterministic scenario compiler, preflight, asset resolution, bundle export, look-dev orchestration and visual-critique packaging.
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

## 5. Generate FLUX cinematic look-dev targets

If your local Ollama setup already supports:

```bash
ollama run x/flux-klein:4b "a cat holding a sign that says hello world"
```

then generate a target for one scenario shot with:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005
```

The CLI uses the captured Three.js frame as a reference when available and writes the generated target, prompt and metadata under:

```text
build/lookdev/<scenario_id>/
```

Generate all shots by omitting `--shot-id`.

See `docs/FLUX_LOOKDEV.md` for provider details and reference-image caveats.

## 6. Build a visual-critic package

The preferred workflow is now one command:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005
```

It runs the deterministic export/capture, generates the local FLUX target and packages the comparison for Astra/visual critic.

Outputs include:

```text
build/preview/raptor_hunt_001/shot_005.png
build/lookdev/raptor_hunt_001/shot_005.png
build/lookdev/raptor_hunt_001/shot_005.prompt.txt
build/lookdev/raptor_hunt_001/shot_005.json
build/critique/raptor_hunt_001/shot_005.json
build/critique/raptor_hunt_001/shot_005.request.md
```

The critique package explicitly keeps scenario semantics and deterministic Three.js staging as source-of-truth. FLUX is only a realism/look target. Structural mesh/material/rig/animation defects are routed to reusable Blender asset work; camera, placement, lighting and preset defects can remain deterministic patches.

To regenerate only critique packaging from existing files:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --skip-export \
  --skip-capture \
  --skip-lookdev
```

See `docs/VISUAL_CRITIQUE_WORKFLOW.md` and `agents/visual-critic.md`.

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
- `docs/FLUX_LOOKDEV.md`
- `docs/VISUAL_CRITIQUE_WORKFLOW.md`

## Astra bootstrap

After cloning this repository on the workstation with Blender 5.2.1, give Astra the complete instructions in:

`ASTRA_BOOTSTRAP_PROMPT.md`

Astra should focus on visual factory-building: create/refine reusable dinosaur/environment masters, rigs, textures and missing animations, export/register GLBs, run the deterministic browser runtime, generate FLUX look-dev targets, consume critique packages and iterate actual 3D quality. The deterministic engine/runtime should be extended only when an actual reusable capability is missing.

## IP policy

The project may take genre/workflow inspiration from dinosaur simulation games, but repository assets must be original or properly licensed. Do not copy Jurassic World/JWE proprietary models, logos, audio, UI, or other protected game assets.
