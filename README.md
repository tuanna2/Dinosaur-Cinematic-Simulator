# Dinosaur Cinematic Simulator

AI-assisted dinosaur cinematic simulation and video production pipeline built around Unreal Engine, Blender, deterministic scenario specifications, and specialized AI agents.

## Current bootstrap

This repository separates deterministic execution from AI-only creative work.

- Unreal Engine: world simulation, behavior, Sequencer, cameras and Movie Render Queue.
- Blender 5.2.1: reusable dinosaur/environment master assets.
- `agents/*.md`: AI roles for direction, asset creation and visual QA.
- `schemas/*.json`: machine contracts.
- `pipeline/*.py`: deterministic validation and asset resolution.
- `scenarios/*`: executable cinematic specifications.

## First vertical slice

`scenarios/raptor_hunt_001/scenario.json`

A pack of eight Velociraptors hunts a Triceratops through a rain forest into open grassland. A T-Rex enters and attacks the pack. Target duration: 3 minutes, documentary cinematic style.

## Run deterministic checks

```bash
python3 pipeline/validate_scenario.py scenarios/raptor_hunt_001/scenario.json
python3 pipeline/resolve_assets.py scenarios/raptor_hunt_001/scenario.json
```

The initial asset catalog is intentionally empty. The resolver should therefore report the dinosaur/environment/animation IDs that must be bootstrapped before Unreal can execute the scene.

## Astra handoff

After cloning this branch on the workstation with Blender 5.2.1 and Unreal Engine installed, give Astra the complete instructions in:

`ASTRA_BOOTSTRAP_PROMPT.md`

Astra should bootstrap Unreal + Blender assets once. Over time, normal video production should reuse the asset library and invoke AI only when creative judgment, a genuinely missing asset/animation, or visual criticism is required.

See `docs/ARCHITECTURE.md` for the system design.
