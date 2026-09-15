from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "x/flux2-klein:4b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_NEGATIVE_PROMPT = (
    "cartoon, stylized toy, plastic skin, low-poly, game UI, text, watermark, "
    "extra limbs, duplicated animals, malformed anatomy, floating feet"
)


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

    preserve = (
        "Use the supplied reference image as the strict composition guide. Preserve camera angle, "
        "animal positions, silhouettes, action geography, framing and relative scale. "
        if has_reference
        else "Create a production look-development target for this exact cinematic shot. "
    )

    lens = camera.get("lens_mm", 50)
    preset = str(camera.get("preset", "cinematic")).replace("_", " ")
    target = camera.get("target")
    target_text = f", focused on {actor_label(str(target), actors)}" if target else ""
    action_text = "; ".join(action_phrases) or "natural prehistoric animal behavior"

    return (
        f"{preserve}"
        f"Photorealistic prehistoric wildlife documentary frame, not a video game screenshot. "
        f"Scene: {action_text}. Environment: {str(environment.get('asset_id', 'prehistoric wilderness')).replace('_', ' ')}, "
        f"weather {str(environment.get('weather', 'natural')).replace('_', ' ')}, "
        f"time {str(environment.get('time_of_day', 'day')).replace('_', ' ')}. "
        f"Camera language: {preset}, {lens}mm lens{target_text}. "
        "Dinosaurs must have paleontologically plausible anatomy, believable body mass and weight, "
        "continuous neck/hip/tail transitions, grounded feet, natural musculature, realistic eyes, teeth, gums and oral tissue. "
        "Skin should have physically plausible micro-scales, folds, scars, mud and wet roughness variation without looking embossed or synthetic. "
        "Dense layered vegetation, wet ground, atmospheric depth, rain readability, volumetric mist, natural occlusion, "
        "cinematic contrast and physically believable late-afternoon lighting. "
        "BBC-style high-end natural-history documentary realism, subtle filmic color response, realistic depth of field. "
        "Do not redesign the shot, add unrelated animals, add text, logos, HUD, borders or interface elements."
    )


def parse_ollama_response(raw: bytes) -> dict[str, Any]:
    text = raw.decode("utf-8").strip()
    if not text:
        raise RuntimeError("Ollama returned an empty response")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    last: dict[str, Any] | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            last = item
            if item.get("image"):
                return item
    if last is None:
        raise RuntimeError("Could not parse Ollama response as JSON/NDJSON")
    return last


def generate_image(
    *,
    endpoint: str,
    model: str,
    prompt: str,
    reference_path: Path | None,
    width: int | None,
    height: int | None,
    steps: int | None,
    seed: int | None,
    negative_prompt: str | None,
    timeout_seconds: int,
) -> bytes:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if reference_path is not None:
        payload["images"] = [base64.b64encode(reference_path.read_bytes()).decode("ascii")]
    if width is not None:
        payload["width"] = width
    if height is not None:
        payload["height"] = height
    if steps is not None:
        payload["steps"] = steps
    if seed is not None:
        payload["seed"] = seed
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt

    request = urllib.request.Request(
        endpoint.rstrip("/") + "/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            result = parse_ollama_response(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach Ollama at {endpoint}: {exc.reason}") from exc

    image_b64 = result.get("image")
    if not image_b64:
        error = result.get("error")
        if error:
            raise RuntimeError(f"Ollama image generation failed: {error}")
        raise RuntimeError(
            "Ollama response did not contain an image field. "
            "Your Ollama build may not expose experimental image generation through /api/generate."
        )
    try:
        return base64.b64decode(image_b64)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("Ollama returned invalid base64 image data") from exc


def generate_for_shot(
    scenario: dict[str, Any],
    shot: dict[str, Any],
    *,
    preview_dir: Path,
    output_dir: Path,
    endpoint: str,
    model: str,
    use_preview: bool,
    width: int | None,
    height: int | None,
    steps: int | None,
    seed: int | None,
    negative_prompt: str | None,
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
        "model": model,
        "ollama_url": endpoint,
        "reference_preview": str(reference) if reference else None,
        "width": width,
        "height": height,
        "steps": steps,
        "seed": seed,
        "negative_prompt": negative_prompt,
        "output": str(output_path),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if dry_run:
        print(f"DRY-RUN {shot_id}: {prompt_path}")
        return None

    image = generate_image(
        endpoint=endpoint,
        model=model,
        prompt=prompt,
        reference_path=reference,
        width=width,
        height=height,
        steps=steps,
        seed=seed,
        negative_prompt=negative_prompt,
        timeout_seconds=timeout_seconds,
    )
    output_path.write_bytes(image)
    print(f"WROTE {shot_id}: {output_path}")
    return output_path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate cinematic look-dev target frames with a local Ollama FLUX.2 Klein model."
    )
    p.add_argument("scenario", type=Path, help="Scenario JSON path")
    p.add_argument("--shot-id", action="append", help="Shot id to generate; repeatable. Defaults to all shots.")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    p.add_argument("--preview-dir", type=Path)
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--no-preview", action="store_true", help="Do text-to-image only; do not send captured preview as reference.")
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=576)
    p.add_argument("--steps", type=int)
    p.add_argument("--seed", type=int)
    p.add_argument("--negative-prompt", default=DEFAULT_NEGATIVE_PROMPT)
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    scenario_path = args.scenario.resolve()
    scenario = load_json(scenario_path)
    scenario_id = str(scenario.get("scenario_id", scenario_path.stem))
    preview_dir = (args.preview_dir or ROOT / "build" / "preview" / scenario_id).resolve()
    output_dir = (args.output_dir or ROOT / "build" / "lookdev" / scenario_id).resolve()

    try:
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
                endpoint=args.ollama_url,
                model=args.model,
                use_preview=not args.no_preview,
                width=args.width,
                height=args.height,
                steps=args.steps,
                seed=args.seed,
                negative_prompt=args.negative_prompt,
                timeout_seconds=args.timeout,
                dry_run=args.dry_run,
            )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
