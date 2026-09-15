# Original dinosaur asset workshop

These assets were authored locally with Blender **5.2.1 LTS**, using original
procedural geometry and packed texture artwork. No external dinosaur/game assets
were imported. Coordinates in authoring helpers are `(right, forward, up)` and
converted to Blender `(X, -Y, Z)`; GLB exports face Three.js +Z with Y up.

## Saved masters

- `dinosaurs/velociraptor/velociraptor_master.blend`
- `dinosaurs/trex/trex_master.blend`
- `dinosaurs/triceratops/triceratops_master.blend`
- `environments/tropical_rainforest.blend`

Adjacent numbered files preserve successive source revisions where
applicable. The current masters are the working sources. **Edit these masters;
do not rerun initial creation over them.** Sources, revision history, runtime
GLBs and preview images stay local and are ignored by Git. Back up this workshop
directory when transferring the project; scripts alone are not a substitute for
preserving subsequent manual edits.

All dinosaurs retain the original named root/pelvis/neck/head/jaw, three tail
bones, left/right thigh/shin/foot and forelimb bones. The texture images are packed
in the source and embedded in the GLBs. Animation IDs are embedded as exact Action
names. Each logical animation registration points to its species master GLB.

## Routine export

From the repository root:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/dinosaurs/trex/trex_master.blend --python-exit-code 1 \
  --python blender/export_glb.py -- \
  --output web/public/assets/dinosaurs/trex_master.glb
python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json
cd web
npm run build
npm run capture:preview
npm run verify:assets
```

`optimize_exports.py` exports all current dinosaur masters with the standard
helper and batches/decimates a temporary copy of the environment for the browser.
It retains the detailed environment source. It also validates and saves the
current dinosaur meshes; use source control/backups before intentional revisions.

## Construction history

The following scripts record the sequential workshop operations. They are
**one-time revisions, not idempotent repair commands**. Do not replay them against
already revised masters. For a clean reconstruction in a separate empty checkout,
the order used was:

1. `bootstrap_assets.py`
2. `refine_bootstrap.py`
3. `polish_bootstrap.py`
4. `refine_animation.py`
5. `optimize_exports.py`
6. `refine_silhouette.py` (creates the intact `_v4` checkpoint)
7. `finalize_masters.py` (loads that checkpoint and adds non-destructive joint/tail bridges)
8. `repair_skin_weights.py`
9. `correct_jaw_axis.py`
10. `separate_jaw_skin.py`

Other repair/weld scripts record rejected surface experiments. They are retained
for traceability, **are not part of the final reconstruction**, and must not be
run against the current masters. `finalize_masters.py` deliberately restores a
numbered checkpoint; it is not a routine export command.

Run Blender scripts with `--background --python-exit-code 1 --python <script>`.
The initial creator refuses to overwrite an existing master. Revision scripts
preserve a numbered source before editing. Asset registration is performed by
`register_bootstrap.py` through `pipeline/register_asset.py`.

## Verification

`npm run verify:assets` launches system Chrome against Vite and checks all ten
actors are skinned GLBs, the real environment replaces the placeholder world,
all eleven clips deform vertices through the existing AnimationMixer, the pack
respects target body clearance, and repeated timeline seeks reproduce both actor
states and canvas pixels. It saves individual animation pose pairs, event-time
frames and `build/preview/asset_qa/verification.json`.

These checks establish runtime integration. They do not certify paleontological
accuracy, natural locomotion, cinematic composition or final visual quality.
See `docs/VISUAL_BOOTSTRAP_REVIEW.md` for the actual visual review.

## Current quality candidates

The asset catalog now points to `trex_quality_candidate.blend` and
`tropical_rainforest_quality_candidate.blend`. Keep these saved sources; exporting
an older master will overwrite the reviewed GLB with an older version.

After the baseline construction history above, the one-time revision order was:

1. `trex_quality_pass.py`
2. `trex_skull_revision.py`
3. `trex_detail_fit.py`
4. `trex_oral_revision.py`
5. `trex_eye_fit.py`
6. `rainforest_quality_pass.py` (independent of the T-Rex sequence)
7. `clear_camera_corridor.py`

These mutate candidates and are **not idempotent**. Do not repeat them on the
already revised source. Texture bakes are packed; external PNGs are generated.

Routine candidate exports:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background \
  blender/dinosaurs/trex/trex_quality_candidate.blend --python-exit-code 1 \
  --python blender/export_glb.py -- \
  --output web/public/assets/dinosaurs/trex_master.glb
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 \
  --python blender/export_quality_environment.py
python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json
cd web
npm run capture:hero
npm run capture:preview
npm run verify:assets
```

`export_quality_environment.py` loads the saved candidate and applies reductions
only to the export session; it never saves the reduced mesh over the source.
See `docs/VISUAL_QUALITY_PROGRESS.md` for the latest quality verdict.
