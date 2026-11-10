import unittest

from ai_engine.demo_plan import build_demo_plan
from ai_engine.plan_generator import validate_and_normalize


class PlanValidationTests(unittest.TestCase):
    def test_demo_plan_normalizes(self):
        raw = build_demo_plan("Apache Kafka", 70)
        plan = validate_and_normalize(raw, "Apache Kafka")
        self.assertGreaterEqual(len(plan["beats"]), 4)
        self.assertEqual(plan["topic"], "Apache Kafka")
        self.assertTrue(all(beat["spoken_text"] for beat in plan["beats"]))

    def test_unknown_type_falls_back(self):
        raw = {
            "title": "Test",
            "topic": "Test",
            "beats": [
                {"id": f"b{i}", "type": "made_up", "title": "Beat", "spoken_text": "Some words", "nodes": []}
                for i in range(4)
            ],
        }
        plan = validate_and_normalize(raw, "Test")
        self.assertTrue(all(beat["type"] == "concept_visual" for beat in plan["beats"]))

    def test_empty_speech_is_rejected(self):
        raw = {"beats": [{"id": "b1", "title": "Bad", "spoken_text": ""}]}
        with self.assertRaises(ValueError):
            validate_and_normalize(raw, "Test")


if __name__ == "__main__":
    unittest.main()
