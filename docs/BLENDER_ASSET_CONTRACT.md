# Blender → Three.js Asset Contract

This contract keeps Blender 5.2.1 assets reusable and deterministic in the browser runtime.

## Runtime scale and orientation

- Treat 1 runtime unit as 1 meter.
- Put the dinosaur's ground contact at local Y=0 after GLB import.
- The final imported GLB must visually face +Z in Three.js when its root rotation is zero.
- Keep master asset root scale at 1,1,1 whenever practical.
- Apply destructive transforms intentionally in Blender before approving a master; do not rely on shot-specific corrective transforms.

## Master structure

Each dinosaur master should contain:

- one stable armature/skeleton
- skinned mesh(es)
- materials/textures
- reusable animation actions or compatible separate animation GLBs
- stable bone names across revisions

Do not regenerate a new skeleton for every shot. New skins or mesh revisions should continue to use the approved species skeleton unless a versioned migration is intentional.

## Animation IDs

Scenario animation IDs are logical IDs such as:

- `anim_raptor_stalk`
- `anim_raptor_run`
- `anim_raptor_attack`
- `anim_trex_walk`
- `anim_trex_roar`
- `anim_trex_attack`
- `anim_triceratops_graze`
- `anim_triceratops_run`
- `anim_triceratops_defend`

The web runtime supports two layouts:

1. animation clips embedded in the dinosaur master GLB
2. separate GLB animation assets registered with their own `web_path`

For embedded clips, name Blender Actions so the exported clip name clearly matches the logical action. Exact logical IDs are preferred; action-only names such as `run` or `attack` are accepted as a fallback.

## Loop policy

Normally loop:

- idle
- graze
- walk
- stalk
- run/chase/flee

Normally one-shot:

- attack
- defend
- react
- roar

The runtime handles loop policy and cross-fading; animation files should not contain unnecessary lead-in/out frames that make looping visibly jump.

## Export layout

Recommended source/runtime layout:

```text
blender/
  dinosaurs/
    trex/trex_master.blend
    velociraptor/velociraptor_master.blend
    triceratops/triceratops_master.blend
  environments/
    tropical_rainforest.blend

web/public/assets/
  dinosaurs/
    trex_master.glb
    velociraptor_master.glb
    triceratops_master.glb
  animations/
    ...
  environments/
    tropical_rainforest.glb
```

Register exported files through `pipeline/register_asset.py`; scenarios refer only to logical asset IDs.

## Validation checklist before approving a master

- correct apparent scale against the other species
- feet do not visibly slide for locomotion clips
- no obvious skin collapse at hips, neck, jaw or tail base
- root does not unexpectedly drift during in-place clips
- loop seams are acceptable
- bone names remain stable
- textures/materials load in Three.js
- GLB loads without console errors
- runtime zero rotation faces +Z
- at least one browser screenshot has been visually inspected

## Export helper

The repository provides `blender/export_glb.py` for repeatable Blender 5.2.1 GLB exports. Example:

```bash
blender --background blender/dinosaurs/trex/trex_master.blend \
  --python blender/export_glb.py -- \
  --output web/public/assets/dinosaurs/trex_master.glb
```

The script exports glTF/GLB with animations, skins, morph targets and +Y-up glTF conversion enabled.
