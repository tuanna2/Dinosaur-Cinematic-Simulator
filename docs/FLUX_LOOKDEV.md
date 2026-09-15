# FLUX look-development workflow

This repository can use a local Ollama image-generation model as a visual look-development assistant. It does not replace Blender geometry, animation, or final rendering.

Default model:

```text
x/flux-klein:4b
```

This matches the working local command:

```bash
ollama run x/flux-klein:4b "a cat holding a sign that says hello world"
```

Ollama's model page also exposes the FLUX.2 Klein family under `x/flux2-klein`; use `--model` if your local tag differs.

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

Confirm the exact local command works first:

```bash
ollama run x/flux-klein:4b "photorealistic tyrannosaurus rex in a wet prehistoric rainforest"
```

The integration intentionally invokes the `ollama` CLI rather than relying on an experimental HTTP image API. Ollama writes generated images into the command's current directory; the pipeline runs each generation inside an isolated temporary directory and copies the resulting image into `build/lookdev/...`.

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

If `build/preview/<scenario>/<shot>.png` exists, the command copies it to the isolated generation directory as `reference.png` and includes `./reference.png` in the Ollama prompt. This follows Ollama's normal CLI convention for attaching an image path. FLUX is asked to preserve composition while upgrading the frame into a photorealistic target.

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

Generate without attaching the Three.js frame:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --no-preview
```

Use another tag:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --model x/flux2-klein:4b
```

Inspect the generated prompt without invoking Ollama:

```bash
python3 pipeline/generate_lookdev.py \
  scenarios/raptor_hunt_001/scenario.json \
  --shot-id shot_005 \
  --dry-run
```

## Ollama image settings

Ollama image-generation settings such as image width, height, steps, seed and negative prompt are currently interactive `/set` settings. This integration deliberately starts with the proven one-shot `ollama run MODEL PROMPT` path rather than attempting to emulate unstable image-generation API fields.

If reproducible settings become important, extend the provider layer to launch an interactive session or use the stable image API available in the installed Ollama version. Do not leak provider-specific settings into scenario JSON.

## Reference-image caveat

FLUX.2 Klein advertises generation/editing capabilities, but CLI support can vary between Ollama builds. If attaching the preview fails or gives poor results, run with `--no-preview`. The result is still useful for anatomy, material, lighting and environment look development, but should not be treated as an exact composition match.

## Agent workflow

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

The visual critic should distinguish deterministic fixes (camera, lighting, density, actor placement) from changes that require editing a reusable Blender asset (anatomy, topology, material, rig or animation).
