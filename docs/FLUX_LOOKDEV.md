# FLUX look-development workflow

This repository can use a local Ollama image-generation model as a visual look-development assistant. It does not replace Blender geometry, animation, or final rendering.

Default model:

```text
x/flux2-klein:4b
```

## Purpose

The Three.js runtime remains the deterministic source of truth for shot timing, actor positions, behavior and camera composition. FLUX produces a photorealistic target frame that helps the visual critic and asset agents reason about:

- dinosaur anatomy and body mass
- skin/material response
- eyes, mouth, teeth and soft tissue
- lighting and atmosphere
- foliage density and ground treatment
- cinematic contrast and depth

The generated image is a reference target only. Do not use it as a replacement video frame and do not infer exact 3D geometry from it.

## Prerequisites

Confirm Ollama and the image model work locally first:

```bash
ollama run x/flux2-klein:4b "photorealistic tyrannosaurus rex in a wet prehistoric rainforest"
```

The integration uses Ollama's local HTTP endpoint by default:

```text
http://127.0.0.1:11434/api/generate
```

No Python packages beyond the standard library are required.

## Generate scenario previews first

```bash
python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json
cd web
npm run capture:preview
cd ..
```

This creates deterministic frames in:

```text
build/preview/raptor_hunt_001/
```

## Generate one FLUX target

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005
```

When `build/preview/<scenario>/<shot>.png` exists, it is automatically sent as a reference image so the prompt asks FLUX to preserve the shot composition.

Outputs:

```text
build/lookdev/raptor_hunt_001/shot_005.png
build/lookdev/raptor_hunt_001/shot_005.prompt.txt
build/lookdev/raptor_hunt_001/shot_005.json
```

## Generate all shots

```bash
python3 pipeline/generate_lookdev.py scenarios/raptor_hunt_001/scenario.json
```

## Useful options

Text-to-image only, without the Three.js reference frame:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --no-preview
```

Use a different local model or Ollama endpoint:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --model x/flux2-klein:4b \
  --ollama-url http://127.0.0.1:11434
```

Inspect prompts without invoking the model:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --dry-run
```

Set reproducibility/output parameters when supported by the installed Ollama image runner:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --width 1024 \
  --height 576 \
  --seed 42
```

## Ollama version caveat

Ollama's image-generation support has changed across experimental releases. Some versions accept FLUX image generation through `/api/generate`; some newer releases have temporarily disabled it. Reference-image editing has also varied by version.

The integration therefore keeps Ollama isolated behind `pipeline/generate_lookdev.py`. If the local model works but a future Ollama API changes, only this provider layer should need adjustment; the scenario/runtime/Blender contracts should not change.

If reference-image editing behaves poorly, rerun with `--no-preview`. The resulting target is still useful for anatomy, material and lighting look development, but it must not be treated as a composition match.

## Agent workflow

Recommended loop:

```text
scenario.json
   -> Three.js deterministic preview
   -> FLUX target image
   -> visual critic compares preview vs target
   -> asset/environment/animation agent changes Blender masters
   -> export GLB + capture preview again
   -> repeat until accepted
   -> Blender/Cycles final rendering
```

The visual critic should distinguish between deterministic fixes (camera, lighting, density, actor placement) and changes that require editing a reusable Blender asset (anatomy, topology, material, rig or animation).
