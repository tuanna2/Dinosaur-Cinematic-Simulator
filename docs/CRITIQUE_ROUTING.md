# Visual critique routing

The visual critic produces a review result. This repository then routes that result deterministically into two different queues:

```text
visual critique result
        |
        +--> deterministic patches
        |      camera / placement / lighting / fog / density / presets
        |
        +--> reusable asset work
               dinosaur anatomy/materials
               animation/rig/motion
               environment master assets
```

The router does not call an AI model, edit Blender files, or apply scenario patches. It only validates, groups and packages work so Astra or a specialized agent can execute it safely.

## 1. Save the visual critic result

For a shot such as `shot_005`, save the critic JSON as:

```text
build/critique/raptor_hunt_001/shot_005.result.json
```

The result should follow:

```text
schemas/visual_critique_result.schema.json
```

Example:

```json
{
  "shot_id": "shot_005",
  "pass": false,
  "issues": [
    {
      "category": "anatomy",
      "severity": "blocking",
      "observation": "The T-Rex neck and shoulder transition lacks believable continuous mass.",
      "evidence": "preview_vs_lookdev_quality_reference"
    }
  ],
  "patches": [
    {
      "path": "camera.distance",
      "operation": "set",
      "value": 12.5,
      "reason": "Keep the full threat silhouette readable."
    }
  ],
  "requires_agent": [
    {
      "agent": "asset_designer",
      "asset_id": "dino_trex_master",
      "severity": "blocking",
      "reason": "Increase continuous neck-to-shoulder volume and remove primitive joint transitions.",
      "acceptance_criteria": [
        "No visible neck-to-torso seam in three-quarter view.",
        "The same rig still deforms cleanly during walk, roar and attack captures."
      ]
    }
  ]
}
```

## 2. Route the result

Run:

```bash
python3 pipeline/route_visual_critique.py \
  scenarios/raptor_hunt_001/scenario.json \
  build/critique/raptor_hunt_001/shot_005.result.json
```

By default the router writes:

```text
build/work/raptor_hunt_001/shot_005/
├── routing.json
├── deterministic_patches.json
├── work_requests.json
└── requests/
    ├── raptor_hunt_001__shot_005__asset_designer__dino_trex_master.md
    ├── raptor_hunt_001__shot_005__animation_director__anim_trex_roar.md
    └── ...
```

## 3. Grouping behavior

Multiple critic findings for the same `(agent, asset_id)` are merged into one reusable work request.

For example, these two findings:

```text
T-Rex neck mass is too thin
T-Rex eye/oral materials look synthetic
```

both targeting `asset_designer + dino_trex_master` become one request containing both reasons and all unique acceptance criteria.

The highest applicable severity becomes the request priority.

If a `requires_agent` item omits `severity`, the router infers priority from matching issue categories:

- `asset_designer` <- anatomy, material, continuity
- `animation_director` <- animation, continuity
- `environment_designer` <- environment, lighting, continuity

## 4. Asset validation

By default every `asset_id` in `requires_agent` must already exist in `config/asset_catalog.json`.

This prevents a visual critic hallucination from silently creating a new master asset ID.

For intentional new work only, use:

```bash
python3 pipeline/route_visual_critique.py \
  scenarios/raptor_hunt_001/scenario.json \
  build/critique/raptor_hunt_001/shot_005.result.json \
  --allow-unregistered-assets
```

Registered assets are enriched with their current Blender source, export path, web path, skeleton ID and species so Astra knows exactly which reusable source to modify.

## 5. Astra execution contract

Each generated Markdown request is an executable brief for Astra or the matching specialized agent.

The agent must:

- modify the reusable registered asset, not create a shot-specific fake
- preserve the logical asset ID
- preserve scenario semantics and deterministic actor count/staging
- treat FLUX only as a visual-quality reference
- ignore FLUX hallucinated actor count, framing and blocking
- export/register the runtime asset using the existing catalog contract
- recapture the same shot after the change
- rebuild the visual critique package
- verify every acceptance criterion in the actual preview/render before marking work complete

## 6. Deterministic patches stay separate

`deterministic_patches.json` is deliberately not applied automatically yet.

Examples include:

```text
camera.distance
camera target/framing
actor spacing
fog density
rain strength
lighting/exposure
existing preset selection
```

Keeping these separate prevents Blender asset work and scenario/runtime configuration work from being mixed together. A later deterministic patch-applier can consume this file after path contracts are formalized.

## 7. Full loop

```text
scenario
  -> Three.js deterministic capture
  -> FLUX text-generated quality target
  -> visual critique package
  -> visual critic result JSON
  -> route_visual_critique.py
       |-> deterministic_patches.json
       `-> Astra work requests
              -> edit Blender master / animation / environment
              -> export GLB
              -> capture same shot again
              -> rebuild critique package
              -> review again
```

FLUX never becomes scene truth and never becomes a final video frame.
