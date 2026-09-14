# Astra Bootstrap Prompt

Use this prompt after cloning the repository on the workstation that has Blender 5.2.1 and Unreal Engine installed.

---

You are the bootstrap implementation agent for `Dinosaur-Cinematic-Simulator`.

Read these files first and follow them as contracts:

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/PRODUCTION_WORKFLOW.md`
- `docs/UNREAL_EXECUTION_CONTRACT.md`
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

Local environment:

- Blender version: 5.2.1
- Unreal Engine: detect the installed UE5 version and use it; document the exact version in the repo.
- Do not replace deterministic pipeline steps with LLM calls.

## Before changing Unreal or Blender

From the repository root run:

```bash
python3 -m unittest discover -s tests -v
python3 pipeline/preflight.py scenarios/raptor_hunt_001/scenario.json
```

The initial preflight is expected to report `missing_assets` because the master asset library has not been bootstrapped yet.

The Unreal runtime must consume the compiled `execution_plan.json` contract instead of asking an LLM to reinterpret story prose or scenario JSON at runtime.

## Objective

Bootstrap a reusable cinematic dinosaur simulator whose first executable vertical slice is `raptor_hunt_001`.

The simulator is primarily a video-production engine, not a park-management game. Prioritize cinematic quality, reusable dinosaur assets, behavior, camera control, Sequencer automation and Movie Render Queue.

## Work in this order

### 1. Detect and document Unreal

Detect the actual installed Unreal Engine 5 version before creating version-sensitive source files. Record the exact version and platform in the repository setup documentation.

### 2. Unreal project

Create the Unreal project under `unreal/DinosaurCinematicSimulator/`.

Enable/configure the minimum required UE plugins/features for:

- Sequencer
- Movie Render Queue / Movie Render Pipeline
- Control Rig
- PCG
- Navigation
- Python Editor Script Plugin if useful for deterministic editor automation

Do not enable unrelated plugins.

### 3. Director runtime/API

Implement `docs/UNREAL_EXECUTION_CONTRACT.md`.

The production path is:

```text
scenario.json
  -> pipeline/preflight.py
  -> execution_plan.json
  -> Unreal deterministic executor
```

Unreal must support at least:

- consume compiled execution plans
- load environment by logical asset ID
- spawn all compiled actor instances by logical asset ID
- stable actor lookup by `instance_id`
- set registered weather/time presets
- apply registered camera presets
- execute registered action mappings
- play named animation assets
- build or populate a Level Sequence
- render predictable low-resolution previews
- invoke Movie Render Queue for final render
- return machine-readable errors for unresolved/unsupported operations

Prefer C++ for stable runtime/core types and Python/Editor scripting for editor automation where it simplifies Sequencer/MRQ generation. Blueprints may be used for content-facing configuration, but do not make the entire pipeline manual Blueprint wiring.

### 4. Asset registry bridge

Implement deterministic lookup from logical IDs in `config/asset_catalog.json` to Unreal/Blender paths.

Logical IDs include:

- `dino_trex_master`
- `dino_velociraptor_master`
- `dino_triceratops_master`
- `env_tropical_rainforest`
- `anim_*` IDs required by the example scenario

The scenario and execution plan must never depend directly on random generated filenames.

Do not casually edit catalog entries by hand. After an asset is actually created/imported and verified, register it with `pipeline/register_asset.py`, for example:

```bash
python3 pipeline/register_asset.py dino_trex_master \
  --type dinosaur \
  --status approved \
  --blender-source blender/dinosaurs/trex/trex_master.blend \
  --export-path staging/dinosaurs/trex_master.glb \
  --unreal-path /Game/Dinosaurs/TRex/SK_TRex_Master \
  --species tyrannosaurus_rex
```

Use `--replace` only for an intentional update of an existing logical asset.

### 5. Bootstrap assets in Blender 5.2.1

Because the catalog is initially empty, create the first reusable master assets needed by `raptor_hunt_001`:

- Tyrannosaurus rex
- Velociraptor
- Triceratops
- tropical rainforest environment kit

Create reusable masters, not shot-specific meshes.

For each dinosaur create a clean skeletal asset and the smallest useful animation set required to execute the scenario. At minimum satisfy every animation ID referenced by `raptor_hunt_001`.

Use Blender Python (`bpy`) for repeatable operations where practical. Preserve `.blend` source files under `blender/` and exported runtime assets under a documented import staging directory.

Do not repeatedly regenerate a dinosaur from scratch. Once a usable master exists, iterate that master.

### 6. Environment

Create a tropical rainforest vertical-slice environment with:

- dense jungle
- jungle edge
- open grassland
- rain
- wet ground
- atmospheric depth/fog

Use reusable vegetation/rock modules and UE PCG where appropriate. Optimize for cinematic framing and reasonable preview performance.

### 7. Dinosaur behavior

Implement only enough autonomous behavior for the vertical slice:

- idle
- wander
- orient/detect target
- stalk/chase
- flee
- threat/reaction
- attack trigger

The scenario/director must be able to override autonomous behavior for deterministic cinematic shots.

### 8. Cameras and Sequencer

Implement the initial registered camera presets required by `docs/UNREAL_EXECUTION_CONTRACT.md` and the example scenario:

- aerial_establishing
- static_hide
- medium_tracking
- low_threat_reveal
- wide_observational
- long_lens_observation

Generate a Level Sequence from `execution_plan.json`; do not hand-author the full scenario timeline.

### 9. Preview and visual QA hooks

Provide a command or documented procedure that:

1. runs deterministic preflight
2. refuses to render if required assets/presets remain unresolved
3. builds/opens the Unreal scenario from the compiled execution plan
4. renders representative preview frames or a low-resolution preview
5. writes outputs to predictable scenario-specific paths

Recommended layout:

```text
build/<scenario_id>/
  execution_plan.json
  preview/
    shot_001.png
    shot_002.png
    ...
```

Prepare a machine-readable place for visual-critic patches, but do not require an AI call for normal execution.

### 10. Final render

Configure Movie Render Queue for the scenario render settings. For the example scenario target 3840x2160 at 60 fps for final output, while preview uses the scenario `preview_scale` setting.

### 11. Close the bootstrap gaps

After creating/importing/registering the masters and required animations, rerun:

```bash
python3 pipeline/preflight.py scenarios/raptor_hunt_001/scenario.json
```

The bootstrap asset phase is not complete until preflight reports `ready`.

### 12. Documentation and verification

Add/update:

- exact local prerequisites
- Unreal version used
- Blender/Unreal asset import conventions
- how to run preflight
- how to register assets
- how to build/open the Unreal project
- how to execute `raptor_hunt_001`
- how to render preview
- how to render final

Run every deterministic validation/test you can run locally. Actually open/run Blender and Unreal for their respective verification steps. Do not claim Blender/Unreal steps succeeded unless you executed them.

## Important architecture rule

If a step can be reproduced exactly with code/config, implement it as code/config. Use AI reasoning only for creative or visual tasks such as initial asset design, animation repair, cinematic direction and visual criticism.

## Completion criteria

The bootstrap is complete when a fresh clone on the configured workstation can run deterministic preflight, resolve all required logical asset IDs, feed the compiled execution plan to Unreal, generate the `raptor_hunt_001` Level Sequence, and produce a preview render without manually rebuilding the scene shot-by-shot.
