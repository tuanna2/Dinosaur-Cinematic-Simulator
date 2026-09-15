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
  "export_path": "web/public/assets/dinosaurs/trex_master.glb",
  "web_path": "/assets/dinosaurs/trex_master.glb"
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
6. expose behavior/animation state through machine-readable runtime snapshots

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

Actions may include `offset_seconds` relative to their shot start. The compiler converts that offset into an absolute event timestamp. Offsets must remain inside the shot duration.

This allows actions inside one shot to be sequenced deterministically, for example:

```json
{
  "id": "shot_005",
  "start": 125,
  "duration": 12,
  "actions": [
    {"actor": "trex_01", "action": "enter", "offset_seconds": 0},
    {"actor": "trex_01", "action": "roar", "offset_seconds": 6}
  ]
}
```

The runtime uses `THREE.AnimationMixer` per dinosaur instance. Approved animations may be embedded in the master GLB or provided as separate GLB animation assets. Locomotion clips loop; attack/defend/react/roar are treated as one-shots. Transitions cross-fade instead of hard-switching.

## Behavior

Scenario actions select deterministic behavior intents. The first runtime layer supports:

- target-oriented stalk/chase/attack movement
- flee/scatter/retreat movement
- stable raptor-pack surround slots
- local pack-member separation
- smooth heading changes
- scenario override of autonomous motion

AI does not choose movement each frame.

## Camera

Camera events use reusable presets. The initial runtime supports:

- `aerial_establishing`
- `static_hide`
- `medium_tracking`
- `low_threat_reveal`
- `wide_observational`
- `long_lens_observation`

A preset is deterministic code/config. Camera changes smoothly converge to the registered offset/focal settings while tracking the target. AI may design a new preset, but playback of an existing preset does not require AI.

## Environment

The web runtime owns realtime scene setup including:

- lighting
- fog/atmosphere
- deterministic rain particles
- time-of-day presets
- placeholder terrain/vegetation before the real environment GLB exists

When a registered environment GLB is available, the placeholder world is hidden automatically while runtime weather/lighting remain active.

## Deterministic time control

The browser runtime must support exact timeline control independent of realtime browser speed:

```js
window.dinosaurRuntime.pause()
window.dinosaurRuntime.seek(42.5)
window.dinosaurRuntime.stepFrame()
window.dinosaurRuntime.renderFrameAt(90)
window.dinosaurRuntime.snapshot()
window.dinosaurRuntime.captureDataUrl()
```

`seek()` reconstructs state from time zero using fixed simulation steps derived from scenario FPS. This is intentionally slower than normal playback but repeatable and suitable for capture/QA.

## Development loop

```text
scenario.json
  -> export_web_bundle.py
  -> Vite / Three.js
  -> browser preview
  -> deterministic shot screenshots
  -> optional visual critic
  -> deterministic scenario/preset/asset patch
```

The fast browser loop is the default production path.

## Preview capture

The web package includes a system-Chrome capture command:

```bash
cd web
npm run capture:preview
```

It starts Vite, opens the runtime headlessly, seeks to the midpoint of every camera shot and saves one PNG per shot under:

```text
build/preview/<scenario_id>/
```

This output is intended for visual QA and Dream-Loop-style criticism. Set `CHROME_BIN` when Chrome/Chromium is not at a standard path.

## Final capture

Final long-form fixed-FPS frame/video capture remains a separate production stage. It should consume the same deterministic browser APIs rather than rely on interactive screen recording. FFmpeg post-processing remains downstream.

A future high-end backend such as Unreal may consume the same `execution_plan.json`, but it is optional and must not change scenario semantics.
