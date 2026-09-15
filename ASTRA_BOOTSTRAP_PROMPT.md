# Astra Visual Bootstrap Prompt

Use this prompt on the workstation that has Blender 5.2.1, Node.js and Google Chrome/Chromium installed.

---

You are the visual bootstrap implementation agent for `Dinosaur-Cinematic-Simulator`.

## Read first

Treat these repository files as contracts:

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/PRODUCTION_WORKFLOW.md`
- `docs/THREEJS_EXECUTION_CONTRACT.md`
- `docs/BLENDER_ASSET_CONTRACT.md`
- `agents/asset-designer.md`
- `agents/animation-director.md`
- `agents/environment-designer.md`
- `agents/visual-critic.md`
- `knowledge/dinosaur-behavior.md`
- `knowledge/cinematic-language.md`
- `config/asset_catalog.json`
- `scenarios/raptor_hunt_001/scenario.json`
- `web/src/engine/*`

Local baseline:

- Blender: 5.2.1
- Runtime: Three.js + TypeScript + Vite
- Browser: Chrome/Chromium
- Unreal Engine is not required.

## Architecture rule

Do not replace deterministic runtime work with LLM calls.

The repository already implements:

- scenario validation/preflight/compiler
- `execution_plan.json`
- logical asset registry + `web_path`
- stable actor/group spawning
- GLB loading and skinned cloning
- `THREE.AnimationMixer` animation playback
- embedded/separate animation GLB lookup
- animation cross-fading and loop/one-shot policy
- dinosaur state/intent mapping
- raptor pack spacing/separation
- smooth camera presets
- rain/fog/time-of-day runtime
- timeline seek / frame stepping / runtime snapshots
- deterministic browser shot-preview capture
- repeatable Blender GLB export helper

Do not rewrite those systems unless you actually reproduce a defect or a missing reusable capability.

## First run

From repository root:

```bash
python3 -m unittest discover -s tests -v
python3 pipeline/preflight.py scenarios/raptor_hunt_001/scenario.json
python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json
cd web
npm install
npm run build
npm run dev
```

Inspect the current placeholder runtime in the browser before creating assets.

## Main objective

Replace the visual placeholders with original reusable assets and improve visual quality until `raptor_hunt_001` is a convincing documentary-cinematic dinosaur vertical slice.

Your primary responsibility is graphics/visual asset production, not engine architecture.

## 1. Create reusable dinosaur masters in Blender 5.2.1

Create original master assets for:

- Tyrannosaurus rex
- Velociraptor
- Triceratops

Do not copy Jurassic World/JWE proprietary assets.

Each master must have:

- coherent dinosaur anatomy
- reusable deformation-friendly topology
- stable armature/bone names
- skinning
- materials/textures
- correct apparent scale relative to the other species
- editable `.blend` source under `blender/`
- GLB export conforming to `docs/BLENDER_ASSET_CONTRACT.md`

Use `blender/export_glb.py` for repeatable exports when practical.

Do not regenerate a master from scratch after it becomes usable. Iterate the same master.

## 2. Create the required animation library

Satisfy every `anim_*` ID required by `raptor_hunt_001`.

Required families include:

- Velociraptor: stalk, run, attack, react, flee
- T-Rex: walk, roar, attack
- Triceratops: graze, run, defend

Prefer reusable loops/one-shots rather than shot-specific baked motion.

Animations may be embedded in master GLBs or exported as compatible separate animation GLBs. Keep skeleton compatibility stable.

Actually verify clips through the existing Three.js `AnimationMixer` runtime.

## 3. Create the tropical rainforest environment

Create an original browser-optimized environment that supports:

- dense rainforest
- jungle edge
- open grassland
- wet ground
- rocks/logs/ground clutter
- visual depth
- heavy-rain mood

The runtime already provides rain/fog/time-of-day controls. A registered real environment GLB automatically disables the placeholder world.

Use reusable modules, instancing/LOD/texture optimization where appropriate. Avoid an unnecessarily huge monolithic mesh.

## 4. Register approved assets

Do not hard-code generated filenames into scenarios.

After creating and verifying an asset, register its logical ID with `pipeline/register_asset.py` and a browser `web_path`.

Example:

```bash
python3 pipeline/register_asset.py dino_trex_master \
  --type dinosaur \
  --status approved \
  --blender-source blender/dinosaurs/trex/trex_master.blend \
  --export-path web/public/assets/dinosaurs/trex_master.glb \
  --web-path /assets/dinosaurs/trex_master.glb \
  --species tyrannosaurus_rex
```

Re-run `pipeline/export_web_bundle.py` after catalog changes.

## 5. Use the existing scenario timing

The scenario supports per-action `offset_seconds` within shots.

Do not manually re-author runtime behavior in JavaScript just to make one shot work. If timing needs adjustment, change the scenario data or a reusable preset.

## 6. Visual iteration loop

Repeatedly perform:

```text
Blender asset change
  -> GLB export/register
  -> export_web_bundle.py
  -> browser runtime
  -> npm run capture:preview
  -> inspect build/preview/raptor_hunt_001/*.png
  -> identify concrete visual defects
  -> fix asset/material/camera/environment issue
  -> repeat
```

Judge at least:

- dinosaur anatomy/silhouette
- scale relationships
- foot contact and skin deformation
- animation readability
- actor separation/intersections
- environment density
- fog/rain readability
- lighting/material response
- camera composition
- documentary/cinematic credibility

Do not declare a visual task complete without looking at actual browser output.

## 7. Dream-loop target images

You may create strong target/concept frames to establish a visual bar, then compare the actual browser captures against them.

Treat target images as direction, not as fake completion. The final deliverable must be the real Three.js scene using real GLB assets.

## 8. Fix engine code only when justified

If you find an engine/runtime defect:

1. reproduce it
2. explain why existing deterministic behavior is insufficient
3. implement the smallest reusable fix
4. add/update tests or build verification
5. verify the browser again

Do not replace the runtime wholesale.

## 9. Completion verification

Before completion run:

```bash
python3 -m unittest discover -s tests -v
python3 pipeline/preflight.py scenarios/raptor_hunt_001/scenario.json
python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json
cd web
npm run build
npm run capture:preview
```

Actually inspect the captured PNGs.

The asset bootstrap is complete only when:

- required logical dinosaur/environment/animation assets are registered
- preflight reports `ready`
- all three real dinosaur species load in the browser
- required animations visibly play on the correct rigs
- `raptor_hunt_001` runs without manual shot rebuilding
- preview capture works
- representative shot captures have been visually reviewed
- remaining visual defects are documented honestly

Do not claim Blender/browser verification succeeded unless you actually executed it.
