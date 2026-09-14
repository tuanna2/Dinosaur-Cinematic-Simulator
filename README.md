# Dinosaur Cinematic Simulator

AI-assisted dinosaur cinematic simulation and video-production pipeline built around Unreal Engine, Blender, deterministic scenario specifications, and specialized AI agents.

The project is designed primarily as a cinematic/video factory rather than a park-management game.

## Architecture principle

**Deterministic when possible; AI only when necessary.**

Normal production should not ask an LLM to spawn actors, apply known weather, play known animations, choose registered assets, construct known camera presets, or invoke rendering. AI is reserved for story/shot design, genuinely missing reusable assets or animations, and visual criticism/repair.

See `AGENTS.md` for repository-wide agent rules.

## Current bootstrap

- Unreal Engine: world simulation, dinosaur behavior, Sequencer, cameras and Movie Render Queue.
- Blender 5.2.1: reusable dinosaur/environment master assets.
- `agents/*.md`: specialized AI role contracts.
- `knowledge/*.md`: reusable domain/cinematic knowledge.
- `schemas/*.json`: machine contracts.
- `pipeline/*.py`: deterministic validation, compilation, asset resolution and agent-request generation.
- `scenarios/*`: executable cinematic specifications.

## First vertical slice

`scenarios/raptor_hunt_001/scenario.json`

A pack of eight Velociraptors hunts a Triceratops through a rainforest into open grassland. A T-Rex enters and attacks the pack. Target duration: 3 minutes, documentary cinematic style.

## Deterministic preflight

From the repository root:

```bash
python3 pipeline/preflight.py scenarios/raptor_hunt_001/scenario.json
```

This validates the scenario, expands actor groups into stable instance IDs, compiles an Unreal-facing execution plan, and resolves required logical assets.

Outputs are written to:

```text
build/preflight/raptor_hunt_001/preflight.json
build/preflight/raptor_hunt_001/execution_plan.json
```

During bootstrap the asset catalog is intentionally empty, so the expected status is `missing_assets`.

Turn those deterministic gaps into explicit AI work requests with:

```bash
python3 pipeline/build_agent_requests.py \
  build/preflight/raptor_hunt_001/preflight.json \
  --output build/preflight/raptor_hunt_001/agent_requests.json
```

When the asset catalog is mature, a `ready` preflight should proceed directly to Unreal without an asset-generation agent.

## Tests

The deterministic Python layer uses only the standard library:

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions also runs the test/compile/preflight contract on the bootstrap PR.

## Unreal handoff contract

The Unreal implementation must consume `execution_plan.json` without asking an LLM to reinterpret the scenario at runtime.

See:

- `docs/UNREAL_EXECUTION_CONTRACT.md`
- `docs/PRODUCTION_WORKFLOW.md`
- `docs/ARCHITECTURE.md`

## Astra bootstrap

After cloning this branch on the workstation with Blender 5.2.1 and Unreal Engine installed, give Astra the complete instructions in:

`ASTRA_BOOTSTRAP_PROMPT.md`

Astra is expected to build the initial factory: Unreal integration, reusable dinosaur/environment masters, animation/preset libraries, Sequencer automation and rendering. Over time, normal video production should reuse that library and invoke AI only for new creative/visual gaps.

## IP policy

The project may take genre/workflow inspiration from dinosaur simulation games, but repository assets must be original or properly licensed. Do not copy Jurassic World/JWE proprietary models, logos, audio, UI, or other protected game assets.
