from __future__ import annotations

import unittest

from ai_engine.critic import evaluate_plan_quality
from ai_engine.demo_plan import build_demo_plan
from ai_engine.plan_generator import validate_and_normalize


class CriticTests(unittest.TestCase):
    def test_demo_plan_passes_critic_quality_gate(self):
        plan = validate_and_normalize(build_demo_plan("Two Sum", 70), "Two Sum")
        report = evaluate_plan_quality(plan)
        self.assertTrue(report.passed)
        self.assertGreaterEqual(report.score, 7.5)
        self.assertGreaterEqual(report.hook_score, 8.0)
        self.assertGreaterEqual(report.intuition_score, 8.0)

    def test_bland_plan_fails_critic(self):
        bland_plan = {
            "title": "Two Sum",
            "topic": "Two Sum",
            "beats": [
                {
                    "id": "beat_1",
                    "type": "concept_visual",
                    "title": "Introduction",
                    "spoken_text": "Today we will study the Two Sum problem from the LeetCode platform.",
                },
                {
                    "id": "beat_2",
                    "type": "summary",
                    "title": "Conclusion",
                    "spoken_text": "Thank you for watching this explanation.",
                },
            ],
        }
        report = evaluate_plan_quality(bland_plan)
        self.assertFalse(report.passed)
        self.assertLess(report.score, 7.5)


if __name__ == "__main__":
    unittest.main()
