from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from pipeline.build_agent_requests import build_requests
from pipeline.build_visual_critique_package import build_package
from pipeline.compile_execution_plan import compile_plan
from pipeline.export_web_bundle import export_bundle
from pipeline.generate_lookdev import DEFAULT_MODEL as LOOKDEV_DEFAULT_MODEL
from pipeline.generate_lookdev import build_prompt, find_shot
from pipeline.preflight import resolve_required
from pipeline.register_asset import register
from pipeline.route_visual_critique import route_critique
from pipeline.run_lookdev_loop import DEFAULT_MODEL as LOOP_DEFAULT_MODEL
from pipeline.run_lookdev_loop import build_commands
from pipeline.run_visual_iteration import critique_summary, decide_iteration, next_iteration_dir
from pipeline.validate_scenario import load_json, validate


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "scenarios" / "raptor_hunt_001" / "scenario.json"
CATALOG = ROOT / "config" / "asset_catalog.json"


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenario = load_json(SCENARIO)

    def test_sample_scenario_is_valid(self) -> None:
        self.assertEqual(validate(self.scenario), [])

    def test_compiler_expands_actor_groups(self) -> None:
        plan = compile_plan(self.scenario)
        self.assertEqual(len(plan["actor_groups"]["raptor_pack"]), 8)
        self.assertEqual(plan["actor_groups"]["raptor_pack"][0], "raptor_pack_01")
        self.assertEqual(plan["actor_groups"]["raptor_pack"][-1], "raptor_pack_08")
        self.assertEqual(len(plan["instances"]), 10)

    def test_compiler_preserves_render_contract(self) -> None:
        plan = compile_plan(self.scenario)
        self.assertEqual(plan["render"]["width"], 3840)
        self.assertEqual(plan["render"]["height"], 2160)
        self.assertEqual(plan["render"]["fps"], 60)

    def test_action_offsets_compile_to_event_times(self) -> None:
        plan = compile_plan(self.scenario)
        shot_events = [
            event
            for event in plan["events"]
            if event["type"] == "action" and event["shot_id"] == "shot_005"
        ]
        by_action = {(event["actor"], event["action"]): event for event in shot_events}
        self.assertEqual(by_action[("trex_01", "enter")]["time"], 125.0)
        self.assertEqual(by_action[("trex_01", "roar")]["time"], 131.0)
        self.assertEqual(by_action[("raptor_pack", "react")]["time"], 131.0)

    def test_action_offset_must_stay_inside_shot(self) -> None:
        invalid = copy.deepcopy(self.scenario)
        invalid["shots"][0]["actions"][0]["offset_seconds"] = invalid["shots"][0]["duration"]
        errors = validate(invalid)
        self.assertTrue(any("offset_seconds" in error for error in errors))

    def test_required_assets_include_animation_and_master_assets(self) -> None:
        plan = compile_plan(self.scenario)
        required = set(plan["required_assets"])
        self.assertIn("env_tropical_rainforest", required)
        self.assertIn("dino_trex_master", required)
        self.assertIn("dino_velociraptor_master", required)
        self.assertIn("dino_triceratops_master", required)
        self.assertIn("anim_trex_roar", required)

    def test_asset_resolver_reports_missing(self) -> None:
        plan = compile_plan(self.scenario)
        catalog = {"assets": [{"id": "dino_trex_master"}]}
        resolved, missing = resolve_required(plan, catalog)
        self.assertEqual(resolved, ["dino_trex_master"])
        self.assertIn("env_tropical_rainforest", missing)
        self.assertIn("anim_trex_roar", missing)

    def test_compiled_plan_is_json_serializable(self) -> None:
        plan = compile_plan(self.scenario)
        encoded = json.dumps(plan)
        self.assertIn("raptor_hunt_001", encoded)

    def test_agent_requests_route_dinosaurs_animations_and_environment(self) -> None:
        report = {
            "scenario_id": "test",
            "missing_assets": ["dino_trex_master", "anim_trex_roar", "env_tropical_rainforest"],
        }
        requests = build_requests(report)
        agents = {request["agent"] for request in requests}
        self.assertIn("asset_designer", agents)
        self.assertIn("animation_director", agents)
        self.assertIn("environment_designer", agents)

    def test_asset_registration_supports_web_path(self) -> None:
        catalog = {"assets": []}
        register(
            catalog,
            {
                "id": "dino_trex_master",
                "type": "dinosaur",
                "status": "approved",
                "web_path": "/assets/trex_master.glb",
            },
        )
        self.assertEqual(catalog["assets"][0]["web_path"], "/assets/trex_master.glb")

    def test_web_bundle_exports_execution_plan_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "runtime"
            plan_path, manifest_path = export_bundle(SCENARIO, CATALOG, output)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(plan["scenario_id"], "raptor_hunt_001")
            self.assertEqual(len(plan["instances"]), 10)
            self.assertEqual(manifest["schema_version"], 1)
            self.assertIsInstance(manifest["assets"], list)

    def test_flux_default_model_is_canonical_4b_tag_everywhere(self) -> None:
        self.assertEqual(LOOKDEV_DEFAULT_MODEL, "x/flux2-klein:4b")
        self.assertEqual(LOOP_DEFAULT_MODEL, "x/flux2-klein:4b")

    def test_lookdev_prompt_uses_shot_semantics(self) -> None:
        shot = find_shot(self.scenario, "shot_005")
        prompt = build_prompt(self.scenario, shot, False)
        self.assertIn("tyrannosaurus rex enter", prompt)
        self.assertIn("tyrannosaurus rex roar", prompt)
        self.assertIn("8 velociraptor react", prompt)
        self.assertIn("32mm lens", prompt)
        self.assertIn("visual-quality reference only", prompt)
        self.assertNotIn("./reference.png", prompt)

    def test_lookdev_prompt_does_not_claim_preview_image_editing(self) -> None:
        shot = find_shot(self.scenario, "shot_005")
        prompt = build_prompt(self.scenario, shot, True)
        self.assertIn("this Ollama generation step is text-only", prompt)
        self.assertIn("advisory realism/look target", prompt)
        self.assertNotIn("Reference image:", prompt)
        self.assertNotIn("./reference.png", prompt)

    def test_visual_critique_package_links_preview_target_and_relevant_actors(self) -> None:
        shot = find_shot(self.scenario, "shot_005")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview_dir = root / "preview"
            lookdev_dir = root / "lookdev"
            output_dir = root / "critique"
            preview_dir.mkdir()
            lookdev_dir.mkdir()
            (preview_dir / "shot_005.png").write_bytes(b"preview")
            (lookdev_dir / "shot_005.png").write_bytes(b"target")
            (lookdev_dir / "shot_005.prompt.txt").write_text("prompt\n", encoding="utf-8")
            (lookdev_dir / "shot_005.json").write_text(
                json.dumps(
                    {
                        "provider": "ollama_cli",
                        "model": "x/flux2-klein:4b",
                        "generation_input": "text_only",
                        "reference_sent_to_model": False,
                        "composition_authority": "deterministic_preview",
                    }
                ),
                encoding="utf-8",
            )

            package_path, request_path = build_package(
                self.scenario,
                shot,
                preview_dir=preview_dir,
                lookdev_dir=lookdev_dir,
                output_dir=output_dir,
            )
            package = json.loads(package_path.read_text(encoding="utf-8"))
            actor_ids = {actor["id"] for actor in package["actors"]}

            self.assertEqual(package["schema_version"], 2)
            self.assertEqual(package["shot_id"], "shot_005")
            self.assertEqual(actor_ids, {"raptor_pack", "trex_01"})
            self.assertTrue(package["inputs"]["preview_frame"].endswith("shot_005.png"))
            self.assertTrue(package["inputs"]["lookdev_target"].endswith("shot_005.png"))
            self.assertEqual(package["lookdev_metadata"]["model"], "x/flux2-klein:4b")
            self.assertFalse(package["lookdev_metadata"]["reference_sent_to_model"])
            self.assertEqual(package["review_contract"]["composition_authority"], "deterministic_preview")
            self.assertIn("requires_agent", package["expected_output"])
            request = request_path.read_text(encoding="utf-8")
            self.assertIn("ignore any different actor count", request)

    def test_lookdev_loop_builds_generation_and_packaging_commands(self) -> None:
        commands = build_commands(
            SCENARIO.resolve(),
            shot_ids=["shot_005"],
            model="x/flux2-klein:4b",
            timeout=120,
            no_preview=False,
            skip_export=True,
            skip_capture=True,
            skip_lookdev=False,
            skip_package=False,
            allow_missing_lookdev=False,
        )
        self.assertEqual(len(commands), 2)
        lookdev_command = commands[0][0]
        package_command = commands[1][0]
        self.assertTrue(any(part.endswith("generate_lookdev.py") for part in lookdev_command))
        self.assertIn("x/flux2-klein:4b", lookdev_command)
        self.assertIn("shot_005", lookdev_command)
        self.assertTrue(any(part.endswith("build_visual_critique_package.py") for part in package_command))

    def test_visual_iteration_next_directory_is_monotonic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(next_iteration_dir(root).name, "iteration_001")
            (root / "iteration_001").mkdir()
            (root / "iteration_003").mkdir()
            self.assertEqual(next_iteration_dir(root).name, "iteration_004")

    def test_visual_iteration_pass_requires_clean_routing(self) -> None:
        critique = {
            "shot_id": "shot_005",
            "pass": True,
            "issues": [],
            "patches": [],
            "requires_agent": [],
        }
        routing = route_critique(self.scenario, critique, {"assets": []})
        decision = decide_iteration(critique, routing, None)
        self.assertEqual(decision["state"], "PASS")
        self.assertEqual(decision["trend"], "unknown")

    def test_visual_iteration_blocking_request_blocks_pass(self) -> None:
        critique = {
            "shot_id": "shot_005",
            "pass": False,
            "issues": [
                {
                    "category": "anatomy",
                    "severity": "blocking",
                    "observation": "T-Rex hip continuity is visibly broken.",
                    "evidence": "preview_only",
                }
            ],
            "patches": [],
            "requires_agent": [
                {
                    "agent": "asset_designer",
                    "asset_id": "dino_trex_master",
                    "severity": "blocking",
                    "reason": "Repair hip continuity.",
                    "acceptance_criteria": ["No visible hip seam."],
                }
            ],
        }
        catalog = {"assets": [{"id": "dino_trex_master", "type": "dinosaur"}]}
        routing = route_critique(self.scenario, critique, catalog)
        decision = decide_iteration(critique, routing, None)
        self.assertEqual(decision["state"], "BLOCKED")
        self.assertEqual(decision["routing"]["work_request_priorities"]["blocking"], 1)

    def test_visual_iteration_reports_improvement_against_previous_critique(self) -> None:
        before = critique_summary(
            {
                "pass": False,
                "issues": [{"severity": "blocking"}, {"severity": "high"}],
                "patches": [],
                "requires_agent": [{"asset_id": "dino_trex_master"}],
            }
        )
        critique = {
            "shot_id": "shot_005",
            "pass": False,
            "issues": [{"category": "anatomy", "severity": "medium"}],
            "patches": [],
            "requires_agent": [],
        }
        routing = route_critique(self.scenario, critique, {"assets": []})
        decision = decide_iteration(critique, routing, before)
        self.assertEqual(decision["state"], "CONTINUE")
        self.assertEqual(decision["trend"], "improved")
        self.assertLess(decision["quality_delta"], 0)


if __name__ == "__main__":
    unittest.main()
