from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
DEFAULT_MODEL = "x/flux-klein"


def command_text(command: Sequence[str]) -> str:
    return " ".join(str(part) for part in command)


def run_command(command: list[str], *, cwd: Path, dry_run: bool) -> None:
    print(f"RUN [{cwd}]: {command_text(command)}")
    if dry_run:
        return
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {command_text(command)}")


def python_command(script: str, scenario: Path, shot_ids: list[str] | None = None) -> list[str]:
    command = [sys.executable, str(ROOT / "pipeline" / script), str(scenario)]
    for shot_id in shot_ids or []:
        command.extend(["--shot-id", shot_id])
    return command


def build_commands(
    scenario: Path,
    *,
    shot_ids: list[str] | None,
    model: str,
    timeout: int,
    no_preview: bool,
    skip_export: bool,
    skip_capture: bool,
    skip_lookdev: bool,
    skip_package: bool,
    allow_missing_lookdev: bool,
) -> list[tuple[list[str], Path]]:
    commands: list[tuple[list[str], Path]] = []

    if not skip_export:
        commands.append(
            (
                [sys.executable, str(ROOT / "pipeline" / "export_web_bundle.py"), str(scenario)],
                ROOT,
            )
        )

    if not skip_capture:
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        commands.append(([npm, "run", "capture:preview"], WEB_ROOT))

    if not skip_lookdev:
        command = python_command("generate_lookdev.py", scenario, shot_ids)
        command.extend(["--model", model, "--timeout", str(timeout)])
        if no_preview:
            command.append("--no-preview")
        commands.append((command, ROOT))

    if not skip_package:
        command = python_command("build_visual_critique_package.py", scenario, shot_ids)
        if allow_missing_lookdev:
            command.append("--allow-missing-lookdev")
        commands.append((command, ROOT))

    return commands


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Run the deterministic preview -> Ollama FLUX look-dev -> visual-critique-package workflow. "
            "This orchestrates existing tools; it does not let FLUX modify scene truth."
        )
    )
    p.add_argument("scenario", type=Path, help="Scenario JSON path")
    p.add_argument("--shot-id", action="append", help="Shot id for FLUX/package stages; repeatable. Defaults to all shots.")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--no-preview", action="store_true", help="Do not attach Three.js preview to FLUX generation.")
    p.add_argument("--skip-export", action="store_true")
    p.add_argument("--skip-capture", action="store_true")
    p.add_argument("--skip-lookdev", action="store_true")
    p.add_argument("--skip-package", action="store_true")
    p.add_argument(
        "--allow-missing-lookdev",
        action="store_true",
        help="Allow preview-only critique packages when FLUX output is absent.",
    )
    p.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    return p


def main() -> int:
    args = parser().parse_args()
    scenario = args.scenario.resolve()

    try:
        if not scenario.exists():
            raise FileNotFoundError(f"Scenario not found: {scenario}")
        if not args.skip_capture and shutil.which("npm") is None and shutil.which("npm.cmd") is None:
            raise RuntimeError("npm executable was not found in PATH")

        scenario_data = json.loads(scenario.read_text(encoding="utf-8"))
        scenario_id = str(scenario_data.get("scenario_id", scenario.stem))
        available_shots = {str(shot.get("id")) for shot in scenario_data.get("shots", [])}
        for shot_id in args.shot_id or []:
            if shot_id not in available_shots:
                raise ValueError(f"Unknown shot id: {shot_id}")

        for command, cwd in build_commands(
            scenario,
            shot_ids=args.shot_id,
            model=args.model,
            timeout=args.timeout,
            no_preview=args.no_preview,
            skip_export=args.skip_export,
            skip_capture=args.skip_capture,
            skip_lookdev=args.skip_lookdev,
            skip_package=args.skip_package,
            allow_missing_lookdev=args.allow_missing_lookdev,
        ):
            run_command(command, cwd=cwd, dry_run=args.dry_run)

        if args.dry_run:
            print(f"DRY-RUN complete for {scenario_id}")
        else:
            print(f"LOOKDEV LOOP READY: {ROOT / 'build' / 'critique' / scenario_id}")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
