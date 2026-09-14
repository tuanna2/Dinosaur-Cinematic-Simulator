#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--catalog", type=Path, default=Path("config/asset_catalog.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    scenario = load(args.scenario)
    catalog = load(args.catalog)

    required = set()
    env = scenario.get("environment", {})
    if env.get("asset_id"):
        required.add(env["asset_id"])

    for actor in scenario.get("actors", []):
        if actor.get("asset_id"):
            required.add(actor["asset_id"])

    for shot in scenario.get("shots", []):
        for action in shot.get("actions", []):
            if action.get("animation"):
                required.add(action["animation"])

    available = {
        item["id"]
        for item in catalog.get("assets", [])
        if isinstance(item, dict) and item.get("id")
    }

    report = {
        "scenario_id": scenario.get("scenario_id"),
        "required": sorted(required),
        "resolved": sorted(required & available),
        "missing": sorted(required - available)
    }

    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")

    return 1 if report["missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
