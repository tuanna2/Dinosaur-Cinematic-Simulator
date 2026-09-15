# Visual critique workflow

This workflow turns a deterministic scenario shot into a repeatable visual-quality review package.

FLUX is used only for look development. The scenario and Three.js runtime remain authoritative for story semantics, actor count, timing, camera intent and staging.

## One-command preparation

From the repository root:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005
```

The runner executes:

1. `pipeline/export_web_bundle.py`
2. `cd web && npm run capture:preview`
3. `pipeline/generate_lookdev.py`
4. `pipeline/build_visual_critique_package.py`

The default image model is:

```text
x/flux-klein:4b
```

which is invoked through the same local CLI form used interactively:

```bash
ollama run x/flux-klein:4b "<prompt>"
```

## Outputs

For `shot_005`, the loop produces or consumes:

```text
build/preview/raptor_hunt_001/shot_005.png
build/lookdev/raptor_hunt_001/shot_005.png
build/lookdev/raptor_hunt_001/shot_005.prompt.txt
build/lookdev/raptor_hunt_001/shot_005.json
build/critique/raptor_hunt_001/shot_005.json
build/critique/raptor_hunt_001/shot_005.request.md
```

The critique JSON is the preferred handoff to Astra/visual critic. It contains:

- exact scenario shot definition
- environment context
- only actors relevant to that shot
- absolute preview/look-dev file paths
- FLUX provider/model metadata
- source-of-truth rules
- review dimensions
- deterministic patch policy
- expected JSON result shape

## Recommended Astra loop

Give Astra the critique package and request file together with `agents/visual-critic.md`.

The critic should route results into two classes.

### Deterministic patches

Use `patches` for things such as:

- camera distance, target, lens or framing
- actor spacing/placement
- fog, rain, exposure or light parameters
- environment density
- selection of an existing registered animation/preset

These should be applied in the scenario/runtime and verified by another deterministic capture.

### Reusable asset work

Use `requires_agent` for things such as:

- dinosaur anatomy/silhouette
- topology and joint continuity
- UV/material redesign
- eyes, teeth, gums and oral tissue
- skin weights and rig changes
- locomotion/attack/reaction animation
- reusable environment-master changes

These should be routed to `asset_designer`, `animation_director` or `environment_designer`, applied to Blender masters, exported to GLB, and verified by another capture.

## Review priority

Fix structural problems before cosmetic detail:

```text
anatomy / silhouette / mass
        ↓
topology continuity
        ↓
locomotion / weight / contact
        ↓
interaction geography
        ↓
camera / composition
        ↓
environment depth
        ↓
lighting / materials
        ↓
micro detail / color polish
```

This prevents repeated procedural detail work from hiding a fundamentally weak mesh or motion system.

## Incremental commands

If previews already exist:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --skip-export \
  --skip-capture
```

If the FLUX target already exists and only the package must be rebuilt:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --skip-export \
  --skip-capture \
  --skip-lookdev
```

Preview-only packaging is possible when FLUX is temporarily unavailable:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --skip-export \
  --skip-capture \
  --skip-lookdev \
  --allow-missing-lookdev
```

Inspect the intended subprocesses without running anything:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --dry-run
```

## Acceptance loop

After an agent changes a Blender master or deterministic setting:

1. export/register the updated asset if needed
2. regenerate the web runtime bundle
3. capture the same shot again
4. generate a fresh FLUX target only if the intended look changed materially
5. rebuild the critique package
6. compare again

A shot should not pass merely because it resembles FLUX. It passes when the deterministic 3D result satisfies the scenario, reads cinematically and meets the repository quality criteria without relying on hallucinated 2D details.
