# Three.js Execution Contract

Three.js is the primary runtime for the cinematic simulator. Blender is the asset workshop. The browser runtime must execute compiled plans deterministically and must not require an LLM for normal playback.

## Input

Compile/export a scenario with:

```bash
python3 pipeline/export_web_bundle.py scenarios/<scenario_id>/scenario.json
```

This writes:

```text
web/public/runtime/execution_plan.json
web/public/runtime/asset_manifest.json
```

The web app consumes these files directly.

## Asset resolution

Scenarios use logical IDs. `config/asset_catalog.json` may map an approved asset to a browser path through `web_path`, for example:

```json
{
  "id": "dino_trex_master",
  "type": "dinosaur",
  "status": "approved",
  "blender_source": "blender/dinosaurs/trex_master.blend",
  "export_path": "exports/dinosaurs/trex_master.glb",
  "web_path": "/assets/trex_master.glb"
}
```

The runtime must never infer random filenames from a story prompt. If a GLB is missing during bootstrap, the development runtime may use a clearly synthetic placeholder so camera/timeline work can continue, but preflight still reports the real asset as missing.

## Actors

Each compiled instance has a stable `instance_id`, `group_id`, `asset_id` and species. The runtime must:

1. create exactly one runtime object per instance
2. retain lookup by `instance_id`
3. resolve group IDs through `actor_groups`
4. clone reusable GLB templates rather than reloading the same file for every pack member
5. keep scenario identity separate from mesh filenames

## Actions

Initial deterministic action families:

- idle / graze
- walk / enter
- stalk
- run / chase
- flee / retreat / scatter
- react / defend
- roar / victory_roar
- attack

During bootstrap the browser runtime may represent some actions with simple steering while the real animation library is incomplete. Once an animation is approved, action-to-animation mapping must be registered and reusable.

## Camera

Camera events use reusable presets. The initial runtime supports:

- `aerial_establishing`
- `static_hide`
- `medium_tracking`
- `low_threat_reveal`
- `wide_observational`
- `long_lens_observation`

A preset is deterministic code/config. AI may design a new preset, but playback of an existing preset does not require AI.

## Environment

The web runtime owns realtime scene setup including:

- lighting
- fog/atmosphere
- terrain/ground
- vegetation placement or instancing
- weather effects
- water/shaders when required

Environment assets should be modular and optimized for browser playback. Repeated vegetation should use instancing where practical.

## Development loop

```text
scenario.json
  -> export_web_bundle.py
  -> Vite / Three.js
  -> browser preview
  -> screenshot/video capture
  -> optional visual critic
  -> deterministic patch
```

The fast browser loop is the default production path.

## Final capture

Initial final output may be captured from the browser runtime at the requested aspect/FPS using a deterministic capture tool added later to the pipeline. Offline FFmpeg post-processing remains downstream.

A future high-end backend such as Unreal may consume the same `execution_plan.json`, but it is optional and must not change scenario semantics.
