from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "config" / "asset_catalog.json"
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "blocking": 3}
AGENT_CATEGORIES = {
    "asset_designer": {"anatomy", "material", "continuity"},
    "animation_director": {"animation", "continuity"},
    "environment_designer": {"environment", "lighting", "continuity"},
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(asset["id"]): asset
        for asset in catalog.get("assets", [])
        if isinstance(asset, dict) and asset.get("id")
    }


def infer_agent(asset_id: str) -> str:
    if asset_id.startswith("anim_"):
        return "animation_director"
    if asset_id.startswith("env_") or asset_id.startswith("weather_"):
        return "environment_designer"
    return "asset_designer"


def task_for(asset_id: str, agent: str) -> str:
    if asset_id.startswith("anim_") or agent == "animation_director":
        return "refine_animation"
    if asset_id.startswith("env_") or agent == "environment_designer":
        return "refine_environment"
    if asset_id.startswith("dino_"):
        return "refine_dinosaur_master"
    if asset_id.startswith("prop_"):
        return "refine_prop"
    return "refine_reusable_asset"


def max_severity(values: list[str], default: str = "high") -> str:
    valid = [value for value in values if value in SEVERITY_RANK]
    if not valid:
        return default
    return max(valid, key=lambda value: SEVERITY_RANK[value])


def inferred_request_severity(
    request: dict[str, Any],
    issues: list[dict[str, Any]],
    agent: str,
) -> str:
    explicit = str(request.get("severity", "")).lower()
    if explicit in SEVERITY_RANK:
        return explicit

    categories = AGENT_CATEGORIES.get(agent, set())
    related = [
        str(issue.get("severity", "")).lower()
        for issue in issues
        if str(issue.get("category", "")).lower() in categories
    ]
    return max_severity(related, default="high")


def stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return output


def asset_context(asset: dict[str, Any] | None) -> dict[str, Any] | None:
    if asset is None:
        return None
    keys = (
        "id",
        "type",
        "status",
        "blender_source",
        "export_path",
        "web_path",
        "skeleton_id",
        "species",
        "notes",
    )
    return {key: asset.get(key) for key in keys if key in asset}


def validate_shot(scenario: dict[str, Any], critique: dict[str, Any]) -> str:
    shot_id = str(critique.get("shot_id", "")).strip()
    if not shot_id:
        raise ValueError("Critique result is missing shot_id")
    valid_shots = {str(shot.get("id")) for shot in scenario.get("shots", [])}
    if shot_id not in valid_shots:
        raise ValueError(f"Critique references unknown shot id: {shot_id}")
    return shot_id


def route_critique(
    scenario: dict[str, Any],
    critique: dict[str, Any],
    catalog: dict[str, Any],
    *,
    allow_unregistered_assets: bool = False,
    source_critique: str | None = None,
) -> dict[str, Any]:
    scenario_id = str(scenario.get("scenario_id", "scenario"))
    shot_id = validate_shot(scenario, critique)
    issues = [item for item in critique.get("issues", []) if isinstance(item, dict)]
    patches = [item for item in critique.get("patches", []) if isinstance(item, dict)]
    agent_items = [item for item in critique.get("requires_agent", []) if isinstance(item, dict)]
    assets = catalog_index(catalog)

    deterministic_patches: list[dict[str, Any]] = []
    for index, patch in enumerate(patches, start=1):
        path = str(patch.get("path", "")).strip()
        operation = str(patch.get("operation", "")).strip()
        if not path or not operation:
            raise ValueError(f"Invalid deterministic patch at index {index}: path and operation are required")
        deterministic_patches.append(
            {
                "patch_id": f"{scenario_id}__{shot_id}__patch_{index:03d}",
                "shot_id": shot_id,
                "status": "pending",
                "path": path,
                "operation": operation,
                "value": patch.get("value"),
                "reason": str(patch.get("reason", "")).strip(),
                "source": "visual_critique",
            }
        )

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for index, item in enumerate(agent_items, start=1):
        asset_id = str(item.get("asset_id", "")).strip()
        if not asset_id:
            raise ValueError(f"Invalid requires_agent item at index {index}: asset_id is required")
        agent = str(item.get("agent", "")).strip() or infer_agent(asset_id)
        if agent not in {"asset_designer", "animation_director", "environment_designer"}:
            raise ValueError(f"Unsupported agent '{agent}' for {asset_id}")

        asset = assets.get(asset_id)
        if asset is None and not allow_unregistered_assets:
            raise ValueError(
                f"Critique requested unregistered asset '{asset_id}'. "
                "Register it first or rerun with --allow-unregistered-assets for intentional new work."
            )

        key = (agent, asset_id)
        group = grouped.setdefault(
            key,
            {
                "request_id": f"{scenario_id}__{shot_id}__{agent}__{asset_id}",
                "scenario_id": scenario_id,
                "shot_id": shot_id,
                "agent": agent,
                "task": task_for(asset_id, agent),
                "asset_id": asset_id,
                "priority": "low",
                "reasons": [],
                "acceptance_criteria": [],
                "asset": asset_context(asset),
                "required_context": [
                    "AGENTS.md",
                    f"agents/{agent.replace('_', '-')}.md",
                    "config/asset_catalog.json",
                    "docs/VISUAL_CRITIQUE_WORKFLOW.md",
                    "docs/CRITIQUE_ROUTING.md",
                ],
                "completion_contract": {
                    "preserve_logical_asset_id": True,
                    "edit_reusable_source_when_registered": asset is not None,
                    "export_registered_runtime_asset": asset is not None,
                    "verify_same_shot_after_change": True,
                    "rebuild_visual_critique_package": True,
                    "never_use_flux_frame_as_final_video": True,
                },
            },
        )

        reason = str(item.get("reason", "")).strip()
        if reason:
            group["reasons"].append(reason)
        criteria = item.get("acceptance_criteria", [])
        if isinstance(criteria, list):
            group["acceptance_criteria"].extend(str(value) for value in criteria)

        severity = inferred_request_severity(item, issues, agent)
        if SEVERITY_RANK[severity] > SEVERITY_RANK[str(group["priority"])]:
            group["priority"] = severity

    work_requests: list[dict[str, Any]] = []
    for key in sorted(grouped):
        request = grouped[key]
        request["reasons"] = stable_unique(request["reasons"])
        request["acceptance_criteria"] = stable_unique(request["acceptance_criteria"])
        if not request["acceptance_criteria"]:
            request["acceptance_criteria"] = [
                f"The reported defect for {request['asset_id']} is no longer visible in a repeat capture of {shot_id}."
            ]
        work_requests.append(request)

    return {
        "schema_version": 1,
        "scenario_id": scenario_id,
        "shot_id": shot_id,
        "critique_pass": bool(critique.get("pass", False)),
        "source_critique": source_critique,
        "issue_count": len(issues),
        "deterministic_patch_count": len(deterministic_patches),
        "work_request_count": len(work_requests),
        "deterministic_patches": deterministic_patches,
        "work_requests": work_requests,
    }


def request_markdown(request: dict[str, Any], source_critique: str | None) -> str:
    asset = request.get("asset") or {}
    lines = [
        f"# Astra work request: {request['asset_id']}",
        "",
        f"- request_id: `{request['request_id']}`",
        f"- agent: `{request['agent']}`",
        f"- task: `{request['task']}`",
        f"- priority: `{request['priority']}`",
        f"- scenario: `{request['scenario_id']}`",
        f"- shot: `{request['shot_id']}`",
    ]
    if source_critique:
        lines.append(f"- source critique: `{source_critique}`")
    if asset.get("blender_source"):
        lines.append(f"- Blender source: `{asset['blender_source']}`")
    if asset.get("export_path"):
        lines.append(f"- runtime export: `{asset['export_path']}`")

    lines.extend(["", "## Why this work exists", ""])
    for reason in request.get("reasons", []):
        lines.append(f"- {reason}")

    lines.extend(["", "## Acceptance criteria", ""])
    for criterion in request.get("acceptance_criteria", []):
        lines.append(f"- {criterion}")

    lines.extend(
        [
            "",
            "## Execution rules",
            "",
            "- Fix the reusable registered asset rather than making a one-shot visual hack.",
            "- Preserve scenario semantics, actor count and deterministic staging.",
            "- Use the FLUX image only as a visual-quality reference; do not reproduce its hallucinated composition or actors.",
            "- Export/register the runtime asset using the existing catalog contract.",
            f"- Recapture `{request['shot_id']}` and rebuild its critique package after the change.",
            "- Do not mark complete until the acceptance criteria are visually verified in the real render/preview.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(result: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    requests_dir = output_dir / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)

    routing_path = output_dir / "routing.json"
    patches_path = output_dir / "deterministic_patches.json"
    requests_path = output_dir / "work_requests.json"

    routing_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    patches_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scenario_id": result["scenario_id"],
                "shot_id": result["shot_id"],
                "patches": result["deterministic_patches"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    requests_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scenario_id": result["scenario_id"],
                "shot_id": result["shot_id"],
                "requests": result["work_requests"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    for request in result["work_requests"]:
        path = requests_dir / f"{request['request_id']}.md"
        path.write_text(request_markdown(request, result.get("source_critique")), encoding="utf-8")

    return {
        "routing": routing_path,
        "patches": patches_path,
        "work_requests": requests_path,
        "requests_dir": requests_dir,
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Route a visual-critic result into deterministic patch work and reusable Astra/agent work requests. "
            "This command never applies patches or edits Blender assets itself."
        )
    )
    p.add_argument("scenario", type=Path, help="Scenario JSON path")
    p.add_argument("critique_result", type=Path, help="Visual critic result JSON")
    p.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--allow-unregistered-assets", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        scenario_path = args.scenario.resolve()
        critique_path = args.critique_result.resolve()
        catalog_path = args.catalog.resolve()
        scenario = load_json(scenario_path)
        critique = load_json(critique_path)
        catalog = load_json(catalog_path)
        scenario_id = str(scenario.get("scenario_id", scenario_path.stem))
        shot_id = validate_shot(scenario, critique)
        output_dir = (
            args.output_dir.resolve()
            if args.output_dir
            else (ROOT / "build" / "work" / scenario_id / shot_id).resolve()
        )

        result = route_critique(
            scenario,
            critique,
            catalog,
            allow_unregistered_assets=args.allow_unregistered_assets,
            source_critique=str(critique_path),
        )
        paths = write_outputs(result, output_dir)
        print(f"WROTE {paths['routing']}")
        print(f"WROTE {paths['patches']}")
        print(f"WROTE {paths['work_requests']}")
        print(f"WROTE {result['work_request_count']} Astra request(s) under {paths['requests_dir']}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
