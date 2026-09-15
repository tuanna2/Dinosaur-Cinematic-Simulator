# FLUX look-development workflow

This repository can use a local Ollama FLUX.2 Klein model as a visual look-development assistant. It does not replace Blender geometry, animation, Three.js staging, or final rendering.

Default model:

```text
x/flux2-klein:4b
```

This matches the tested local command:

```bash
ollama run x/flux2-klein:4b "a cat holding a sign that says hello world"
```

## Purpose

The deterministic Three.js runtime remains the source of truth for:

- actor count and species
- actor positions and interaction geography
- shot timing
- camera placement and framing
- continuity
- animation playback

FLUX produces an advisory visual-quality target that helps the visual critic and asset agents reason about:

- dinosaur anatomy and body mass
- silhouette quality
- skin/material response
- eyes, mouth, teeth and soft tissue
- lighting and atmosphere
- foliage richness and ground treatment
- cinematic contrast and documentary realism

The generated image is a reference target only. Never use it as a replacement video frame and never infer exact scene geometry or blocking from it.

## Important Ollama limitation

The current repository integration invokes:

```bash
ollama run x/flux2-klein:4b "<prompt>"
```

as a text-to-image command.

The captured Three.js preview is **not** sent into the FLUX model in this workflow. It remains available separately for the downstream visual critic. Therefore FLUX may change:

- actor count
- poses
- camera angle
- framing
- blocking
- environment layout

This is expected. Those differences are not scene defects.

For example, if the scenario contains eight raptors but the FLUX image shows two, the critic must ignore the FLUX count and use the scenario + deterministic preview as authoritative.

Metadata records this explicitly:

```json
{
  "generation_input": "text_only",
  "reference_sent_to_model": false,
  "composition_authority": "deterministic_preview",
  "lookdev_role": "advisory_anatomy_material_lighting_environment_target"
}
```

## Prerequisites

Confirm the exact local model works first:

```bash
ollama run x/flux2-klein:4b \
  "photorealistic tyrannosaurus rex in a wet prehistoric rainforest"
```

Generated images are written to the command's current directory. The pipeline runs Ollama in an isolated temporary directory and copies the newest generated image into `build/lookdev/...`.

No Python packages beyond the standard library are required.

## Generate deterministic scenario previews first

```bash
python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json
cd web
npm run capture:preview
cd ..
```

This creates frames in:

```text
build/preview/raptor_hunt_001/
```

## Generate one FLUX target

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005
```

Outputs:

```text
build/lookdev/raptor_hunt_001/shot_005.png
build/lookdev/raptor_hunt_001/shot_005.prompt.txt
build/lookdev/raptor_hunt_001/shot_005.json
```

The prompt includes the shot semantics, environment intent and camera language, but the FLUX result is not required to match the deterministic composition.

## Generate all shots

```bash
python3 pipeline/generate_lookdev.py scenarios/raptor_hunt_001/scenario.json
```

## One-command workflow

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005
```

If preview frames already exist:

```bash
python3 pipeline/run_lookdev_loop.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --skip-export \
  --skip-capture
```

## Useful options

Use another local model tag:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --model x/flux2-klein:4b-fp8
```

Inspect the generated prompt without invoking Ollama:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --dry-run
```

`--no-preview` now only prevents associating an existing preview path with the generated look-dev metadata. Ollama generation remains text-only either way.

## Critique policy

The critic must split responsibilities this way:

```text
scenario + deterministic Three.js preview
        -> actor count
        -> blocking
        -> camera/framing
        -> continuity
        -> motion geography

FLUX target
        -> anatomy/silhouette quality bar
        -> materials/skin/wetness
        -> eyes/mouth/teeth quality bar
        -> lighting/atmosphere
        -> environment richness
        -> documentary realism
```

Never change the real scene merely to reproduce a FLUX hallucination.

## Agent workflow

```text
scenario.json
   -> deterministic Three.js preview
   -> text-generated FLUX visual-quality target
   -> visual critic uses each source for its proper dimensions
   -> asset/environment/animation agent changes reusable Blender masters
   -> export GLB + capture preview again
   -> repeat until accepted
   -> Blender/Cycles final rendering
```

The visual critic should distinguish deterministic fixes (camera, lighting, density, actor placement) from changes that require editing a reusable Blender asset (anatomy, topology, material, rig or animation).
