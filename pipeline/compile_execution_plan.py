#!/usr/bin/env python3
"""Compile a validated scenario into a deterministic execution plan.

The execution plan expands actor groups into stable instance IDs and converts
shots into explicit camera/action events. Unreal consumes this plan; an LLM is
not required at runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from pipeline.validate_scenario import load_json, validate
except ModuleNotFoundError:  # direct execution from pipeline/
    from validate_scenario import load_json, validate


def _instance_ids(actor: dict[str, Any]) -> list[str]:
    actor_id = str(actor["id"])
    count = int(actor["count"])
    if count == 1:
        return [actor_id]
    width = max(2, len(str(count)))
    return [f"{actor_id}_{index:0{width}d}" for index in range(1, count + 1)]


def compile_plan(scenario: dict[str, Any]) -> dict[str, Any]:
    errors = validate(scenario)
    if errors:
        raise ValueError("scenario is invalid: " + "; ".join(errors))

    actor_groups: dict[str, list[str]] = {}
    instances: list[dict[str, Any]] = []

    for actor in scenario["actors"]:
        ids = _instance_ids(actor)
        actor_groups[actor["id"]] = ids
        for instance_id in ids:
            instances.append(
                {
                    "instance_id": instance_id,
                    "group_id": actor["id"],
                    "asset_id": actor["asset_id"],
                    "species": actor["species"],
                    "variant": actor.get("variant"),
                }
            )

    events: list[dict[str, Any]] = []
    required_assets: set[str] = {scenario["environment"]["asset_id"]}

    for actor in scenario["actors"]:
        required_assets.add(actor["asset_id"])

    for shot in scenario["shots"]:
        start = float(shot["start"])
        end = start + float(shot["duration"])
        events.append(
            {
                "type": "camera",
                "time": start,
                "shot_id": shot["id"],
                "end_time": end,
                "camera": shot["camera"],
            }
        )
        for order, action in enumerate(shot["actions"]):
            animation = action.get("animation")
            if animation:
                required_assets.add(animation)
            events.append(
                {
                    "type": "action",
                    "time": start,
                    "shot_id": shot["id"],
                    "order": order,
                    "actor": action["actor"],
                    "resolved_instances": (
                        actor_groups.get(action["actor"], [])
                        if action["actor"] != "environment"
                        else ["environment"]
                    ),
                    "action": action["action"],
                    "target": action.get("target"),
                    "resolved_target_instances": actor_groups.get(action.get("target", ""), []),
                    "animation": animation,
                }
            )

    events.sort(key=lambda event: (event["time"], 0 if event["type"] == "camera" else 1, event.get("order", 0)))

    return {
        "plan_version": 1,
        "scenario_id": scenario["scenario_id"],
        "duration_seconds": scenario["duration_seconds"],
        "style": scenario["style"],
        "environment": scenario["environment"],
        "actor_groups": actor_groups,
        "instances": instances,
        "required_assets": sorted(required_assets),
        "events": events,
        "render": scenario["render"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        scenario = load_json(args.scenario)
        plan = compile_plan(scenario)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"COMPILE FAILED: {exc}", file=sys.stderr)
        return 1

    text = json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"WROTE: {args.output}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
