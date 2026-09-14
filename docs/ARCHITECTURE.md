# Dinosaur Cinematic Simulator Architecture

## Goal

Build a reusable cinematic dinosaur simulation pipeline for video production. Unreal Engine is the runtime and renderer; Blender is the asset workshop; AI agents are used only for creative judgment, missing assets, animation repair, scene design, and visual QA.

## Core principle

Use deterministic code whenever the expected result can be specified exactly. Use an AI agent only when the task requires creative judgment, visual reasoning, or generation.

## Pipeline

1. Human/ChatGPT writes a story brief.
2. Director agent converts the brief to `scenario.json`.
3. `pipeline/validate_scenario.py` validates structure and timing.
4. `pipeline/resolve_assets.py` compares requirements against `config/asset_catalog.json`.
5. Missing assets are delegated to the asset designer / Astra + Blender.
6. Unreal scene builder loads the scenario, spawns actors, configures environment and builds Sequencer tracks.
7. Unreal renders a low-cost preview.
8. Visual critic reviews preview frames and emits bounded patches.
9. Deterministic code applies approved patches.
10. Movie Render Queue renders final output.
11. FFmpeg/TTS/subtitle jobs run downstream.

## Repository ownership

- `agents/`: role instructions for AI agents.
- `knowledge/`: stable production knowledge shared by agents.
- `schemas/`: machine contracts.
- `config/`: reusable catalogs and runtime configuration.
- `scenarios/`: production scenario packages.
- `pipeline/`: deterministic orchestration scripts.
- `unreal/`: Unreal project and automation (to be bootstrapped by Astra on a machine with Unreal installed).
- `blender/`: Blender scripts and source assets.

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
- setting time of day or weather values
- playing an existing animation clip
- creating known Sequencer tracks
- validating JSON
- rendering with fixed settings
- FFmpeg encoding

## Target runtime

Unreal Engine 5.x with Sequencer, Movie Render Queue, PCG, Control Rig, Navigation and Python/Editor automation as appropriate.

Blender baseline for this repository: 5.2.1.
