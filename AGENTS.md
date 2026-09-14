# Repository Agent Instructions

This repository is a dinosaur cinematic simulator and video-production engine. It is not primarily a park-management game.

## Core rule

Use deterministic code whenever the expected result can be specified exactly. Use an AI agent only for tasks that require creative judgment, visual judgment, asset creation, animation adaptation, or ambiguous design decisions.

## Read first

Before changing architecture or content, read:

1. `docs/ARCHITECTURE.md`
2. `schemas/scenario.schema.json`
3. `config/asset_catalog.json`
4. `knowledge/dinosaur-behavior.md`
5. `knowledge/cinematic-language.md`

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
- Level Sequence track generation from an execution plan
- Movie Render Queue invocation
- frame/video post-processing
- file/path validation

The pipeline entry point for these checks is `pipeline/preflight.py`.

## AI-only or AI-preferred responsibilities

AI may be used for:

- story brief -> scenario design
- shot and camera composition decisions
- creation of a missing dinosaur/environment/prop master asset
- rigging or animation adaptation when no reusable clip exists
- visual critique of preview renders
- repairing a shot whose visual result fails quality targets
- designing a new reusable behavior or cinematic preset when the existing library cannot express the intent

## Asset policy

- Reuse approved master assets before creating new ones.
- Address assets through logical IDs in `config/asset_catalog.json`.
- Do not hard-code random Blender filenames or Unreal content paths into scenarios.
- Dinosaur master assets must be reusable, rigged, and animation-compatible.
- Generated one-off assets should not silently become masters; register them explicitly.

## Blender

The bootstrap workstation uses Blender 5.2.1. Prefer Python (`bpy`) or a stable tool/MCP interface for repeatable changes. Save editable `.blend` sources and export engine-ready assets separately.

## Unreal

The exact installed Unreal Engine version must be detected on the workstation and documented before committing version-sensitive engine code. Prefer stable core code for scenario execution and editor scripting for repeatable Sequencer/MRQ construction. Avoid workflows that require manual editor clicking for routine production.

## Required workflow before Unreal execution

Run:

```bash
python3 pipeline/preflight.py scenarios/<scenario_id>/scenario.json
```

A scenario with `missing_assets` is not render-ready. Missing assets may be sent to the appropriate AI agent. A `ready` result may proceed without an AI agent.

## Change discipline

- Preserve schema compatibility unless intentionally bumping the schema version.
- Add tests for deterministic pipeline changes.
- Keep generated caches, Unreal build outputs, Blender autosaves, and rendered frames out of Git unless explicitly required.
- Never copy Jurassic World/JWE proprietary models, logos, audio, UI, or other copyrighted game assets into this repository.
