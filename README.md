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
- Ollama + FLUX Klein: optional local photorealistic look-development targets.
- Python standard library: deterministic scenario compiler, preflight, asset resolution, bundle export, look-dev orchestration, critique routing and visual-iteration state management.
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

The runtime supports deterministic execution-plan playback, GLB master loading/skinned cloning, `THREE.AnimationMixer`, dinosaur behavior state mapping, pack spacing, cinematic camera presets, rain/fog/lighting, fixed-step seeking, runtime snapshots and PNG capture.

The browser exposes:

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

## 4. Capture one preview frame per shot

```bash
cd web
npm run capture:preview
```

Frames are written under:

```text
build/preview/<scenario_id>/
```

## 5. Generate FLUX cinematic look-dev targets

The tested Ollama model tag is:

```bash
ollama run x/flux2-klein:4b "a cat holding a sign that says hello world"
```

Generate one target:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005
```

The current Ollama integration is text-to-image. It does **not** edit the Three.js preview. The preview remains authoritative for actor count, camera, blocking and continuity; FLUX is only a visual-quality reference for anatomy, materials, lighting, atmosphere and environment richness.

Outputs:

```text
build/lookdev/<scenario_id>/<shot_id>.png
build/lookdev/<scenario_id>/<shot_id>.prompt.txt
build/lookdev/<scenario_id>/<shot_id>.json
```

See `docs/FLUX_LOOKDEV.md`.

## 6. Build the visual-critic package

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005
```

This prepares the deterministic preview, FLUX quality target and critique package.

The visual critic writes:

```text
build/critique/raptor_hunt_001/shot_005.result.json
```

Then route it:

```bash
python3 pipeline/route_visual_critique.py \
  scenarios/raptor_hunt_001/scenario.json \
  build/critique/raptor_hunt_001/shot_005.result.json
```

Routing separates deterministic patches from reusable Astra/agent work:

```text
build/work/raptor_hunt_001/shot_005/
├── routing.json
├── deterministic_patches.json
├── work_requests.json
└── requests/*.md
```

See `docs/VISUAL_CRITIQUE_WORKFLOW.md` and `docs/CRITIQUE_ROUTING.md`.

## 7. Run repeatable visual-improvement iterations

Before Astra edits the next routed Blender asset:

```bash
python3 pipeline/run_visual_iteration.py \
  scenarios/raptor_hunt_001/scenario.json \
  start \
  --shot-id shot_005
```

After Astra edits the registered `.blend` and exports the registered GLB:

```bash
python3 pipeline/run_visual_iteration.py \
  scenarios/raptor_hunt_001/scenario.json \
  capture \
  --shot-id shot_005
```

This exports the runtime bundle, runs the web production build, recaptures previews and rebuilds the critique package while reusing the same FLUX visual target.

After the visual critic writes a **new** `shot_005.result.json`:

```bash
python3 pipeline/run_visual_iteration.py \
  scenarios/raptor_hunt_001/scenario.json \
  finalize \
  --shot-id shot_005
```

The state machine snapshots before/after evidence, records SHA-256 receipts for targeted registered Blender/GLB assets, reroutes remaining work and writes a deterministic decision:

```text
PASS
CONTINUE
BLOCKED
```

Iteration evidence is stored under:

```text
build/iterations/<scenario_id>/<shot_id>/iteration_###/
```

`PASS` requires critic `pass: true`, no high/blocking issues, no deterministic patches and no routed agent work. Lower weighted issue score means `improved`; higher means `regressed`.

See `docs/VISUAL_ITERATION_LOOP.md`.

## Blender asset workflow

See `docs/BLENDER_ASSET_CONTRACT.md` for scale, orientation, skeleton, animation naming and GLB conventions.

A repeatable Blender 5.2.1 export helper is included:

```bash
blender --background blender/dinosaurs/trex/trex_master.blend \
  --python blender/export_glb.py -- \
  --output web/public/assets/dinosaurs/trex_master.glb
```

After Blender exports an approved GLB, register it through the catalog CLI rather than hard-coding filenames in the scenario.

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
- `docs/CRITIQUE_ROUTING.md`
- `docs/VISUAL_ITERATION_LOOP.md`

## Astra bootstrap

After cloning this repository on the workstation with Blender 5.2.1, give Astra the complete instructions in:

`ASTRA_BOOTSTRAP_PROMPT.md`

Astra should focus on visual factory-building: improve reusable dinosaur/environment masters, rigs, textures and animations, execute routed work requests, export registered GLBs and use the deterministic iteration state machine to prove improvement in real captures.

## IP policy

The project may take genre/workflow inspiration from dinosaur simulation games, but repository assets must be original or properly licensed. Do not copy Jurassic World/JWE proprietary models, logos, audio, UI, or other protected game assets.
