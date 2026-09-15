from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pipeline.route_visual_critique import route_critique, write_outputs


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = ROOT / "scenarios" / "raptor_hunt_001" / "scenario.json"
CATALOG_PATH = ROOT / "config" / "asset_catalog.json"


class CritiqueRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    def test_routes_patches_and_groups_reusable_asset_work(self) -> None:
        critique = {
            "shot_id": "shot_005",
            "pass": False,
            "issues": [
                {
                    "category": "anatomy",
                    "severity": "blocking",
                    "observation": "T-Rex neck and shoulder mass are too primitive.",
                    "evidence": "preview_vs_lookdev_quality_reference",
                },
                {
                    "category": "animation",
                    "severity": "high",
                    "observation": "The roar pose lacks believable weight transfer.",
                    "evidence": "preview_only",
                },
                {
                    "category": "lighting",
                    "severity": "medium",
                    "observation": "Rain backlight is too flat.",
                    "evidence": "preview_vs_lookdev_quality_reference",
                },
            ],
            "patches": [
                {
                    "path": "camera.distance",
                    "operation": "set",
                    "value": 12.5,
                    "reason": "Keep the threat silhouette readable.",
                }
            ],
            "requires_agent": [
                {
                    "agent": "asset_designer",
                    "asset_id": "dino_trex_master",
                    "reason": "Increase continuous neck-to-shoulder mass.",
                    "acceptance_criteria": [
                        "No visible neck-to-torso seam in three-quarter view."
                    ],
                },
                {
                    "agent": "asset_designer",
                    "asset_id": "dino_trex_master",
                    "reason": "Improve oral tissue and eye material response.",
                    "acceptance_criteria": [
                        "Eyes, gums, tongue and teeth remain visually distinct in the hero capture."
                    ],
                },
                {
                    "agent": "animation_director",
                    "asset_id": "anim_trex_roar",
                    "reason": "Add grounded weight transfer to the roar.",
                    "acceptance_criteria": [
                        "Feet stay planted and pelvis motion supports the roar."
                    ],
                },
                {
                    "agent": "environment_designer",
                    "asset_id": "env_tropical_rainforest",
                    "severity": "medium",
                    "reason": "Improve layered wet foliage and rain readability.",
                    "acceptance_criteria": [
                        "Foreground, midground and background foliage read as separate depth layers."
                    ],
                },
            ],
        }

        result = route_critique(self.scenario, critique, self.catalog)
        by_asset = {request["asset_id"]: request for request in result["work_requests"]}

        self.assertEqual(result["deterministic_patch_count"], 1)
        self.assertEqual(result["work_request_count"], 3)
        self.assertEqual(result["deterministic_patches"][0]["path"], "camera.distance")
        self.assertEqual(by_asset["dino_trex_master"]["priority"], "blocking")
        self.assertEqual(len(by_asset["dino_trex_master"]["reasons"]), 2)
        self.assertEqual(by_asset["anim_trex_roar"]["priority"], "high")
        self.assertEqual(by_asset["env_tropical_rainforest"]["priority"], "medium")
        self.assertTrue(
            by_asset["dino_trex_master"]["asset"]["blender_source"].endswith(
                "trex_quality_candidate.blend"
            )
        )

    def test_rejects_unregistered_asset_by_default(self) -> None:
        critique = {
            "shot_id": "shot_005",
            "pass": False,
            "issues": [],
            "patches": [],
            "requires_agent": [
                {
                    "agent": "asset_designer",
                    "asset_id": "dino_unknown_master",
                    "reason": "Unknown asset request.",
                    "acceptance_criteria": ["Exists."],
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "unregistered asset"):
            route_critique(self.scenario, critique, self.catalog)

    def test_writes_machine_manifest_and_individual_astra_requests(self) -> None:
        critique = {
            "shot_id": "shot_005",
            "pass": False,
            "issues": [
                {
                    "category": "anatomy",
                    "severity": "high",
                    "observation": "T-Rex body mass is weak.",
                    "evidence": "preview_vs_lookdev_quality_reference",
                }
            ],
            "patches": [],
            "requires_agent": [
                {
                    "agent": "asset_designer",
                    "asset_id": "dino_trex_master",
                    "reason": "Increase body mass while preserving rig compatibility.",
                    "acceptance_criteria": ["Hero silhouette reads as heavy and continuous."],
                }
            ],
        }
        result = route_critique(
            self.scenario,
            critique,
            self.catalog,
            source_critique="build/critique/raptor_hunt_001/shot_005.result.json",
        )

        with tempfile.TemporaryDirectory() as tmp:
            paths = write_outputs(result, Path(tmp))
            routing = json.loads(paths["routing"].read_text(encoding="utf-8"))
            requests = json.loads(paths["work_requests"].read_text(encoding="utf-8"))
            request_files = list(paths["requests_dir"].glob("*.md"))

            self.assertEqual(routing["shot_id"], "shot_005")
            self.assertEqual(len(requests["requests"]), 1)
            self.assertEqual(len(request_files), 1)
            text = request_files[0].read_text(encoding="utf-8")
            self.assertIn("trex_quality_candidate.blend", text)
            self.assertIn("Recapture `shot_005`", text)
            self.assertIn("FLUX image only as a visual-quality reference", text)


if __name__ == "__main__":
    unittest.main()
