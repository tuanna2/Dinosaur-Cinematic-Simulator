from __future__ import annotations

import json
import unittest
from pathlib import Path

from pipeline.build_agent_requests import build_requests
from pipeline.compile_execution_plan import compile_plan
from pipeline.preflight import resolve_required
from pipeline.register_asset import register
from pipeline.validate_scenario import load_json, validate


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "scenarios" / "raptor_hunt_001" / "scenario.json"


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

    def test_agent_requests_route_animation_and_dinosaur_gaps(self) -> None:
        report = {
            "scenario_id": "sample",
            "missing_assets": ["anim_trex_roar", "dino_trex_master"],
        }
        requests = build_requests(report)
        by_asset = {request["asset_id"]: request for request in requests}
        self.assertEqual(by_asset["anim_trex_roar"]["agent"], "animation_director")
        self.assertEqual(by_asset["dino_trex_master"]["agent"], "asset_designer")

    def test_register_asset_rejects_duplicate_without_replace(self) -> None:
        catalog = {
            "schema_version": 1,
            "blender_version": "5.2.1",
            "assets": [
                {"id": "dino_trex_master", "type": "dinosaur", "status": "approved"}
            ],
        }
        with self.assertRaises(ValueError):
            register(
                catalog,
                {"id": "dino_trex_master", "type": "dinosaur", "status": "approved"},
            )

    def test_register_asset_adds_and_sorts_asset(self) -> None:
        catalog = {
            "schema_version": 1,
            "blender_version": "5.2.1",
            "assets": [
                {"id": "env_tropical_rainforest", "type": "environment", "status": "approved"}
            ],
        }
        register(
            catalog,
            {
                "id": "dino_trex_master",
                "type": "dinosaur",
                "status": "approved",
                "blender_source": "blender/dinosaurs/trex.blend",
            },
        )
        self.assertEqual([item["id"] for item in catalog["assets"]], ["dino_trex_master", "env_tropical_rainforest"])


if __name__ == "__main__":
    unittest.main()
