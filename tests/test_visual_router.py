import unittest

from ai_engine.demo_plan import ANAGRAM_SCAN
from ai_engine.visual_router import assign_visuals


class VisualRouterTests(unittest.TestCase):
    def test_curated_anagram_scan_keeps_renderer_supported_schema(self):
        plan = {
            "topic": "Valid Anagram",
            "beats": [{"id": "counts", "type": "concept_visual", "spoken_text": "Count each letter.", "visual": ANAGRAM_SCAN}],
        }
        assign_visuals(plan, "curated")
        beat = plan["beats"][0]
        self.assertEqual(beat["visual"]["kind"], "scan")
        self.assertIn("cells", beat["visual"]["data"]["rows"][0])
        self.assertIn("key", beat["visual"]["data"]["buckets"][0])
        self.assertIsInstance(beat["visual"]["data"]["banner"], str)

    def test_ai_topic_cannot_select_anagram_specific_scan(self):
        plan = {
            "topic": "OAuth",
            "beats": [{
                "id": "flow",
                "type": "concept_visual",
                "spoken_text": "The client exchanges a code for a token.",
                "nodes": [{"label": "Client"}, {"label": "Token endpoint"}],
                "visual": {"kind": "scan", "data": {"rows": [{"cells": ["x"]}]}},
            }],
        }
        assign_visuals(plan, "llm")
        self.assertEqual(plan["beats"][0]["visual"]["kind"], "stages")

    def test_new_topic_routes_from_beat_data_without_topic_specific_guess(self):
        plan = {
            "topic": "OAuth Device Flow",
            "beats": [{
                "id": "exchange",
                "type": "concept_visual",
                "spoken_text": "A short code connects the device to the user.",
                "nodes": [{"label": "Device code"}, {"label": "User approval"}],
            }],
        }
        assign_visuals(plan, "llm")
        self.assertEqual(plan["beats"][0]["visual"]["kind"], "stages")


if __name__ == "__main__":
    unittest.main()
