from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    from pipeline.build_visual_critique_package import build_package, find_shot
    from pipeline.route_visual_critique import (
        DEFAULT_CATALOG,
        SEVERITY_RANK,
        load_json,
        route_critique,
        validate_shot,
        write_outputs,
    )
except ModuleNotFoundError:  # Direct `python pipeline/...py` execution.
    from build_visual_critique_package import build_package, find_shot
    from route_visual_critique import (
        DEFAULT_CATALOG,
        SEVERITY_RANK,
        load_json,
        route_critique,
        validate_shot,
        write_outputs,
    )


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
SEVERITY_WEIGHT = {"low": 1, "medium": 4, "high": 16, "blocking": 64}
TERMINAL_STATUSES = {"pass", "continue", "blocked"}


def command_text(command: Sequence[str]) -> str:
    return " ".join(str(part) for part in command)


def run_command(command: list[str], *, cwd: Path, dry_run: bool = False) -> None:
    print(f"RUN [{cwd}]: {command_text(command)}")
    if dry_run:
        return
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {command_text(command)}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_receipt(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256_file(path),
    }


def copy_with_receipt(source: Path, destination: Path) -> dict[str, Any] | None:
    receipt = file_receipt(source)
    if receipt is None:
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    receipt["snapshot"] = str(destination.resolve())
    return receipt


def git_head() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def iteration_root(scenario_id: str, shot_id: str) -> Path:
    return ROOT / "build" / "iterations" / scenario_id / shot_id


def iteration_number(path: Path) -> int | None:
    if not path.name.startswith("iteration_"):
        return None
    try:
        return int(path.name.split("_", 1)[1])
    except ValueError:
        return None


def next_iteration_dir(root: Path) -> Path:
    numbers = [iteration_number(path) for path in root.glob("iteration_*") if path.is_dir()]
    valid = [number for number in numbers if number is not None]
    number = (max(valid) + 1) if valid else 1
    return root / f"iteration_{number:03d}"


def manifest_path(iteration_dir: Path) -> Path:
    return iteration_dir / "iteration.json"


def read_manifest(iteration_dir: Path) -> dict[str, Any]:
    path = manifest_path(iteration_dir)
    if not path.exists():
        raise FileNotFoundError(f"Missing iteration manifest: {path}")
    return load_json(path)


def write_manifest(iteration_dir: Path, manifest: dict[str, Any]) -> None:
    iteration_dir.mkdir(parents=True, exist_ok=True)
    manifest_path(iteration_dir).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def find_active_iteration(root: Path) -> Path:
    candidates: list[tuple[int, Path]] = []
    for path in root.glob("iteration_*"):
        if not path.is_dir():
            continue
        number = iteration_number(path)
        if number is None or not manifest_path(path).exists():
            continue
        manifest = read_manifest(path)
        status = str(manifest.get("status", ""))
        if status not in TERMINAL_STATUSES:
            candidates.append((number, path))
    if not candidates:
        raise FileNotFoundError(f"No active visual iteration under {root}")
    return max(candidates)[1]


def severity_counts(critique: dict[str, Any]) -> dict[str, int]:
    counts = {severity: 0 for severity in SEVERITY_WEIGHT}
    for issue in critique.get("issues", []):
        if not isinstance(issue, dict):
            continue
        severity = str(issue.get("severity", "")).lower()
        if severity in counts:
            counts[severity] += 1
    return counts


def critique_summary(critique: dict[str, Any] | None) -> dict[str, Any] | None:
    if critique is None:
        return None
    counts = severity_counts(critique)
    issue_score = sum(SEVERITY_WEIGHT[key] * value for key, value in counts.items())
    patches = [value for value in critique.get("patches", []) if isinstance(value, dict)]
    agent_work = [value for value in critique.get("requires_agent", []) if isinstance(value, dict)]
    return {
        "pass_claim": bool(critique.get("pass", False)),
        "issue_count": sum(counts.values()),
        "severity_counts": counts,
        "issue_score": issue_score,
        "patch_count": len(patches),
        "requires_agent_count": len(agent_work),
        "quality_score": issue_score + len(patches) + len(agent_work),
    }


def routing_summary(routing: dict[str, Any]) -> dict[str, Any]:
    priorities = {severity: 0 for severity in SEVERITY_WEIGHT}
    for request in routing.get("work_requests", []):
        if not isinstance(request, dict):
            continue
        priority = str(request.get("priority", "")).lower()
        if priority in priorities:
            priorities[priority] += 1
    return {
        "deterministic_patch_count": int(routing.get("deterministic_patch_count", 0)),
        "work_request_count": int(routing.get("work_request_count", 0)),
        "work_request_priorities": priorities,
    }


def decide_iteration(
    critique: dict[str, Any],
    routing: dict[str, Any],
    before_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    after = critique_summary(critique)
    assert after is not None
    route = routing_summary(routing)

    blocking = after["severity_counts"]["blocking"] > 0 or route["work_request_priorities"]["blocking"] > 0
    high = after["severity_counts"]["high"] > 0 or route["work_request_priorities"]["high"] > 0
    unresolved = route["deterministic_patch_count"] > 0 or route["work_request_count"] > 0

    if blocking:
        state = "BLOCKED"
        reason = "At least one blocking visual issue or blocking routed work request remains."
    elif bool(critique.get("pass", False)) and not high and not unresolved:
        state = "PASS"
        reason = "Critic passed the shot and no high/blocking issue, deterministic patch, or agent work remains."
    else:
        state = "CONTINUE"
        reason = "The shot still has unresolved visual work or has not met the pass contract."

    trend = "unknown"
    quality_delta: int | None = None
    if before_summary is not None:
        quality_delta = int(after["quality_score"]) - int(before_summary["quality_score"])
        if quality_delta < 0:
            trend = "improved"
        elif quality_delta > 0:
            trend = "regressed"
        else:
            trend = "unchanged"

    return {
        "state": state,
        "reason": reason,
        "trend": trend,
        "quality_delta": quality_delta,
        "before": before_summary,
        "after": after,
        "routing": route,
    }


def catalog_assets(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(asset.get("id")): asset
        for asset in catalog.get("assets", [])
        if isinstance(asset, dict) and asset.get("id")
    }


def current_work_asset_ids(work_dir: Path) -> list[str]:
    requests = work_dir / "work_requests.json"
    if not requests.exists():
        return []
    data = load_json(requests)
    return sorted(
        {
            str(request.get("asset_id"))
            for request in data.get("requests", [])
            if isinstance(request, dict) and request.get("asset_id")
        }
    )


def asset_receipts(catalog: dict[str, Any], asset_ids: list[str]) -> dict[str, Any]:
    assets = catalog_assets(catalog)
    output: dict[str, Any] = {}
    for asset_id in asset_ids:
        asset = assets.get(asset_id)
        if asset is None:
            continue
        entry: dict[str, Any] = {"asset_id": asset_id}
        for key in ("blender_source", "export_path"):
            value = asset.get(key)
            if value:
                entry[key] = file_receipt(ROOT / str(value))
        output[asset_id] = entry
    return output


def changed_assets(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    for asset_id in sorted(set(before) | set(after)):
        old = before.get(asset_id, {})
        new = after.get(asset_id, {})
        keys = ("blender_source", "export_path")
        if any((old.get(key) or {}).get("sha256") != (new.get(key) or {}).get("sha256") for key in keys):
            changed.append(asset_id)
    return changed


def canonical_paths(scenario_id: str, shot_id: str) -> dict[str, Path]:
    critique = ROOT / "build" / "critique" / scenario_id
    work = ROOT / "build" / "work" / scenario_id / shot_id
    return {
        "preview": ROOT / "build" / "preview" / scenario_id / f"{shot_id}.png",
        "lookdev": ROOT / "build" / "lookdev" / scenario_id / f"{shot_id}.png",
        "package": critique / f"{shot_id}.json",
        "request": critique / f"{shot_id}.request.md",
        "result": critique / f"{shot_id}.result.json",
        "execution": critique / f"{shot_id}.execution.json",
        "work": work,
        "routing": work / "routing.json",
        "patches": work / "deterministic_patches.json",
        "work_requests": work / "work_requests.json",
    }


def start_iteration(
    scenario: dict[str, Any],
    shot_id: str,
    catalog: dict[str, Any],
) -> Path:
    scenario_id = str(scenario.get("scenario_id", "scenario"))
    root = iteration_root(scenario_id, shot_id)
    root.mkdir(parents=True, exist_ok=True)

    # Do not allow overlapping iterations for the same shot.
    try:
        active = find_active_iteration(root)
    except FileNotFoundError:
        active = None
    if active is not None:
        raise RuntimeError(f"Active iteration already exists: {active}")

    iteration_dir = next_iteration_dir(root)
    before_dir = iteration_dir / "before"
    paths = canonical_paths(scenario_id, shot_id)

    receipts: dict[str, Any] = {}
    snapshot_map = {
        "preview": (paths["preview"], before_dir / "preview.png"),
        "lookdev": (paths["lookdev"], before_dir / "lookdev.png"),
        "critique_package": (paths["package"], before_dir / "critique.package.json"),
        "critique_request": (paths["request"], before_dir / "critique.request.md"),
        "critique_result": (paths["result"], before_dir / "critique.result.json"),
        "execution": (paths["execution"], before_dir / "execution.json"),
        "routing": (paths["routing"], before_dir / "routing.json"),
        "patches": (paths["patches"], before_dir / "deterministic_patches.json"),
        "work_requests": (paths["work_requests"], before_dir / "work_requests.json"),
    }
    for name, (source, destination) in snapshot_map.items():
        receipt = copy_with_receipt(source, destination)
        if receipt is not None:
            receipts[name] = receipt

    before_critique = load_json(paths["result"]) if paths["result"].exists() else None
    asset_ids = current_work_asset_ids(paths["work"])
    assets_before = asset_receipts(catalog, asset_ids)

    manifest = {
        "schema_version": 1,
        "scenario_id": scenario_id,
        "shot_id": shot_id,
        "iteration": iteration_number(iteration_dir),
        "status": "started",
        "git_head_start": git_head(),
        "before": {
            "receipts": receipts,
            "critique_summary": critique_summary(before_critique),
            "target_asset_ids": asset_ids,
            "asset_receipts": assets_before,
        },
        "after": None,
        "decision": None,
    }
    write_manifest(iteration_dir, manifest)
    print(f"ITERATION STARTED: {iteration_dir}")
    return iteration_dir


def capture_iteration(
    scenario_path: Path,
    scenario: dict[str, Any],
    shot_id: str,
    catalog: dict[str, Any],
    *,
    skip_export: bool,
    skip_web_build: bool,
    skip_capture: bool,
    allow_missing_lookdev: bool,
    dry_run: bool,
) -> Path:
    scenario_id = str(scenario.get("scenario_id", scenario_path.stem))
    root = iteration_root(scenario_id, shot_id)
    iteration_dir = find_active_iteration(root)
    manifest = read_manifest(iteration_dir)
    if manifest.get("status") not in {"started", "captured"}:
        raise RuntimeError(f"Iteration is not ready for capture: {manifest.get('status')}")

    if not skip_export:
        run_command(
            [sys.executable, str(ROOT / "pipeline" / "export_web_bundle.py"), str(scenario_path)],
            cwd=ROOT,
            dry_run=dry_run,
        )
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    if not skip_web_build:
        if shutil.which(npm) is None:
            raise RuntimeError("npm executable was not found in PATH")
        run_command([npm, "run", "build"], cwd=WEB_ROOT, dry_run=dry_run)
    if not skip_capture:
        if shutil.which(npm) is None:
            raise RuntimeError("npm executable was not found in PATH")
        run_command([npm, "run", "capture:preview"], cwd=WEB_ROOT, dry_run=dry_run)

    if dry_run:
        print(f"DRY-RUN capture complete for {iteration_dir}")
        return iteration_dir

    paths = canonical_paths(scenario_id, shot_id)
    shot = find_shot(scenario, shot_id)
    package_path, request_path = build_package(
        scenario,
        shot,
        preview_dir=paths["preview"].parent,
        lookdev_dir=paths["lookdev"].parent,
        output_dir=paths["package"].parent,
        allow_missing_lookdev=allow_missing_lookdev,
    )

    after_dir = iteration_dir / "after"
    receipts: dict[str, Any] = {}
    for name, source, destination in (
        ("preview", paths["preview"], after_dir / "preview.png"),
        ("lookdev", paths["lookdev"], after_dir / "lookdev.png"),
        ("critique_package", package_path, after_dir / "critique.package.json"),
        ("critique_request", request_path, after_dir / "critique.request.md"),
    ):
        receipt = copy_with_receipt(source, destination)
        if receipt is not None:
            receipts[name] = receipt

    before_assets = manifest.get("before", {}).get("asset_receipts", {}) or {}
    target_asset_ids = list(manifest.get("before", {}).get("target_asset_ids", []) or [])
    after_assets = asset_receipts(catalog, target_asset_ids)
    changed = changed_assets(before_assets, after_assets)

    manifest["status"] = "awaiting_critique"
    manifest["git_head_capture"] = git_head()
    manifest["after"] = {
        "receipts": receipts,
        "asset_receipts": after_assets,
        "changed_assets": changed,
        "result_expected_at": str(paths["result"].resolve()),
    }
    write_manifest(iteration_dir, manifest)
    print(f"ITERATION CAPTURED: {iteration_dir}")
    print(f"CRITIQUE RESULT REQUIRED: {paths['result']}")
    return iteration_dir


def next_action_markdown(decision: dict[str, Any], work_dir: Path) -> str:
    state = decision["state"]
    lines = [
        f"# Visual iteration decision: {state}",
        "",
        decision["reason"],
        "",
        f"Trend: `{decision['trend']}`",
    ]
    if decision.get("quality_delta") is not None:
        lines.append(f"Quality-score delta: `{decision['quality_delta']}` (negative is improvement)")

    if state == "PASS":
        lines.extend(["", "No routed visual work remains for this shot under the current critic contract."])
    else:
        lines.extend(["", "## Next work", ""])
        requests_dir = work_dir / "requests"
        request_paths = sorted(requests_dir.glob("*.md")) if requests_dir.exists() else []
        if request_paths:
            lines.append("Execute the highest-priority routed request first:")
            for path in request_paths:
                lines.append(f"- `{path}`")
        patches = work_dir / "deterministic_patches.json"
        if patches.exists():
            data = load_json(patches)
            if data.get("patches"):
                lines.append(f"- Review deterministic patches in `{patches}`")
        lines.extend(
            [
                "",
                "Before editing the next reusable asset, start a new iteration with `run_visual_iteration.py ... start`.",
            ]
        )
    return "\n".join(lines) + "\n"


def finalize_iteration(
    scenario_path: Path,
    scenario: dict[str, Any],
    shot_id: str,
    catalog: dict[str, Any],
    *,
    allow_unregistered_assets: bool,
    allow_unchanged_result: bool,
) -> Path:
    scenario_id = str(scenario.get("scenario_id", scenario_path.stem))
    root = iteration_root(scenario_id, shot_id)
    iteration_dir = find_active_iteration(root)
    manifest = read_manifest(iteration_dir)
    if manifest.get("status") != "awaiting_critique":
        raise RuntimeError(f"Iteration is not awaiting critique: {manifest.get('status')}")

    paths = canonical_paths(scenario_id, shot_id)
    if not paths["result"].exists():
        raise FileNotFoundError(f"Missing updated visual critic result: {paths['result']}")

    result_receipt = file_receipt(paths["result"])
    assert result_receipt is not None
    before_result = manifest.get("before", {}).get("receipts", {}).get("critique_result")
    if (
        before_result
        and before_result.get("sha256") == result_receipt.get("sha256")
        and not allow_unchanged_result
    ):
        raise RuntimeError(
            "Critique result is byte-identical to the result captured at iteration start. "
            "Run the visual critic on the new preview first, or use --allow-unchanged-result intentionally."
        )

    critique = load_json(paths["result"])
    validate_shot(scenario, critique)
    routing = route_critique(
        scenario,
        critique,
        catalog,
        allow_unregistered_assets=allow_unregistered_assets,
        source_critique=str(paths["result"].resolve()),
    )

    # Refresh canonical routed work and preserve an immutable iteration copy.
    write_outputs(routing, paths["work"])
    final_dir = iteration_dir / "final"
    iteration_work = final_dir / "work"
    write_outputs(routing, iteration_work)
    copy_with_receipt(paths["result"], final_dir / "critique.result.json")
    copy_with_receipt(paths["execution"], final_dir / "execution.json")

    before_summary = manifest.get("before", {}).get("critique_summary")
    decision = decide_iteration(critique, routing, before_summary)
    decision_path = iteration_dir / "decision.json"
    decision_path.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    (iteration_dir / "NEXT_ACTION.md").write_text(next_action_markdown(decision, paths["work"]), encoding="utf-8")

    manifest["status"] = str(decision["state"]).lower()
    manifest["git_head_finalize"] = git_head()
    manifest["after"]["critique_result"] = result_receipt
    manifest["decision"] = decision
    write_manifest(iteration_dir, manifest)

    print(f"ITERATION {decision['state']}: {iteration_dir}")
    print(f"TREND: {decision['trend']}")
    print(f"NEXT ACTION: {iteration_dir / 'NEXT_ACTION.md'}")
    return iteration_dir


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Manage repeatable visual-improvement iterations around Astra/Blender work. "
            "Use start before editing, capture after editing/export, and finalize after the visual critic writes a new result."
        )
    )
    p.add_argument("scenario", type=Path, help="Scenario JSON path")
    p.add_argument("phase", choices=("start", "capture", "finalize"))
    p.add_argument("--shot-id", required=True)
    p.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    p.add_argument("--skip-export", action="store_true", help="Capture phase: skip runtime bundle export.")
    p.add_argument("--skip-web-build", action="store_true", help="Capture phase: skip npm production build.")
    p.add_argument("--skip-capture", action="store_true", help="Capture phase: skip browser recapture.")
    p.add_argument("--allow-missing-lookdev", action="store_true")
    p.add_argument("--allow-unregistered-assets", action="store_true")
    p.add_argument("--allow-unchanged-result", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        scenario_path = args.scenario.resolve()
        catalog_path = args.catalog.resolve()
        scenario = load_json(scenario_path)
        catalog = load_json(catalog_path)
        find_shot(scenario, args.shot_id)

        if args.phase == "start":
            start_iteration(scenario, args.shot_id, catalog)
        elif args.phase == "capture":
            capture_iteration(
                scenario_path,
                scenario,
                args.shot_id,
                catalog,
                skip_export=args.skip_export,
                skip_web_build=args.skip_web_build,
                skip_capture=args.skip_capture,
                allow_missing_lookdev=args.allow_missing_lookdev,
                dry_run=args.dry_run,
            )
        else:
            finalize_iteration(
                scenario_path,
                scenario,
                args.shot_id,
                catalog,
                allow_unregistered_assets=args.allow_unregistered_assets,
                allow_unchanged_result=args.allow_unchanged_result,
            )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
