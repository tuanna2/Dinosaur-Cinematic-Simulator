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

The current bootstrap runtime can already:

- load the compiled execution plan
- spawn stable actor instances
- expand the eight-member raptor pack
- apply deterministic camera presets
- execute simple chase/flee/stalk/attack steering
- run the 3-minute timeline
- use clear placeholder dinosaurs when approved GLB assets are not available
- replace placeholders automatically when logical asset IDs receive valid `web_path` entries

Placeholders are development-only; preflight still reports missing real assets.

## Asset registration

After Blender exports an approved GLB, register it through the catalog CLI rather than hard-coding filenames in the scenario:

```bash
python3 pipeline/register_asset.py dino_trex_master \
  --type dinosaur \
  --blender-source blender/dinosaurs/trex_master.blend \
  --export-path exports/dinosaurs/trex_master.glb \
  --web-path /assets/trex_master.glb \
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

GitHub Actions validates the deterministic Python layer and builds the web runtime.

## Runtime contract

See:

- `docs/THREEJS_EXECUTION_CONTRACT.md`
- `docs/PRODUCTION_WORKFLOW.md`
- `docs/ARCHITECTURE.md`

## Astra bootstrap

After cloning this branch on the workstation with Blender 5.2.1, give Astra the complete instructions in:

`ASTRA_BOOTSTRAP_PROMPT.md`

Astra is expected to improve the existing Three.js factory rather than replace it: create reusable dinosaur/environment masters, rig/animate/export GLBs, wire animation playback, improve rainforest/weather/lighting, and visually iterate the first vertical slice.

## IP policy

The project may take genre/workflow inspiration from dinosaur simulation games, but repository assets must be original or properly licensed. Do not copy Jurassic World/JWE proprietary models, logos, audio, UI, or other protected game assets.
