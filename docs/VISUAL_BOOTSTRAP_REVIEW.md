# Visual bootstrap review — 2026-09-15

## Outcome

**The technical asset bootstrap works. The requested convincing documentary-cinematic
quality target is not met.** The remaining visual work below is material, not a
claim that a polished vertical slice has been completed.

The catalog's `approved` status denotes reviewed, reusable **bootstrap preview**
assets. It does not denote final cinematic approval. Preflight `ready` is a logical
asset-resolution result; it is not a visual-quality certificate.

## Actual execution and evidence

Executed locally in the repository:

- Installed Blender **5.2.1 LTS**, build `9e2066aef7ef`: creation, saved-source
  revisions, animation authoring, validation and actual GLB exports.
- `python3 -m unittest discover -s tests -v`: **11 tests pass**.
- `python3 pipeline/preflight.py scenarios/raptor_hunt_001/scenario.json`: **ready**,
  15 required IDs resolved, no missing assets, 10 instances.
- `python3 pipeline/export_web_bundle.py scenarios/raptor_hunt_001/scenario.json`:
  execution plan and manifest exported.
- `npm install`, `npm run build`, Vite dev server and installed Google Chrome:
  actual browser execution. Build passes with the existing large-chunk advisory.
- Multiple `npm run capture:preview` runs: seven shot PNGs on every completed run.
- `npm run verify:assets`: all ten actors are real skinned meshes; environment
  placeholder is hidden; each of eleven named clips resolves correctly and moves
  sampled skinned vertices through the existing AnimationMixer; repeat seeks match
  actor state and canvas pixels; pack/prey clearance check passes; no browser errors.

Evidence is local under `build/preview/`:

- `baseline/`: original placeholder scene, inspected before authoring.
- `iteration_1/`: first real-GLB captures.
- `raptor_hunt_001/shot_001.png` through `shot_007.png`: final shot previews.
- `raptor_hunt_001/contact_sheet.jpg`: reviewed overview.
- `asset_qa/anim_*_a.png`, `anim_*_b.png`: individual clip pose pairs.
- `asset_qa/time_*.png`: action onset/transition checks in the actual scenario.
- `asset_qa/verification.json`: browser assertions and measured deformation.
- `asset_qa/asset_receipts.json`: final GLB sizes, clip lists and SHA-256 hashes.
- `final-tests.log`, `final-preflight.json`, `final-build.log`: command results.

No concept image or Blender still was substituted for browser output. Numeric
skin checks missed a failed welding experiment; image inspection caught it and
the intact source revision was restored. Failed source experiments are preserved
separately and are not the current exported masters. Final jaw repair transfers
weights from the original source, corrects jaw pitch, and restores independently
skinned mandibles; bite/roar pose pairs were recaptured and inspected.

## Delivered reusable files

| Logical master | Editable source | Browser GLB size |
|---|---|---:|
| `dino_velociraptor_master` | `blender/dinosaurs/velociraptor/velociraptor_master.blend` | 2.56 MB |
| `dino_trex_master` | `blender/dinosaurs/trex/trex_master.blend` | 2.37 MB |
| `dino_triceratops_master` | `blender/dinosaurs/triceratops/triceratops_master.blend` | 2.53 MB |
| `env_tropical_rainforest` | `blender/environments/tropical_rainforest.blend` | 31.57 MB |

Dinosaur GLBs are under `web/public/assets/dinosaurs/`; the environment is under
`web/public/assets/environments/`. Original skin albedo textures are packed into
the sources and GLBs. Each master retains its species skeleton and actions.

Embedded clip registrations:

- Raptor: `anim_raptor_stalk`, `anim_raptor_run`, `anim_raptor_attack`,
  `anim_raptor_react`, `anim_raptor_flee`.
- T-Rex: `anim_trex_walk`, `anim_trex_roar`, `anim_trex_attack`.
- Triceratops: `anim_triceratops_graze`, `anim_triceratops_run`,
  `anim_triceratops_defend`.

Locomotion is in place; runtime steering owns translation. Foot-target authoring
improves straight locomotion. Turns/stops and quadruped front-limb contact still
need refinement. The raptor flee/run clips intentionally reuse a locomotion
family, while the reaction and attack poses differ. The pack still shares clip
phase, so it is too synchronized.

Environment source contains editable tree/root/branch modules, foliage/fern
layers, grass, rocks, fallen logs, puddles and a broad flat migration corridor.
Runtime export batches by material and reduces foliage geometry in an export
copy; source detail is retained. An intermediate 101 MB export was reduced to
31.57 MB. There is no runtime LOD or vegetation instancing implementation in this
revision. This is still a substantial asset for slower devices.

## Bounded runtime fixes and reproduction

1. **Shadow rectangle and self-shadow artifacts.** Baseline and initial GLB images
   show the default directional-light shadow footprint cutting across the ground.
   Expanded its metre-scale bounds, set 2048 shadow resolution, normal/depth bias
   and soft PCF filtering. Recaptured images verify removal of the rectangle.
   Shadows remain origin-centred; distant movement can leave coverage.
2. **Pack approach intersects differently sized real targets.** Existing attack
   slots used a fixed 1.5 m radius regardless of GLB dimensions. Actual captures
   showed the pack inside the Triceratops body area. Clearance now derives from
   each loaded master's horizontal bounds and informs slots/stopping distance.
   Existing overlaps are resolved gradually on state changes. The browser check
   asserts all eight pack members meet target clearance at 31 seconds. This is
   conservative body spacing, not full mesh collision or guaranteed tail clearance.
3. **Preview images contained the UI panel.** Screenshotting the canvas element's
   screen rectangle included the overlaid controls. Capture now writes the PNG
   from the existing `captureDataUrl()` API. The runtime UI is unchanged.

No runtime replacement, LLM render-loop calls, schema change, spawn rewrite or
Unreal dependency was introduced. Seven lens values changed in scenario data;
shot starts, durations, action offsets and the 180-second timeline are preserved.

## Visual review and remaining work

All seven final shot frames and the eleven clip pose pairs were inspected.

| Area | Assessment | Remaining correction |
|---|---|---|
| Anatomy/silhouette | Species distinguishable; proportions remain stylized | Sculpt skulls, hips, feet and oral anatomy on current masters; improve feather coverage and eye integration |
| Surface/topology | Closed bodies restored; primitive transitions and bridge seams visible | Retopologize joint and tail insertions with continuous deformation edge loops; bake normal/roughness maps |
| Motion | All clips move; jaw/neck/leg changes visible | Refine weight transfer, turn/stop foot contact, quadruped front legs, attack recovery and pack phase variation |
| Spacing | Body clearance improved and checked | Tail/head/limb intersections and crowding remain possible; validate throughout pursuit, not just sampled moments |
| Environment | Forest layers, clearing, wet ground and clutter present | Improve canopy structure and near-ground detail; grassland transition is too weak; puddles and leaves remain simple |
| Atmosphere | Fog is strong; rain particles present | Heavy rain reads weakly as sparse points; distant shots lose subject contrast |
| Composition | Wider lenses retain more context | Shot 2 still crops the prey; establishing/late telephoto shots are too foggy; prey and pack are often absent in later predator shots |
| Editing/behavior | Original plan executes without manual rebuilding | Short one-shots settle into held poses during long shots; original 60–125 second camera gap remains |
| Performance | Browser capture succeeds | No certified realtime FPS target, mobile budget, LOD or final 4K video validation |

### Per-shot cinematic verdict

- `shot_001`: **fail final visual bar** — geography visible, but aerial fog suppresses
  contrast and the opening lacks a convincing rainforest canopy.
- `shot_002`: **fail** — stalk animation is readable; prey crop and pack synchronization
  undermine observational composition.
- `shot_003`: **fail** — horns/frill and surrounding pack are readable; static poses,
  joint seams and remaining appendage overlap are conspicuous.
- `shot_004`: **fail** — pursuit runs with animated rigs; locomotion/contact and
  transition into distinct grassland need work.
- `shot_005`: **fail** — T-Rex reveal and early roar frames work technically; simplified
  anatomy, material response and vegetation remain stylized.
- `shot_006`: **fail** — predator remains framed; the short attack has ended by the
  midpoint, leaving an unconvincing moving/held pose and weak interaction geography.
- `shot_007`: **fail** — long-lens atmosphere works as a rough preview; fog and the
  held post-roar pose do not meet the cinematic target.

The assets are useful for continued local visual development. They should not be
presented as a finished documentary, a paleontologically validated reconstruction,
or a final production-quality animation library.
