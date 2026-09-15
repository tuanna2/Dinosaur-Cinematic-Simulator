# Repository Agent Instructions

This repository is a dinosaur cinematic simulator and video-production engine. It is not primarily a park-management game.

## Core rule

Use deterministic code whenever the expected result can be specified exactly. Use an AI agent only for tasks that require creative judgment, visual judgment, asset creation, animation adaptation, or ambiguous design decisions.

## Read first

Before changing architecture or content, read:

1. `docs/ARCHITECTURE.md`
2. `docs/THREEJS_EXECUTION_CONTRACT.md`
3. `schemas/scenario.schema.json`
4. `config/asset_catalog.json`
5. `knowledge/dinosaur-behavior.md`
6. `knowledge/cinematic-language.md`
7. `docs/FLUX_LOOKDEV.md`
8. `docs/VISUAL_CRITIQUE_WORKFLOW.md`

Role-specific agents must also read their matching file in `agents/`.

## Deterministic responsibilities

Do not call an LLM for these operations:

- scenario schema validation
- asset lookup by logical ID
- actor spawning once a logical asset ID is resolved
- actor/group instance naming
- weather/time preset application once the preset exists
- animation playback once an animation ID is resolved
- camera preset application once defined
- execution-plan compilation
- Three.js runtime-bundle export
- browser playback of an approved execution plan
- deterministic preview capture
- packaging preview/look-dev inputs for visual critique
- frame/video post-processing
- file/path validation

The pipeline entry point for checks is `pipeline/preflight.py`; the web export entry point is `pipeline/export_web_bundle.py`.

## AI-only or AI-preferred responsibilities

AI may be used for:

- story brief -> scenario design
- shot and camera composition decisions
- FLUX look-development target generation
- creation/refinement of a missing dinosaur/environment/prop master asset
- rigging or animation adaptation when no reusable clip exists
- visual critique of preview renders against scenario intent and optional FLUX targets
- repairing a shot whose visual result fails quality targets
- designing a new reusable behavior or cinematic preset when the existing library cannot express the intent

## FLUX look-development policy

The default local image model is `x/flux-klein` through Ollama CLI. The canonical tagged equivalent is `x/flux2-klein:4b`.

FLUX is advisory only:

- scenario semantics and deterministic Three.js staging remain authoritative
- never use a FLUX frame directly as a final video frame
- never reproduce hallucinated extra animals/props merely because they appear in a target
- use the target to expose realism gaps in anatomy, materials, environment, atmosphere, lighting and visual hierarchy
- route reusable mesh/material/rig/animation defects back to Blender master assets

Prepare a review with:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/<scenario_id>/scenario.json \
  --shot-id <shot_id>
```

Then read the generated package under `build/critique/<scenario_id>/` together with `agents/visual-critic.md`.

## Asset policy

- Reuse approved master assets before creating new ones.
- Address assets through logical IDs in `config/asset_catalog.json`.
- Do not hard-code random Blender filenames into scenarios.
- Browser-ready GLB/GLTF assets use the catalog `web_path` field.
- Dinosaur master assets must be reusable, rigged, and animation-compatible.
- Generated one-off assets should not silently become masters; register them explicitly.
- Placeholder meshes in the web runtime are development aids, not approved master assets.
- Do not spend repeated iterations adding micro-detail to a master that still fails anatomy, topology continuity or locomotion quality.

## Blender

The bootstrap workstation uses Blender 5.2.1. Prefer Python (`bpy`) or a stable tool/MCP interface for repeatable changes. Save editable `.blend` sources and export engine-ready GLB/GLTF separately.

For visual-quality work, prioritize structural corrections in this order: anatomy/silhouette/body mass -> topology continuity -> rig/deformation/locomotion -> interaction geography -> environment/camera -> materials/lighting -> micro-detail.

## Three.js runtime

Three.js + TypeScript + Vite is the default engine/runtime. Routine production must not require Unreal Engine.

Before changing runtime semantics, preserve compatibility with `execution_plan.json`. Favor small reusable systems for:

- logical asset loading
- actor/group lookup
- steering/behavior
- animation state
- camera presets
- environment/weather
- capture hooks

Do not move creative interpretation into the render loop.

## Optional Unreal backend

Unreal may be added later as an optional high-end renderer. If implemented, it must consume the same execution plan and must not become a dependency for the normal browser workflow.

## Required workflow before production playback

Run:

```bash
python3 pipeline/preflight.py scenarios/<scenario_id>/scenario.json
python3 pipeline/export_web_bundle.py scenarios/<scenario_id>/scenario.json
```

A scenario with `missing_assets` is not production-ready, although the web runtime may still use visible placeholders during bootstrap development. A `ready` result can proceed without an AI agent.

## Change discipline

- Preserve schema compatibility unless intentionally bumping the schema version.
- Add tests for deterministic pipeline changes.
- Keep generated caches, node modules, browser build outputs, Blender autosaves, large GLBs and rendered frames out of Git unless explicitly required.
- Never copy Jurassic World/JWE proprietary models, logos, audio, UI, or other copyrighted game assets into this repository.
