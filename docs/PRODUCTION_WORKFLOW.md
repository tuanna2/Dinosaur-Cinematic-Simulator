# Production Workflow

The long-term goal is to let ChatGPT handle creative pre-production, let deterministic code handle normal production, and call Astra/Codex only when a genuinely creative or visual gap exists.

## 1. Creative pre-production

In chat, turn a story brief into a repository scenario package. Example brief:

> Eight Velociraptors hunt a Triceratops through a rainforest. The Triceratops escapes into grassland. A T-Rex appears and attacks the pack. Three-minute documentary cinematic video.

The approved result is saved as `scenarios/<scenario_id>/scenario.json`. This step may use ChatGPT because shot design is creative.

## 2. Deterministic preflight

Run:

```bash
python3 pipeline/preflight.py scenarios/<scenario_id>/scenario.json
```

This validates the scenario, expands actor groups, compiles the execution plan and resolves logical asset IDs against the asset catalog.

Outputs:

```text
build/preflight/<scenario_id>/preflight.json
build/preflight/<scenario_id>/execution_plan.json
```

Possible statuses:

- `ready`: continue directly to the web runtime; no AI agent is needed
- `missing_assets`: create explicit agent work requests
- `invalid_scenario`: fix the scenario/spec before runtime execution

## 3. Create AI work only when needed

For a `missing_assets` report:

```bash
python3 pipeline/build_agent_requests.py \
  build/preflight/<scenario_id>/preflight.json \
  --output build/preflight/<scenario_id>/agent_requests.json
```

The request file routes gaps to specialized roles. Examples:

- `dino_*` -> asset designer
- `env_*` / `prop_*` -> asset/environment designer
- `anim_*` -> animation director
- camera/weather presets -> the appropriate specialist

The AI agent must produce reusable assets/presets and register them in `config/asset_catalog.json`. Then rerun preflight.

During early bootstrap, the browser runtime may show obvious synthetic dinosaur placeholders even while preflight reports missing real assets. This lets camera, timing and behavior code progress without pretending the master asset exists.

## 4. Export the Three.js runtime bundle

Run:

```bash
python3 pipeline/export_web_bundle.py scenarios/<scenario_id>/scenario.json
```

This writes:

```text
web/public/runtime/execution_plan.json
web/public/runtime/asset_manifest.json
```

Then:

```bash
cd web
npm install
npm run dev
```

The Three.js implementation consumes the compiled plan according to `docs/THREEJS_EXECUTION_CONTRACT.md`.

Normal execution is deterministic:

```text
execution plan
  -> resolve GLB or bootstrap placeholder
  -> spawn actor instances
  -> apply actions/steering/animations
  -> apply camera presets
  -> realtime browser preview
```

## 5. Visual QA

Visual QA is the main production stage where an AI agent may still be valuable even when all assets exist.

A visual critic inspects preview frames and returns structured corrections such as:

- camera framing change
- actor spacing change
- light/fog/exposure adjustment
- animation mismatch
- collision/interpenetration problem
- environment readability issue

Corrections should become deterministic scenario/preset/code patches whenever possible. The agent should not manually rebuild the whole shot on every run.

## 6. Capture and post-production

After visual QA passes:

```text
Three.js browser runtime
  -> deterministic capture / frames/video
  -> FFmpeg/post-processing
  -> narration/TTS
  -> subtitles
  -> sound/music
  -> final video
```

## Bootstrap phase vs mature phase

During bootstrap, Astra may create most master dinosaurs, environments, animation sets and selected visual systems in Blender/Three.js. This is temporary factory-building work.

As the library matures, production should increasingly look like:

```text
Chat brief
  -> scenario.json
  -> preflight
  -> export web bundle
  -> Three.js
  -> preview
  -> optional visual critic
  -> capture
```

Astra should then be invoked primarily for new assets, missing animations, new reusable presets, or visual failures that deterministic rules cannot solve.

A future Unreal backend is optional. If added, it should consume the same execution plan rather than replacing this workflow.
