# Astra Bootstrap Prompt

Use this prompt after cloning the repository on the workstation that has Blender 5.2.1 and Unreal Engine installed.

---

You are the bootstrap implementation agent for `Dinosaur-Cinematic-Simulator`.

Read these files first and follow them as contracts:

- `docs/ARCHITECTURE.md`
- `agents/director.md`
- `agents/asset-designer.md`
- `agents/visual-critic.md`
- `knowledge/dinosaur-behavior.md`
- `knowledge/cinematic-language.md`
- `schemas/scenario.schema.json`
- `config/asset_catalog.json`
- `scenarios/raptor_hunt_001/scenario.json`

Local environment:

- Blender version: 5.2.1
- Unreal Engine: detect the installed UE5 version and use it; document the exact version in the repo.
- Do not replace deterministic pipeline steps with LLM calls.

## Objective

Bootstrap a reusable cinematic dinosaur simulator whose first executable vertical slice is `raptor_hunt_001`.

The simulator is primarily a video-production engine, not a park-management game. Prioritize cinematic quality, reusable dinosaur assets, behavior, camera control, Sequencer automation and Movie Render Queue.

## Work in this order

### 1. Unreal project

Create the Unreal project under `unreal/DinosaurCinematicSimulator/`.

Enable/configure the minimum required UE plugins/features for:

- Sequencer
- Movie Render Queue / Movie Render Pipeline
- Control Rig
- PCG
- Navigation
- Python Editor Script Plugin if useful for deterministic editor automation

Do not enable unrelated plugins.

### 2. Director runtime/API

Implement a deterministic scenario executor that can consume the repository scenario format.

It must support at least:

- load scenario JSON
- load environment by asset ID
- spawn actor groups by asset ID and count
- actor lookup by scenario actor ID
- set weather preset
- set time-of-day preset
- apply camera preset
- execute basic actions
- play named animation clips
- build or populate a Level Sequence
- render a low-resolution preview
- invoke Movie Render Queue for final render

Prefer C++ for stable runtime/core types and Python/Editor scripting for editor automation where it simplifies Sequencer/MRQ generation. Blueprints may be used for content-facing configuration, but do not make the entire pipeline manual Blueprint wiring.

### 3. Asset registry bridge

Extend `config/asset_catalog.json` with Unreal paths and Blender source paths.

Create deterministic lookup code so the scenario uses logical IDs such as:

- `dino_trex_master`
- `dino_velociraptor_master`
- `dino_triceratops_master`
- `env_tropical_rainforest`

The scenario must never depend directly on random generated filenames.

### 4. Bootstrap assets in Blender 5.2.1

Because the catalog is initially empty, create the first reusable master assets needed by `raptor_hunt_001`:

- Tyrannosaurus rex
- Velociraptor
- Triceratops
- tropical rainforest environment kit

Create reusable masters, not shot-specific meshes.

For each dinosaur create a clean skeletal asset and the smallest useful animation set required to execute the scenario. At minimum satisfy every animation ID referenced by `raptor_hunt_001`.

Use Blender Python (`bpy`) for repeatable operations where practical. Preserve `.blend` source files under `blender/` and exported runtime assets under a documented import staging directory.

Do not repeatedly regenerate a dinosaur from scratch. Once a usable master exists, iterate that master.

### 5. Environment

Create a tropical rainforest vertical-slice environment with:

- dense jungle
- jungle edge
- open grassland
- rain
- wet ground
- atmospheric depth/fog

Use reusable vegetation/rock modules and UE PCG where appropriate. Optimize for cinematic framing and reasonable preview performance.

### 6. Dinosaur behavior

Implement only enough autonomous behavior for the vertical slice:

- idle
- wander
- orient/detect target
- stalk/chase
- flee
- threat/reaction
- attack trigger

The scenario/director must be able to override autonomous behavior for deterministic cinematic shots.

### 7. Cameras and Sequencer

Implement all camera presets currently referenced in `knowledge/cinematic-language.md` and the example scenario, including:

- aerial_establishing
- static_hide
- medium_tracking
- low_threat_reveal
- wide_observational
- long_lens_observation

Generate a Level Sequence for `raptor_hunt_001` from JSON rather than hand-authoring the full timeline.

### 8. Preview and visual QA hooks

Provide a command or documented procedure that:

1. validates the scenario
2. resolves assets
3. opens/builds the Unreal scenario
4. renders representative preview frames or a low-resolution preview
5. writes outputs to a predictable directory such as `outputs/<scenario_id>/preview/`

Prepare a machine-readable place for visual-critic patches, but do not require an AI call for normal execution.

### 9. Final render

Configure Movie Render Queue for the scenario render settings. For the example scenario target 3840x2160 at 60 fps for final output, while preview uses the `preview_scale` setting.

### 10. Documentation and verification

Add:

- exact local prerequisites
- Unreal version used
- Blender/Unreal asset import conventions
- how to run the validator
- how to resolve assets
- how to build/open the Unreal project
- how to execute `raptor_hunt_001`
- how to render preview
- how to render final

Run every deterministic validation/test you can run locally. Do not claim Blender/Unreal steps succeeded unless you actually executed them.

## Important architecture rule

If a step can be reproduced exactly with code/config, implement it as code/config. Use AI reasoning only for creative or visual tasks such as initial asset design, animation repair, cinematic direction and visual criticism.

## Completion criteria

The bootstrap is complete when a fresh clone on the configured workstation can follow documented steps to execute `raptor_hunt_001`, resolve all required logical asset IDs, generate its Unreal sequence and produce a preview render without manually rebuilding the scene shot-by-shot.
