#!/usr/bin/env python3
"""Convert deterministic preflight gaps into explicit AI-agent work requests.

This script does not call an AI model. It only classifies missing logical assets
and emits machine-readable requests that an orchestrator can hand to an agent
later.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def classify(asset_id: str) -> tuple[str, str]:
    if asset_id.startswith("anim_"):
        return "animation_director", "create_or_adapt_animation"
    if asset_id.startswith("dino_"):
        return "asset_designer", "create_dinosaur_master"
    if asset_id.startswith("env_"):
        return "environment_designer", "create_environment"
    if asset_id.startswith("prop_"):
        return "asset_designer", "create_prop"
    if asset_id.startswith("camera_"):
        return "camera_director", "create_camera_preset"
    if asset_id.startswith("weather_"):
        return "environment_designer", "create_weather_preset"
    return "asset_designer", "resolve_unknown_asset"


def build_requests(preflight: dict[str, Any]) -> list[dict[str, Any]]:
    scenario_id = preflight.get("scenario_id")
    requests: list[dict[str, Any]] = []
    for asset_id in sorted(set(preflight.get("missing_assets", []))):
        role, task = classify(asset_id)
        requests.append(
            {
                "request_id": f"{scenario_id}__{asset_id}",
                "scenario_id": scenario_id,
                "agent": role,
                "task": task,
                "asset_id": asset_id,
                "required_context": [
                    "AGENTS.md",
                    f"agents/{role.replace('_', '-')}.md",
                    "config/asset_catalog.json",
                    "docs/ARCHITECTURE.md",
                ],
                "completion_contract": {
                    "register_in_asset_catalog": True,
                    "preserve_logical_asset_id": True,
                    "must_be_reusable": True,
                },
            }
        )
    return requests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preflight", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    preflight = json.loads(args.preflight.read_text(encoding="utf-8"))
    requests = build_requests(preflight)
    result = {
        "scenario_id": preflight.get("scenario_id"),
        "request_count": len(requests),
        "requests": requests,
    }
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"WROTE: {args.output}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
