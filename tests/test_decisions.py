import unittest

from worldops.decisions import LayaTriage, RulesTriage


class FakeRouter:
    def predict(self, event, questions):
        return {"answers": {"route": {"choice": "network", "confidence": 0.7}}, "routing": {"model": "fake"}}


class DecisionTests(unittest.TestCase):
    def test_rules_baseline(self):
        self.assertEqual(RulesTriage().triage({"signal": "GPU temperature alert"})["route"], "facility")
        self.assertEqual(RulesTriage().triage({"signal": "mystery"})["route"], "human_review")

    def test_laya_contract_is_triage_only(self):
        result = LayaTriage(FakeRouter()).triage({"signal": "packet loss"})
        self.assertEqual(result["route"], "network")
        self.assertEqual(result["authority"], "TRIAGE_ONLY")
        self.assertEqual(result["calibration"], "not_established_for_worldops")
