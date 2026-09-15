#!/usr/bin/env python3
"""Register an approved reusable asset in the deterministic asset catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[a-z0-9_-]+$")
ALLOWED_TYPES = {
    "dinosaur",
    "environment",
    "prop",
    "animation",
    "camera_preset",
    "weather_preset",
    "material",
    "audio",
}
ALLOWED_STATUS = {"planned", "draft", "approved", "deprecated"}


def load_catalog(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("assets"), list):
        raise ValueError("catalog must be an object containing an assets array")
    return value


def register(catalog: dict[str, Any], asset: dict[str, Any], replace: bool = False) -> dict[str, Any]:
    asset_id = asset.get("id")
    if not isinstance(asset_id, str) or not ID_RE.fullmatch(asset_id):
        raise ValueError("asset id must match ^[a-z0-9_-]+$")
    if asset.get("type") not in ALLOWED_TYPES:
        raise ValueError(f"unsupported asset type: {asset.get('type')!r}")
    if asset.get("status") not in ALLOWED_STATUS:
        raise ValueError(f"unsupported asset status: {asset.get('status')!r}")

    assets = catalog["assets"]
    existing_index = next(
        (index for index, item in enumerate(assets) if isinstance(item, dict) and item.get("id") == asset_id),
        None,
    )
    if existing_index is not None and not replace:
        raise ValueError(f"asset already exists: {asset_id}; use --replace to update it")

    cleaned = {key: value for key, value in asset.items() if value is not None and value != ""}
    if existing_index is None:
        assets.append(cleaned)
    else:
        assets[existing_index] = cleaned

    assets.sort(key=lambda item: str(item.get("id", "")))
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset_id")
    parser.add_argument("--type", required=True, choices=sorted(ALLOWED_TYPES))
    parser.add_argument("--status", default="approved", choices=sorted(ALLOWED_STATUS))
    parser.add_argument("--catalog", type=Path, default=Path("config/asset_catalog.json"))
    parser.add_argument("--blender-source")
    parser.add_argument("--export-path")
    parser.add_argument("--web-path")
    parser.add_argument("--unreal-path")
    parser.add_argument("--skeleton-id")
    parser.add_argument("--species")
    parser.add_argument("--notes")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    asset = {
        "id": args.asset_id,
        "type": args.type,
        "status": args.status,
        "blender_source": args.blender_source,
        "export_path": args.export_path,
        "web_path": args.web_path,
        "unreal_path": args.unreal_path,
        "skeleton_id": args.skeleton_id,
        "species": args.species,
        "notes": args.notes,
    }

    try:
        catalog = load_catalog(args.catalog)
        register(catalog, asset, replace=args.replace)
        args.catalog.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"REGISTER FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"REGISTERED: {args.asset_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
