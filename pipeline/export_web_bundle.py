#!/usr/bin/env python3
"""Compile a scenario into the static runtime bundle consumed by the Three.js app."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

try:
    from pipeline.compile_execution_plan import compile_plan
    from pipeline.validate_scenario import load_json
except ModuleNotFoundError:
    from compile_execution_plan import compile_plan
    from validate_scenario import load_json


def load_catalog(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("assets"), list):
        raise ValueError("catalog must contain an assets array")
    return value


def export_bundle(
    scenario_path: Path,
    catalog_path: Path,
    output_dir: Path,
    copy_assets: bool = False,
) -> tuple[Path, Path]:
    scenario = load_json(scenario_path)
    plan = compile_plan(scenario)
    catalog = load_catalog(catalog_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = output_dir / "execution_plan.json"
    manifest_path = output_dir / "asset_manifest.json"

    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    assets: list[dict[str, Any]] = []
    for item in catalog.get("assets", []):
        if not isinstance(item, dict) or not item.get("id"):
            continue
        web_path = item.get("web_path")
        export_path = item.get("export_path")
        if copy_assets and not web_path and export_path:
            source = Path(export_path)
            if source.exists() and source.is_file():
                target_dir = output_dir.parent / "assets"
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / source.name
                shutil.copy2(source, target)
                web_path = f"/assets/{target.name}"
        assets.append({"id": item["id"], "web_path": web_path})

    manifest = {"schema_version": 1, "assets": assets}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return plan_path, manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--catalog", type=Path, default=Path("config/asset_catalog.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("web/public/runtime"))
    parser.add_argument("--copy-assets", action="store_true")
    args = parser.parse_args()

    try:
        plan_path, manifest_path = export_bundle(
            args.scenario,
            args.catalog,
            args.output_dir,
            copy_assets=args.copy_assets,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"WEB EXPORT FAILED: {exc}")
        return 1

    print(f"WROTE: {plan_path}")
    print(f"WROTE: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
