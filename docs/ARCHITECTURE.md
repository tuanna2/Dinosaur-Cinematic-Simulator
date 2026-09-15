# Dinosaur Cinematic Simulator Architecture

## Goal

Build a reusable dinosaur cinematic simulation pipeline for video production. Three.js is the primary realtime runtime; Blender is the asset workshop; AI agents are used only for creative judgment, missing assets, animation repair, scene design, and visual QA.

Unreal Engine is not required for the default workflow. A future Unreal backend may consume the same execution plan for selected high-end renders without changing scenario semantics.

## Core principle

Use deterministic code whenever the expected result can be specified exactly. Use an AI agent only when the task requires creative judgment, visual reasoning, or generation.

## Pipeline

1. Human/ChatGPT writes a story brief.
2. Director agent converts the brief to `scenario.json`.
3. `pipeline/validate_scenario.py` validates structure and timing.
4. `pipeline/compile_execution_plan.py` expands stable actor instances and events.
5. `pipeline/resolve_assets.py` compares requirements against `config/asset_catalog.json`.
6. Missing assets are delegated to the relevant agent / Astra + Blender.
7. `pipeline/export_web_bundle.py` exports the deterministic runtime bundle.
8. Three.js loads the execution plan, GLB asset manifest, environment and camera presets.
9. Browser preview runs immediately; placeholders may be used only for bootstrap development.
10. Visual critic may review frames and emit bounded corrections.
11. Approved corrections become deterministic scenario/preset/code changes.
12. Browser capture / FFmpeg / TTS / subtitles run downstream.

## Repository ownership

- `agents/`: role instructions for AI agents.
- `knowledge/`: stable production knowledge shared by agents.
- `schemas/`: machine contracts.
- `config/`: reusable catalogs and runtime configuration.
- `scenarios/`: production scenario packages.
- `pipeline/`: deterministic orchestration scripts.
- `web/`: Vite + TypeScript + Three.js primary runtime.
- `blender/`: Blender scripts and editable source assets.
- `exports/`: engine-ready GLB/texture staging when produced locally; large generated files should normally stay out of Git.

## AI boundaries

AI SHOULD be used for:
- story-to-shot design
- initial environment / dinosaur / prop creation
- missing animation creation or repair
- cinematic camera design
- visual quality criticism
- complex scene redesign

AI SHOULD NOT be used for:
- spawning an actor with known parameters
- selecting an existing asset by exact ID
- setting known weather/time presets
- playing an existing animation clip
- applying an existing camera preset
- validating JSON
- compiling actor groups/events
- exporting the web runtime bundle
- normal Three.js playback
- FFmpeg encoding

## Primary runtime

Three.js + TypeScript + Vite.

The browser runtime consumes `execution_plan.json` and `asset_manifest.json`. Reusable Blender assets are exported as GLB/GLTF and addressed by logical asset IDs through the catalog.

Blender baseline for this repository: 5.2.1.

## Optional future backend

A high-end renderer such as Unreal Engine may be added later behind the same execution-plan contract. It must remain optional and should not become a dependency for normal scenario development or preview production.
