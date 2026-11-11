import unittest

from ai_engine.topic_classifier import classify_topic
from ai_engine.demo_plan import build_demo_plan
from ai_engine.plan_generator import validate_and_normalize


class TopicClassifierTests(unittest.TestCase):

    def test_two_sum_is_classified_as_dsa(self):
        self.assertEqual(classify_topic("Two Sum").family, "dsa")

    def test_kafka_is_not_used_for_two_sum_demo(self):
        plan = build_demo_plan("Two Sum")
        self.assertEqual(plan["topic"], "Two Sum")
        self.assertEqual(plan["topic_family"], "dsa")
        self.assertTrue(any("HashMap" in (b.get("title", "") + b.get("spoken_text", "")) for b in plan["beats"]))
        self.assertFalse(any("Kafka" in b.get("spoken_text", "") for b in plan["beats"]))

    def test_kafka_is_classified_without_fabricating_demo_content(self):
        from ai_engine.demo_plan import CuratedPlanMissing
        self.assertEqual(classify_topic("Apache Kafka").family, "distributed_messaging")
        with self.assertRaises(CuratedPlanMissing):
            build_demo_plan("Apache Kafka")

    def test_topic_mismatch_is_rejected(self):
        plan = build_demo_plan("Two Sum")
        plan["topic"] = "Apache Kafka"
        with self.assertRaises(ValueError) as ctx:
            validate_and_normalize(plan, "Two Sum")
        self.assertIn("Topic lock failed", str(ctx.exception))

    def test_two_sum_content_validator_rejects_old_kafka_plan(self):
        plan = build_demo_plan("Two Sum")
        plan["beats"][0]["spoken_text"] = "Hazaaron applications real time data bhejte hain through Kafka."
        with self.assertRaises(ValueError) as ctx:
            validate_and_normalize(plan, "Two Sum")
        self.assertIn("Kafka concepts detected", str(ctx.exception))

    def test_two_sum_demo_passes_semantic_validator(self):
        plan = build_demo_plan("Two Sum")
        normalized = validate_and_normalize(plan, "Two Sum")
        self.assertEqual(normalized["topic_family"], "dsa")


if __name__ == "__main__":
    unittest.main()

