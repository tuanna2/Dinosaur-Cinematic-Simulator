#!/usr/bin/env python3
"""Repeatable Blender 5.2.1 -> GLB export helper.

Usage:
  blender --background source.blend --python blender/export_glb.py -- --output path/to/asset.glb
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    args = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--selection", action="store_true", help="Export only selected objects")
    parser.add_argument(
        "--animation-mode",
        choices=["ACTIONS", "ACTIVE_ACTIONS", "NLA_TRACKS", "SCENE"],
        default="ACTIONS",
    )
    return parser.parse_args(args)


def main() -> int:
    args = parse_args()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    result = bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLB",
        use_selection=args.selection,
        export_yup=True,
        export_apply=False,
        export_materials="EXPORT",
        export_texcoords=True,
        export_normals=True,
        export_animations=True,
        export_animation_mode=args.animation_mode,
        export_force_sampling=True,
        export_optimize_animation_size=True,
        export_skins=True,
        export_morph=True,
        export_morph_animation=True,
        export_lights=False,
        export_cameras=False,
    )
    if "FINISHED" not in result:
        print(f"GLB EXPORT FAILED: {sorted(result)}", file=sys.stderr)
        return 1

    print(f"EXPORTED GLB: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
