# Visual quality checkpoint — 2026-09-15

## Verdict

**Work in progress. Jurassic World Evolution 2/3 quality is not achieved.**
This checkpoint improves actual Blender/GLB assets and records executable browser
verification. It is not a finished cinematic deliverable. The previous bootstrap
review remains useful history; its file sizes and T-Rex/environment source paths
are superseded by the catalog and the evidence below.

## Asset changes

- T-Rex: revised skull and independent mandible on the existing skeleton, UV atlas,
  original 2048px baked albedo/normal/roughness, fitted dental rows and visible eyes.
  The torso and named action library are retained. Eye fitting uses measured skull
  intersections; camera captures caught both hidden eyes and excessive protrusion.
- Rainforest: wet soil PBR maps, fine curved grass, edge trees and understory leaves.
  Export copy batches material groups and reduces foliage geometry. The environment
  remains large (about 60 MB); this is not yet a certified realtime asset budget.
- Reviewed shot 6 exposed an edge trunk directly in front of the camera. Its module
  was moved in the editable environment source to clear the camera corridor.
- Browser hero capture exercises the actual asset loader and animation controller;
  it is a diagnostic view, not a replacement scenario or a concept render.
- Capture writes canvas pixels and camera transforms for reproducible composition
  review. No new runtime semantics were introduced in this quality pass.

## Current source of truth

The catalog now points to the actual candidate sources used for export:

- `blender/dinosaurs/trex/trex_quality_candidate.blend`
- `blender/environments/tropical_rainforest_quality_candidate.blend`

Original masters and before-quality copies remain local. Catalog `approved` values
are inherited bootstrap integration status; they must not be interpreted as final
visual acceptance. Current candidate notes explicitly reject that interpretation.

GLBs, packed Blender sources, texture bakes and captures are intentionally ignored
by Git under repository policy. A Git checkout alone does not contain the local
asset library. Preserve the Blender directory and exported assets when transferring
this workshop. The tracked scripts record how this procedural checkpoint was built.

## Executed validation

Blender 5.2.1 LTS was actually used for saved-source edits, CPU texture bakes and GLB
exports. Vite and installed Google Chrome actually loaded the exported scene.

- Python pipeline: 11 tests pass; preflight resolves all 15 IDs, 10 actors, 21 events.
- Web production build passes, with its large bundle advisory.
- `npm run capture:preview`: seven scenario frames inspected directly.
- `npm run capture:hero`: silhouette, stride, roar and head close-up inspected.
- `npm run verify:assets`: ten real skinned actors, eleven resolved/deforming clips,
  repeat-seek actor/pixel determinism and sampled pack clearance; no browser errors.

Local evidence: `build/preview/raptor_hunt_001/`, `build/preview/trex_quality/`,
`build/preview/asset_qa/verification.json`, and
`build/preview/trex-quality-verification.log`. Before images are preserved in
`build/preview/quality_pass_before/` and `build/preview/trex_quality_before/`.

## Remaining visual failures

All seven shots still fail the requested final quality bar. In particular:

1. Dinosaur bodies have primitive hip/neck/tail transitions and visible joint seams.
   T-Rex skull, eyelids, nostril and oral soft tissue still read as stylized geometry.
2. Raptors and Triceratops need substantial anatomical and material refinement.
3. Foot contact, weight transfer, turns and synchronized pack animation are unnatural.
4. Long shot intervals outlast short one-shots. Attack/roar settle into held poses.
5. Shot 2 crops the prey. Late shots lack clear predator/prey interaction geography.
6. Canopy shape, ground variation, rain readability and fog contrast remain weak.
7. No commercial-game parity, sustained FPS budget or finished video is certified.

Further production should address continuous anatomy/topology and motion before
adding more small surface details. More procedural detail alone will not close the
quality gap.
