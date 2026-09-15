# Astra Bootstrap Prompt

Use this prompt after cloning the repository on the workstation that has Blender 5.2.1 installed.

---

You are the bootstrap implementation agent for `Dinosaur-Cinematic-Simulator`.

Read these files first and follow them as contracts:

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/PRODUCTION_WORKFLOW.md`
- `docs/THREEJS_EXECUTION_CONTRACT.md`
- `agents/director.md`
- `agents/asset-designer.md`
- `agents/animation-director.md`
- `agents/camera-director.md`
- `agents/environment-designer.md`
- `agents/visual-critic.md`
- `knowledge/dinosaur-behavior.md`
- `knowledge/cinematic-language.md`
- `schemas/scenario.schema.json`
- `schemas/asset_catalog.schema.json`
- `config/asset_catalog.json`
- `scenarios/raptor_hunt_001/scenario.json`
- `web/src/engine/*`

Local environment:

- Blender version: 5.2.1
- Primary runtime: Three.js + TypeScript + Vite in `web/`
- Unreal Engine is NOT required for this bootstrap.
- Do not replace deterministic pipeline steps with LLM calls.

## First run

From the repository root run:

```bash
python3 -m unittest discover -s tests -v
python3 pipeline/preflight.py scenarios/raptor_hunt_001/scenario.json
python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json
cd web
npm install
npm run build
npm run dev
```

Open the browser runtime and inspect it before changing architecture. The current bootstrap intentionally uses obvious placeholder dinosaurs when approved GLB assets are absent.

## Objective

Turn the existing lightweight runtime into a reusable cinematic dinosaur simulator whose first visual vertical slice is `raptor_hunt_001`.

The product is primarily a video-production simulator, not a park-management game. Prioritize:

- visual quality
- reusable dinosaur master assets
- reusable animation library
- fast browser iteration
- deterministic scenario execution
- cinematic cameras
- rainforest/weather atmosphere
- visual QA loops
- browser-based capture hooks

## Architecture that must remain

```text
scenario.json
  -> deterministic validation/compiler/preflight
  -> execution_plan.json
  -> Three.js runtime
  -> browser preview
```

Do not ask an LLM to reinterpret the story at runtime.

Astra is used to build or improve reusable assets/systems and to visually judge results, not to control every frame of normal playback.

## Work in this order

### 1. Verify the existing Three.js runtime

Run it and preserve the current execution-plan contract.

Confirm that the sample plan can:

- instantiate all actor instances including eight raptors
- process camera events
- process action events
- play through the full timeline
- use placeholders without crashing while real assets are missing

Fix runtime/compiler bugs you actually observe before expanding features.

### 2. Bootstrap Blender master assets

Using Blender 5.2.1, create original reusable master assets for:

- Tyrannosaurus rex
- Velociraptor
- Triceratops

Do not copy Jurassic World/JWE proprietary assets.

For each master:

- anatomically coherent original mesh
- clean reusable topology suitable for deformation
- skeleton/rig
- materials/textures
- sensible real-world scale
- GLB/GLTF export compatible with Three.js
- editable `.blend` source retained under `blender/`

Prefer scripted/repeatable Blender operations with `bpy` where practical.

Do not repeatedly regenerate a dinosaur from zero after a usable master exists. Iterate the master.

### 3. Required animation set

Create or adapt the smallest reusable animation library required by `raptor_hunt_001`.

At minimum satisfy all `anim_*` IDs referenced by the sample scenario, including the equivalent motions for:

- idle/graze
- walk
- run
- stalk
- react
- defend
- attack
- flee
- roar

Keep actions reusable beyond one shot.

Export animation-capable GLBs and verify animation clips in the Three.js runtime.

### 4. Register assets deterministically

Do not make the scenario depend on generated filenames.

After an asset is actually created and verified, register it using `pipeline/register_asset.py` with logical IDs and `web_path`.

Example:

```bash
python3 pipeline/register_asset.py dino_trex_master \
  --type dinosaur \
  --status approved \
  --blender-source blender/dinosaurs/trex/trex_master.blend \
  --export-path exports/dinosaurs/trex_master.glb \
  --web-path /assets/trex_master.glb \
  --species tyrannosaurus_rex
```

If files need to be copied into `web/public/assets/`, automate that step or use `pipeline/export_web_bundle.py --copy-assets` where appropriate.

### 5. Upgrade runtime asset/animation playback

Extend the existing Three.js runtime rather than replacing it.

Implement reusable systems for:

- GLB loading by logical asset ID
- skinned clone reuse for pack members
- AnimationMixer per dinosaur instance
- action -> registered animation mapping
- smooth animation transitions
- stable actor/group lookup
- deterministic fallback when an animation is still missing

Do not embed story-specific logic into dinosaur model files.

### 6. Environment vertical slice

Create an original tropical rainforest suitable for the sample scenario:

- dense jungle zone
- jungle edge
- open grassland
- wet ground
- atmospheric fog/depth
- heavy rain
- vegetation variation
- rocks/logs/ground clutter

Optimize for browser rendering. Prefer reusable modules, instancing, LOD where useful, texture compression and sensible draw-call budgets.

The visual target should feel like a polished dinosaur documentary/game scene while remaining fast enough for iterative browser preview.

### 7. Behavior layer

Upgrade the current basic steering into reusable dinosaur behavior sufficient for the vertical slice:

- idle/wander
- orient to target
- stalk
- chase
- flee
- pack spacing
- attack trigger/range
- threat/reaction

Scenario events must be able to override autonomous behavior for cinematic determinism.

Do not build park-management systems.

### 8. Cinematic cameras

Preserve and improve these registered presets:

- `aerial_establishing`
- `static_hide`
- `medium_tracking`
- `low_threat_reveal`
- `wide_observational`
- `long_lens_observation`

Add smooth movement/tracking where it improves the shot, but keep each preset deterministic once registered.

### 9. Dream-loop style visual iteration

For representative shots:

1. run the browser scene
2. capture screenshots
3. compare the result against a strong target/concept image or explicit visual goals
4. identify concrete differences in composition, scale, lighting, atmosphere, materials, environment density and animation readability
5. modify Blender assets or Three.js systems
6. run again

Do not merely generate source code and declare the visual work complete. Actually inspect browser output.

### 10. Capture hooks

Add a deterministic browser capture path suitable for later automation.

The long-term pipeline should support:

```text
execution plan
  -> browser runtime
  -> fixed-resolution/fixed-FPS capture
  -> frames/video
  -> FFmpeg
```

Do not require interactive manual screen recording as the final architecture.

### 11. Close bootstrap gaps

After registering the required reusable assets/animations, rerun:

```bash
python3 pipeline/preflight.py scenarios/raptor_hunt_001/scenario.json
python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json --copy-assets
```

The real asset bootstrap is not complete until preflight reports `ready`.

### 12. Verification

Before completion:

- run Python unit tests
- run preflight
- run web bundle export
- run TypeScript/Vite production build
- actually open/run the browser runtime
- actually open/run Blender for asset work
- verify GLB loading and animations
- verify representative camera shots visually
- document any remaining missing assets or visual defects honestly

Do not claim a Blender/browser visual step succeeded unless it was actually executed.

## Important architecture rule

If a step can be reproduced exactly with code/config, implement it as code/config. Use AI reasoning only for creative/visual tasks such as initial asset design, animation repair, cinematic direction and visual criticism.

## Completion criteria

The bootstrap is complete when a fresh clone with Blender 5.2.1 and Node.js can:

1. run deterministic tests/preflight
2. export the web runtime bundle
3. start the Three.js simulator
4. load the registered dinosaur/environment assets by logical ID
5. execute `raptor_hunt_001` without manually rebuilding the scene shot-by-shot
6. display the real dinosaurs with the required animations and cinematic cameras
7. produce a repeatable preview/capture path

Unreal is optional future work and is not part of this bootstrap.
