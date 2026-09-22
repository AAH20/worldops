import json
import unittest

from worldops.engine import evaluate, plan, validate
from worldops.fixture import make_factory


class PlacementTests(unittest.TestCase):
    def setUp(self):
        self.world = make_factory()

    def test_200_nodes_and_reproducible_receipt(self):
        self.assertEqual(len(self.world["nodes"]), 200)
        self.assertEqual(plan(self.world), plan(self.world))

    def test_baselines_violate_declared_constraints(self):
        for strategy in ("first_fit", "cheapest"):
            result = plan(self.world, strategy)
            self.assertFalse(result["evaluation"]["feasible"])
            self.assertIn("ADVISORY_ONLY", result["authority"])

    def test_worldops_finds_feasible_placement(self):
        result = plan(self.world)
        self.assertTrue(result["evaluation"]["feasible"])
        self.assertEqual(len(result["placements"]), 3)
        self.assertGreater(result["candidate_rejections"], 0)

    def test_cooling_derate_is_enforced(self):
        placement = {"customer-inference": "node-00-00", "model-training": "node-02-00", "batch-embeddings": "node-03-00"}
        constraints = {v["constraint"] for v in evaluate(self.world, placement)["violations"]}
        self.assertIn("cooling", constraints)

    def test_invalid_world_rejected(self):
        broken = json.loads(json.dumps(self.world))
        broken["nodes"][0]["rack"] = "missing"
        with self.assertRaises(ValueError):
            validate(broken)


if __name__ == "__main__":
    unittest.main()
