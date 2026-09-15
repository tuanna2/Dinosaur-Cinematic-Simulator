# Shot 005: routed structural revision

## Verdict

**Improved, still fails final visual quality.** The blocking structural request
was executed on the registered T-Rex candidate and is partially resolved. The
remaining thigh/skull shaping request stays high priority; environment work stays
behind it. No scenario, camera, runtime or FLUX image was modified.

## Executed loop

Read the critique package, request, schema and routing contracts; inspected both
Three.js and FLUX images. Saved `build/critique/raptor_hunt_001/shot_005.result.json`
and ran `pipeline/route_visual_critique.py`. Read both generated work requests and
executed the blocking T-Rex asset request first.

Blender 5.2.1 edited the exact catalog source:
`blender/dinosaurs/trex/trex_quality_candidate.blend`, preserving
`trex_quality_candidate_before_structural.blend` first. Existing thigh/neck vertices
were reshaped, exterior volumes fused, and original skeleton weights transferred.
The jaw and mouth accessories remain separately articulated. The continuous skin
has 75,968 vertices and zero nonmanifold edges. This is an intermediate structural
mesh; intentional joint edge flow remains unfinished.

First browser captures exposed dark seams from UV transfer. Re-unwrapping and
rebaking the existing procedural shader removed those seams in the next actual
capture. No decorative detail pass was added.

Exported the registered GLB, re-exported the runtime bundle, ran production build,
`capture:preview`, `capture:hero` and `verify:assets`. Inspected shot 005 at 131s,
hero stride/roar, attack pose and scenario samples at 125.6s and 131.7s. Rebuilt the
critique package with the same FLUX target, updated the result and rerouted the
remaining work.

## Acceptance evidence

| Criterion | Result |
|---|---|
| Same camera/staging at 131s | Preserved; single visible T-Rex, scenario/runtime untouched |
| Tail-root collar | No longer visible in reviewed repeat frame |
| Pale near-hip triangle | No longer visible in reviewed repeat frame |
| Thigh/knee and neck continuity | Improved; posterior thigh bulge and simplified anatomy remain |
| Skeleton and actions | Preserved; all 11 project clips resolve/deform in browser checks |
| New holes/detached limbs | None observed in inspected samples; full-cycle quality not certified |
| Final cinematic quality | Fail; anatomy and motion need further production work |

Python: 19 tests pass. Preflight: ready, 15 IDs, 10 actors, 21 events.
Web build passes with the large-bundle advisory. Browser QA reports matching repeat
seek states/pixels, sampled pack clearance passing and no browser errors.

Local artifacts (ignored by Git):

- `build/critique/raptor_hunt_001/structural_before/`: initial frame/result/routed requests.
- `build/critique/raptor_hunt_001/shot_005.result.json`: current critique.
- `build/critique/raptor_hunt_001/shot_005.execution.json`: criterion outcomes and SHA-256 receipts.
- `build/critique/raptor_hunt_001/structural-*-blender.log`: source edit/bake logs.
- `build/preview/raptor_hunt_001/shot_005.png`: reviewed final frame of this iteration.
- `build/work/raptor_hunt_001/shot_005/requests/`: current unresolved work.

FLUX was used only to judge realism, continuous body mass and environmental richness.
Its extra animals, front-facing composition, pose and invented details were not
adopted. A closed mouth at the exact 131s roar onset was not treated as a defect;
subsequent real frames confirm the existing animation opens it.
