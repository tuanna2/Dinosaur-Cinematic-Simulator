# Unreal Execution Contract

This document defines the deterministic interface that the Unreal implementation must satisfy. The implementation may use C++, Unreal Python/editor scripting, data assets, or Blueprints internally, but production scenarios must execute from data without requiring an LLM or routine manual editor work.

## Input

The engine consumes the output of:

```bash
python3 pipeline/compile_execution_plan.py scenarios/<scenario_id>/scenario.json --output build/<scenario_id>/execution_plan.json
```

A render may proceed only after preflight reports `ready`.

## Execution-plan responsibilities

### Environment

Given:

```json
{
  "asset_id": "env_tropical_rainforest",
  "weather": "heavy_rain",
  "time_of_day": "late_afternoon"
}
```

Unreal must deterministically:

1. resolve the logical environment ID through the asset catalog/registry
2. load or stream the environment
3. apply a known weather preset
4. apply a known time-of-day preset
5. wait for required world/PCG/navigation readiness before capture

### Actors

Each compiled instance has a stable `instance_id` and `asset_id`. Unreal must:

1. resolve the master asset
2. spawn exactly one actor per compiled instance
3. retain lookup by `instance_id`
4. expose the actor to Sequencer construction
5. fail clearly if an asset is absent instead of silently substituting a random asset

### Actions

The first vertical slice must support these reusable action families:

- idle
- walk / enter
- graze
- stalk
- run / chase / flee / retreat / scatter
- react
- defend
- roar / victory_roar
- attack

Actions may map to behavior-tree/state-machine commands, direct animation playback, or Sequencer tracks. The mapping must be deterministic once registered.

### Group actions

A logical actor such as `raptor_pack` expands to multiple instance IDs. A group action must operate on the resolved instance list in the execution plan. Per-member offsets/variation may be deterministic from a scenario seed or stable instance hash; they must not require an LLM at runtime.

### Camera

A camera event includes a preset, optional target and lens. The engine must provide a reusable preset registry. Initial presets required by the sample scenario:

- `aerial_establishing`
- `static_hide`
- `medium_tracking`
- `low_threat_reveal`
- `wide_observational`
- `long_lens_observation`

A preset defines camera placement/motion relative to subjects; it is not merely a name interpreted by AI each time.

### Sequence construction

For each shot the implementation must create or populate a Level Sequence with:

- camera/camera-cut section for the shot interval
- actor bindings as needed
- animation/action tracks or deterministic action triggers
- environment/weather/time state required by that interval

Sequence construction must be repeatable from the same execution plan.

### Preview

Provide a command or editor automation entry point that renders a low-cost preview using `render.preview_scale`. Preview output must have predictable paths so a visual-critic agent can inspect specific shots.

Recommended structure:

```text
build/<scenario_id>/
  execution_plan.json
  preflight.json
  preview/
    shot_001.png
    shot_002.png
    ...
```

### Final render

Provide a deterministic Movie Render Queue entry point that uses scenario render settings as the baseline. The implementation may apply an approved quality preset, but it must log the effective resolution, FPS, sequence, map, MRQ preset and output path.

## Errors

Machine-readable failures should distinguish at least:

- missing asset
- missing animation
- missing camera preset
- unsupported action
- environment load failure
- actor spawn failure
- sequence construction failure
- preview render failure
- final render failure

Do not recover from these by asking an LLM to guess at runtime. Return the failure to the orchestration layer; that layer may then create an agent work request if appropriate.

## Idempotence

Running the same scenario with the same approved asset catalog and deterministic seed should produce the same actor identities, shot timing, selected assets, and action/camera plan. Visual simulation may contain controlled variation only when explicitly configured.
