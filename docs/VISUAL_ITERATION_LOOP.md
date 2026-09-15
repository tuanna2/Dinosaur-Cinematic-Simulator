# Visual iteration state machine

`pipeline/run_visual_iteration.py` turns the previously manual Astra/Blender refinement cycle into a repeatable evidence-preserving workflow.

The command does not edit Blender assets or call an AI model. Astra still performs creative 3D work and visual criticism. The state machine owns snapshots, deterministic rebuild/capture, routing, quality trend calculation and PASS/CONTINUE/BLOCKED decisions.

## Why this exists

A visual fix should be judged against the exact evidence that triggered it. Without iteration snapshots it is easy to overwrite the previous preview/result, forget which work request was executed, or claim improvement without comparing the new critique against the old one.

Each iteration therefore preserves:

- the preview/look-dev/critique/result that existed before the edit
- the routed work that triggered the edit
- SHA-256 receipts for registered Blender sources and runtime exports targeted by current work requests
- the recaptured preview and rebuilt critique package after the edit
- the new visual-critic result and routed work
- a deterministic decision and quality-score delta

Generated iteration evidence lives under `build/iterations/` and remains local/ignored like other render artifacts.

## State machine

```text
existing critique + routed work
          |
          v
        START
  snapshot before state
          |
          v
   Astra edits Blender
   exports registered GLB
          |
          v
       CAPTURE
 export runtime bundle
 npm production build
 deterministic recapture
 rebuild critique package
          |
          v
  visual critic reviews
  writes new *.result.json
          |
          v
      FINALIZE
 route new critique
 compare old/new severity
          |
     +----+-----+
     |    |     |
    PASS CONTINUE BLOCKED
```

## 1. Start before editing

Before Astra changes the next registered asset:

```bash
python3 pipeline/run_visual_iteration.py \
  scenarios/raptor_hunt_001/scenario.json \
  start \
  --shot-id shot_005
```

This creates the next numbered directory, for example:

```text
build/iterations/raptor_hunt_001/shot_005/iteration_001/
```

The `before/` folder snapshots available evidence. `iteration.json` records the current Git HEAD, current critique summary, targeted logical asset IDs and SHA-256 receipts of their registered `.blend`/GLB files when present.

Only one non-terminal iteration may exist for the same shot.

## 2. Astra performs the routed work

Read the highest-priority request under:

```text
build/work/raptor_hunt_001/shot_005/requests/
```

Edit the registered reusable Blender source, not a shot-specific duplicate. Export the registered runtime asset as required by the work request.

Do not overwrite the old critique result yet; it is the baseline for the active iteration.

## 3. Capture after the edit

```bash
python3 pipeline/run_visual_iteration.py \
  scenarios/raptor_hunt_001/scenario.json \
  capture \
  --shot-id shot_005
```

By default this runs:

```text
export_web_bundle.py
npm run build
npm run capture:preview
build_visual_critique_package.py
```

The same existing FLUX look target is reused. A fresh FLUX image is unnecessary unless visual direction itself changed.

The command also records post-edit `.blend`/GLB receipts and which targeted assets actually changed.

Useful debugging options:

```text
--skip-export
--skip-web-build
--skip-capture
--allow-missing-lookdev
--dry-run
```

After capture the iteration status is `awaiting_critique`.

## 4. Visual critic writes a new result

Review the new authoritative preview and current critique package using `agents/visual-critic.md`.

Write the updated result to the canonical path:

```text
build/critique/raptor_hunt_001/shot_005.result.json
```

The state machine intentionally rejects a byte-identical result by default. This prevents accidentally finalizing an iteration with the old pre-edit critique. `--allow-unchanged-result` exists only for an intentional reviewed no-change conclusion.

## 5. Finalize and route

```bash
python3 pipeline/run_visual_iteration.py \
  scenarios/raptor_hunt_001/scenario.json \
  finalize \
  --shot-id shot_005
```

Finalize:

1. verifies the new critique belongs to the shot
2. routes deterministic patches and reusable agent work
3. refreshes canonical `build/work/...`
4. stores an immutable routed copy under the iteration
5. compares the new critique score with the pre-edit critique score
6. writes `decision.json` and `NEXT_ACTION.md`

## Decision contract

`PASS` requires all of the following:

- critic result has `pass: true`
- no high or blocking issue remains
- no deterministic patch remains
- no routed agent work remains

`BLOCKED` means at least one blocking issue or blocking work request remains. It does not mean tooling failed; it means final visual acceptance is blocked by an urgent defect.

Everything else is `CONTINUE`.

## Quality trend

The comparison is intentionally simple and deterministic:

```text
low      = 1
medium   = 4
high     = 16
blocking = 64
```

The critique quality score adds weighted issue severity plus pending patch/work counts. A lower new score is `improved`, a higher score is `regressed`, and an equal score is `unchanged`.

This is not a substitute for visual judgment. It is a guardrail that makes iteration history auditable.

## Iteration layout

```text
build/iterations/<scenario>/<shot>/iteration_001/
├── iteration.json
├── decision.json                 # after finalize
├── NEXT_ACTION.md                # after finalize
├── before/
│   ├── preview.png
│   ├── lookdev.png
│   ├── critique.package.json
│   ├── critique.request.md
│   ├── critique.result.json
│   ├── execution.json
│   ├── routing.json
│   ├── deterministic_patches.json
│   └── work_requests.json
├── after/
│   ├── preview.png
│   ├── lookdev.png
│   ├── critique.package.json
│   └── critique.request.md
└── final/
    ├── critique.result.json
    ├── execution.json
    └── work/
        ├── routing.json
        ├── deterministic_patches.json
        ├── work_requests.json
        └── requests/
```

## Recommended Astra behavior

For every routed reusable asset fix:

```text
run_visual_iteration.py ... start
        -> edit registered Blender source
        -> export registered GLB
run_visual_iteration.py ... capture
        -> inspect new preview/package
        -> write new critique result
run_visual_iteration.py ... finalize
        -> read NEXT_ACTION.md
```

If the decision is `CONTINUE` or `BLOCKED`, repeat with the highest-priority remaining routed request. Stop only at `PASS` or when a human intentionally changes the quality contract.
