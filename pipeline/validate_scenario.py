#!/usr/bin/env python3
"""Validate a cinematic scenario using only the Python standard library.

This intentionally performs the core checks required by the production pipeline
without depending on an AI model or third-party package.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "scenario_id",
    "title",
    "duration_seconds",
    "style",
    "environment",
    "actors",
    "shots",
    "render",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("scenario root must be a JSON object")
    return value


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        errors.append(f"missing top-level keys: {', '.join(missing)}")

    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    duration = data.get("duration_seconds")
    if not isinstance(duration, (int, float)) or duration <= 0:
        errors.append("duration_seconds must be > 0")
        duration = 0

    actors = data.get("actors", [])
    if not isinstance(actors, list) or not actors:
        errors.append("actors must be a non-empty array")
        actor_ids: set[str] = set()
    else:
        actor_ids = set()
        for index, actor in enumerate(actors):
            if not isinstance(actor, dict):
                errors.append(f"actors[{index}] must be an object")
                continue
            actor_id = actor.get("id")
            if not isinstance(actor_id, str) or not actor_id:
                errors.append(f"actors[{index}].id is required")
            elif actor_id in actor_ids:
                errors.append(f"duplicate actor id: {actor_id}")
            else:
                actor_ids.add(actor_id)
            count = actor.get("count")
            if not isinstance(count, int) or count < 1:
                errors.append(f"actors[{index}].count must be an integer >= 1")

    shots = data.get("shots", [])
    if not isinstance(shots, list) or not shots:
        errors.append("shots must be a non-empty array")
        return errors

    seen_shots: set[str] = set()
    previous_start = -1.0
    latest_end = 0.0

    for index, shot in enumerate(shots):
        prefix = f"shots[{index}]"
        if not isinstance(shot, dict):
            errors.append(f"{prefix} must be an object")
            continue

        shot_id = shot.get("id")
        if not isinstance(shot_id, str) or not shot_id:
            errors.append(f"{prefix}.id is required")
        elif shot_id in seen_shots:
            errors.append(f"duplicate shot id: {shot_id}")
        else:
            seen_shots.add(shot_id)

        start = shot.get("start")
        shot_duration = shot.get("duration")
        if not isinstance(start, (int, float)) or start < 0:
            errors.append(f"{prefix}.start must be >= 0")
            continue
        if not isinstance(shot_duration, (int, float)) or shot_duration <= 0:
            errors.append(f"{prefix}.duration must be > 0")
            continue

        if start < previous_start:
            errors.append(f"{prefix} starts before the previous shot")
        previous_start = float(start)
        latest_end = max(latest_end, float(start) + float(shot_duration))

        camera = shot.get("camera")
        if not isinstance(camera, dict) or not camera.get("preset"):
            errors.append(f"{prefix}.camera.preset is required")

        actions = shot.get("actions")
        if not isinstance(actions, list):
            errors.append(f"{prefix}.actions must be an array")
            continue

        for action_index, action in enumerate(actions):
            aprefix = f"{prefix}.actions[{action_index}]"
            if not isinstance(action, dict):
                errors.append(f"{aprefix} must be an object")
                continue
            actor = action.get("actor")
            if actor != "environment" and actor not in actor_ids:
                errors.append(f"{aprefix}.actor references unknown actor: {actor!r}")
            if not action.get("action"):
                errors.append(f"{aprefix}.action is required")

    if duration and latest_end > float(duration) + 0.001:
        errors.append(
            f"shot timeline ends at {latest_end:.3f}s, beyond duration_seconds={duration}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", type=Path)
    args = parser.parse_args()

    try:
        data = load_json(args.scenario)
        errors = validate(data)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"VALID: {data['scenario_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
