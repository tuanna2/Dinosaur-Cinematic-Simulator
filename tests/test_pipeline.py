from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from pipeline.build_agent_requests import build_requests
from pipeline.compile_execution_plan import compile_plan
from pipeline.export_web_bundle import export_bundle
from pipeline.generate_lookdev import build_prompt, find_shot
from pipeline.preflight import resolve_required
from pipeline.register_asset import register
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

    def test_lookdev_prompt_uses_shot_semantics(self) -> None:
        shot = find_shot(self.scenario, "shot_005")
        prompt = build_prompt(self.scenario, shot, False)
        self.assertIn("tyrannosaurus rex enter", prompt)
        self.assertIn("tyrannosaurus rex roar", prompt)
        self.assertIn("8 velociraptor react", prompt)
        self.assertIn("32mm lens", prompt)
        self.assertNotIn("./reference.png", prompt)

    def test_lookdev_reference_prompt_preserves_composition(self) -> None:
        shot = find_shot(self.scenario, "shot_005")
        prompt = build_prompt(self.scenario, shot, True)
        self.assertIn("Preserve the camera angle", prompt)
        self.assertIn("Reference image: ./reference.png", prompt)


if __name__ == "__main__":
    unittest.main()
