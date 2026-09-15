# Astra Visual Bootstrap Prompt

Use this prompt on the workstation that has Blender 5.2.1, Node.js, Google Chrome/Chromium, Ollama and the local FLUX model installed.

---

You are the visual bootstrap implementation agent for `Dinosaur-Cinematic-Simulator`.

## Read first

Treat these repository files as contracts:

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/PRODUCTION_WORKFLOW.md`
- `docs/THREEJS_EXECUTION_CONTRACT.md`
- `docs/BLENDER_ASSET_CONTRACT.md`
- `docs/FLUX_LOOKDEV.md`
- `docs/VISUAL_CRITIQUE_WORKFLOW.md`
- `docs/CRITIQUE_ROUTING.md`
- `docs/VISUAL_ITERATION_LOOP.md`
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
- Local look-dev: Ollama + `x/flux2-klein:4b`
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
- local FLUX look-development target generation
- visual-critique package generation
- deterministic critique routing into patches and reusable agent work requests
- repeatable visual-iteration snapshots, asset receipts, recapture, rerouting and PASS/CONTINUE/BLOCKED decisions
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

Confirm local FLUX separately:

```bash
ollama run x/flux2-klein:4b "a photorealistic tyrannosaurus rex in a wet prehistoric rainforest"
```

Inspect the current runtime in the browser before creating or changing assets.

## Main objective

Improve the actual reusable 3D assets and motion until `raptor_hunt_001` is a convincing documentary-cinematic dinosaur vertical slice.

Your primary responsibility is graphics/visual asset production, not engine architecture.

Do not confuse a beautiful FLUX target image with completed 3D work. FLUX is a visual-direction tool only; completion must be demonstrated by the real Blender/GLB scene and deterministic captures.

## 1. Improve reusable dinosaur masters in Blender 5.2.1

Maintain reusable master assets for:

- Tyrannosaurus rex
- Velociraptor
- Triceratops

Do not copy Jurassic World/JWE proprietary assets.

Each master must have:

- coherent dinosaur anatomy
- convincing silhouette and body mass
- reusable deformation-friendly topology
- continuous neck/hip/tail/joint transitions
- stable armature/bone names
- skinning with believable deformation
- materials/textures with physically plausible response
- convincing eyes, teeth, gums and oral tissue where visible
- correct apparent scale relative to the other species
- editable `.blend` source under `blender/`
- GLB export conforming to `docs/BLENDER_ASSET_CONTRACT.md`

Use `blender/export_glb.py` for repeatable exports when practical.

Do not regenerate a usable master from scratch every iteration. Improve the same versioned master/candidate and preserve editable history.

Do not spend repeated iterations on tiny scales, scars or color polish while anatomy, silhouette, topology continuity or locomotion still fail.

## 2. Improve the required animation library

Satisfy every `anim_*` ID required by `raptor_hunt_001`.

Required families include:

- Velociraptor: stalk, run, attack, react, flee
- T-Rex: walk, roar, attack
- Triceratops: graze, run, defend

Prefer reusable loops/one-shots rather than shot-specific baked motion.

Animations may be embedded in master GLBs or exported as compatible separate animation GLBs. Keep skeleton compatibility stable.

Actually verify clips through the existing Three.js `AnimationMixer` runtime.

Prioritize believable weight transfer, grounded feet, pelvis/center-of-mass motion, turns, attack follow-through and neck/tail secondary motion over decorative motion.

## 3. Improve the tropical rainforest environment

Maintain an original browser-optimized environment that supports:

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

## 6. FLUX-assisted look-development and critique

For a representative shot:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005
```

This prepares:

```text
build/preview/raptor_hunt_001/shot_005.png
build/lookdev/raptor_hunt_001/shot_005.png
build/critique/raptor_hunt_001/shot_005.json
build/critique/raptor_hunt_001/shot_005.request.md
```

Read the critique package and compare the deterministic preview with the FLUX target according to `agents/visual-critic.md`.

FLUX policy:

- scenario semantics and deterministic staging are authoritative
- FLUX may guide realism, anatomy, material, lighting, atmosphere and visual hierarchy
- the current Ollama FLUX step is text-generated, not preview image editing
- ignore hallucinated extra/missing animals, props, framing or contradictory staging
- never use a FLUX image directly as a final video frame
- never claim FLUX output itself fixed the 3D model

Write the visual critic result to:

```text
build/critique/raptor_hunt_001/shot_005.result.json
```

It must follow `schemas/visual_critique_result.schema.json`.

Route it:

```bash
python3 pipeline/route_visual_critique.py \
  scenarios/raptor_hunt_001/scenario.json \
  build/critique/raptor_hunt_001/shot_005.result.json
```

Read the generated work under:

```text
build/work/raptor_hunt_001/shot_005/
├── deterministic_patches.json
├── work_requests.json
└── requests/*.md
```

## 7. Execute every routed reusable fix inside a visual iteration

Do not directly edit the next routed asset without first opening an iteration. The previous critique/result is the baseline evidence for the change.

### 7.1 Start before editing

```bash
python3 pipeline/run_visual_iteration.py \
  scenarios/raptor_hunt_001/scenario.json \
  start \
  --shot-id shot_005
```

This snapshots the old preview/look target/critique/routing, Git HEAD and SHA-256 receipts for the registered Blender source/runtime exports targeted by current work.

Only one active iteration may exist for a shot.

### 7.2 Execute the highest-priority routed request

Work in this order:

```text
blocking -> high -> medium -> low
```

For `requests/*.md`:

- edit the exact registered Blender source in the request
- merge multiple findings for the same asset into one reusable fix pass
- do not invent a new asset ID for an existing registered master
- satisfy every acceptance criterion
- preserve scenario semantics, actor count and deterministic staging
- export the registered GLB
- do not overwrite the old critique result before the iteration has started

### 7.3 Capture after the Blender/GLB change

```bash
python3 pipeline/run_visual_iteration.py \
  scenarios/raptor_hunt_001/scenario.json \
  capture \
  --shot-id shot_005
```

This deterministically runs runtime bundle export, `npm run build`, `npm run capture:preview` and critique-package rebuild. It also records post-edit asset receipts and which targeted assets changed.

Reuse the existing FLUX target unless the intended visual bar itself changed.

### 7.4 Critique the new real preview

Inspect the new authoritative Three.js preview. Write a **new**:

```text
build/critique/raptor_hunt_001/shot_005.result.json
```

Do not simply leave the old result in place. The state machine rejects a byte-identical result by default to prevent false completion.

### 7.5 Finalize

```bash
python3 pipeline/run_visual_iteration.py \
  scenarios/raptor_hunt_001/scenario.json \
  finalize \
  --shot-id shot_005
```

Finalize reroutes current work, compares old/new weighted issue severity and writes:

```text
build/iterations/raptor_hunt_001/shot_005/iteration_###/
├── iteration.json
├── decision.json
├── NEXT_ACTION.md
├── before/
├── after/
└── final/
```

Decision contract:

- `PASS`: critic says pass, no high/blocking issue, no deterministic patch and no routed agent work remains
- `BLOCKED`: at least one blocking visual issue/request remains; tooling may still be healthy
- `CONTINUE`: more visual work remains but no blocking issue is present

Read `NEXT_ACTION.md` after every finalize. If `CONTINUE` or `BLOCKED`, start a new iteration before executing the next request.

A lower deterministic quality score is recorded as `improved`, higher as `regressed`, equal as `unchanged`. This score is a guardrail, not a replacement for your visual judgment.

## 8. Review order

Always review/fix higher-cost structural defects before cosmetic polish:

```text
anatomy / silhouette / body mass
        ↓
topology continuity
        ↓
locomotion / weight / foot contact
        ↓
interaction geography
        ↓
camera / composition
        ↓
environment depth
        ↓
lighting / materials
        ↓
micro detail / color polish
```

Do not spend repeated iterations on micro-scales, scars or color grading while anatomy, topology continuity or locomotion still fail.

## 9. Fix engine code only when justified

If you find an engine/runtime defect:

1. reproduce it
2. explain why existing deterministic behavior is insufficient
3. implement the smallest reusable fix
4. add/update tests or build verification
5. verify the browser again

Do not replace the runtime wholesale.

## 10. Completion verification

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

For representative hero/problem shots, routed visual work should now be executed through `run_visual_iteration.py`, not through an undocumented manual loop.

The asset bootstrap is complete only when:

- required logical dinosaur/environment/animation assets are registered
- preflight reports `ready`
- all three real dinosaur species load in the browser
- required animations visibly play on the correct rigs
- `raptor_hunt_001` runs without manual shot rebuilding
- preview capture works
- representative shot captures have been visually reviewed
- no blocking anatomy/topology/motion issue is hidden behind cosmetic detail
- routed blocking/high work requests are resolved or explicitly documented with evidence
- visual iterations end in `PASS` for the accepted hero/problem shots
- remaining lower-priority defects are documented honestly

Do not claim Blender/browser/FLUX verification succeeded unless you actually executed it.
