from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "x/flux2-klein:4b"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_shot(scenario: dict[str, Any], shot_id: str) -> dict[str, Any]:
    for shot in scenario.get("shots", []):
        if shot.get("id") == shot_id:
            return shot
    raise ValueError(f"Unknown shot id: {shot_id}")


def actor_label(actor_id: str, actors: list[dict[str, Any]]) -> str:
    if actor_id == "environment":
        return "environment"
    for actor in actors:
        if actor.get("id") == actor_id:
            count = int(actor.get("count", 1))
            species = str(actor.get("species", actor_id)).replace("_", " ")
            return f"{count} {species}" if count > 1 else species
    return actor_id.replace("_", " ")


def build_prompt(scenario: dict[str, Any], shot: dict[str, Any], has_reference: bool) -> str:
    actors = scenario.get("actors", [])
    environment = scenario.get("environment", {})
    camera = shot.get("camera", {})

    action_phrases: list[str] = []
    for action in shot.get("actions", []):
        subject = actor_label(str(action.get("actor", "subject")), actors)
        verb = str(action.get("action", "acting")).replace("_", " ")
        target = action.get("target")
        if target:
            action_phrases.append(f"{subject} {verb} toward {actor_label(str(target), actors)}")
        else:
            action_phrases.append(f"{subject} {verb}")

    lens = camera.get("lens_mm", 50)
    preset = str(camera.get("preset", "cinematic")).replace("_", " ")
    target = camera.get("target")
    target_text = f", focused on {actor_label(str(target), actors)}" if target else ""
    action_text = "; ".join(action_phrases) or "natural prehistoric animal behavior"

    preview_note = (
        "A deterministic Three.js preview exists for downstream comparison, but this Ollama generation step is text-only. "
        "Create an advisory realism/look target rather than an exact composition replacement. "
        if has_reference
        else "Create an advisory production look-development target for this cinematic shot. "
    )

    return (
        f"{preview_note}"
        "Photorealistic prehistoric wildlife documentary frame, not a video game screenshot. "
        f"Scene context: {action_text}. Environment: {str(environment.get('asset_id', 'prehistoric wilderness')).replace('_', ' ')}, "
        f"weather {str(environment.get('weather', 'natural')).replace('_', ' ')}, "
        f"time {str(environment.get('time_of_day', 'day')).replace('_', ' ')}. "
        f"Camera language: {preset}, {lens}mm lens{target_text}. "
        "Dinosaurs should have paleontologically plausible anatomy, believable body mass and weight, continuous neck, hip and tail transitions, "
        "grounded feet, natural musculature, realistic eyes, teeth, gums and oral tissue. "
        "Skin has physically plausible micro-scales, folds, scars, mud and wet roughness variation without looking embossed or synthetic. "
        "Dense layered prehistoric vegetation, wet ground, atmospheric depth, readable rain, volumetric mist, natural occlusion, cinematic contrast, "
        "physically believable late-afternoon lighting, high-end natural-history documentary realism, subtle filmic color response, realistic depth of field. "
        "Avoid cartoon styling, plastic skin, low-poly appearance, game UI, text, logos, watermarks, malformed anatomy, extra limbs and floating feet. "
        "Do not introduce unrelated species or modern objects. "
        "This image is a visual-quality reference only: scenario actor count, exact blocking, camera placement and composition remain authoritative in the deterministic preview."
    )


def generated_images(directory: Path) -> list[Path]:
    return sorted(
        [path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES],
        key=lambda path: path.stat().st_mtime_ns,
    )


def run_ollama_cli(*, model: str, prompt: str, timeout_seconds: int) -> tuple[bytes, str]:
    if shutil.which("ollama") is None:
        raise RuntimeError("ollama executable was not found in PATH")

    with tempfile.TemporaryDirectory(prefix="dino-flux-") as tmp:
        workdir = Path(tmp)

        try:
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                cwd=workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"ollama run timed out after {timeout_seconds}s") from exc

        if result.returncode != 0:
            output = result.stdout.strip()
            raise RuntimeError(f"ollama run failed ({result.returncode}):\n{output}")

        images = generated_images(workdir)
        if not images:
            raise RuntimeError(
                "ollama run completed but no generated image was found in its working directory. "
                "Run the same model manually once to confirm image generation is enabled in this Ollama build.\n"
                f"CLI output:\n{result.stdout.strip()}"
            )
        return images[-1].read_bytes(), result.stdout


def generate_for_shot(
    scenario: dict[str, Any],
    shot: dict[str, Any],
    *,
    preview_dir: Path,
    output_dir: Path,
    model: str,
    use_preview: bool,
    timeout_seconds: int,
    dry_run: bool,
) -> Path | None:
    shot_id = str(shot["id"])
    preview_path = preview_dir / f"{shot_id}.png"
    reference = preview_path if use_preview and preview_path.exists() else None
    prompt = build_prompt(scenario, shot, reference is not None)

    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = output_dir / f"{shot_id}.prompt.txt"
    metadata_path = output_dir / f"{shot_id}.json"
    output_path = output_dir / f"{shot_id}.png"

    prompt_path.write_text(prompt + "\n", encoding="utf-8")
    metadata = {
        "scenario_id": scenario.get("scenario_id"),
        "shot_id": shot_id,
        "provider": "ollama_cli",
        "model": model,
        "generation_input": "text_only",
        "reference_preview": str(reference) if reference else None,
        "reference_sent_to_model": False,
        "composition_authority": "deterministic_preview",
        "lookdev_role": "advisory_anatomy_material_lighting_environment_target",
        "output": str(output_path),
        "command": ["ollama", "run", model, "<prompt>"],
    }

    if dry_run:
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        print(f"DRY-RUN {shot_id}: ollama run {model} <prompt>")
        return None

    image, cli_output = run_ollama_cli(
        model=model,
        prompt=prompt,
        timeout_seconds=timeout_seconds,
    )
    output_path.write_bytes(image)
    metadata["cli_output"] = cli_output.strip()
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {shot_id}: {output_path}")
    return output_path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate advisory cinematic look-dev target frames with local Ollama FLUX Klein.")
    p.add_argument("scenario", type=Path, help="Scenario JSON path")
    p.add_argument("--shot-id", action="append", help="Shot id to generate; repeatable. Defaults to all shots.")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama image model (default: {DEFAULT_MODEL})")
    p.add_argument("--preview-dir", type=Path)
    p.add_argument("--output-dir", type=Path)
    p.add_argument(
        "--no-preview",
        action="store_true",
        help=(
            "Do not associate an existing deterministic preview with look-dev metadata. "
            "Ollama generation is text-only either way; the preview is used later by the critic."
        ),
    )
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    scenario_path = args.scenario.resolve()

    try:
        scenario = load_json(scenario_path)
        scenario_id = str(scenario.get("scenario_id", scenario_path.stem))
        preview_dir = (args.preview_dir or ROOT / "build" / "preview" / scenario_id).resolve()
        output_dir = (args.output_dir or ROOT / "build" / "lookdev" / scenario_id).resolve()

        shots = scenario.get("shots", [])
        if args.shot_id:
            shots = [find_shot(scenario, shot_id) for shot_id in args.shot_id]
        if not shots:
            raise ValueError("Scenario contains no shots")

        for shot in shots:
            generate_for_shot(
                scenario,
                shot,
                preview_dir=preview_dir,
                output_dir=output_dir,
                model=args.model,
                use_preview=not args.no_preview,
                timeout_seconds=args.timeout,
                dry_run=args.dry_run,
            )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
