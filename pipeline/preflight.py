#!/usr/bin/env python3
"""Run deterministic production preflight for a scenario.

Checks scenario validity, resolves required assets, compiles an Unreal-facing
execution plan, and writes a machine-readable report. Exit code is non-zero if
anything required is missing or invalid.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from pipeline.compile_execution_plan import compile_plan
    from pipeline.validate_scenario import load_json, validate
except ModuleNotFoundError:  # direct execution from pipeline/
    from compile_execution_plan import compile_plan
    from validate_scenario import load_json, validate


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def resolve_required(plan: dict[str, Any], catalog: dict[str, Any]) -> tuple[list[str], list[str]]:
    available = {
        item.get("id")
        for item in catalog.get("assets", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    required = set(plan["required_assets"])
    return sorted(required & available), sorted(required - available)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--catalog", type=Path, default=Path("config/asset_catalog.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("build/preflight"))
    args = parser.parse_args()

    try:
        scenario = load_json(args.scenario)
        validation_errors = validate(scenario)
        if validation_errors:
            report = {
                "status": "invalid_scenario",
                "scenario_id": scenario.get("scenario_id"),
                "errors": validation_errors,
            }
            plan = None
            exit_code = 2
        else:
            plan = compile_plan(scenario)
            catalog = _load(args.catalog)
            resolved, missing = resolve_required(plan, catalog)
            report = {
                "status": "ready" if not missing else "missing_assets",
                "scenario_id": scenario["scenario_id"],
                "resolved_assets": resolved,
                "missing_assets": missing,
                "instance_count": len(plan["instances"]),
                "event_count": len(plan["events"]),
            }
            exit_code = 0 if not missing else 1
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"PREFLIGHT FAILED: {exc}", file=sys.stderr)
        return 3

    scenario_dir = args.out_dir / str(report.get("scenario_id") or "unknown")
    scenario_dir.mkdir(parents=True, exist_ok=True)
    (scenario_dir / "preflight.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if plan is not None:
        (scenario_dir / "execution_plan.json").write_text(
            json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
