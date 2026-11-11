import unittest
from unittest.mock import Mock, patch

from ai_engine.cta import cta_keyword
from ai_engine.demo_plan import CuratedPlanMissing, build_demo_plan
from ai_engine.plan_auditor import audit_and_sanitize
from ai_engine.plan_generator import TopicAlignmentError, _review_topic_alignment, validate_and_normalize
from ai_engine.visual_router import assign_visuals
from audio_engine.tts_text import build_tts_text, hindi_number


class PlanValidationTests(unittest.TestCase):
    @patch("ai_engine.plan_generator.requests.post")
    def test_topic_review_rejects_off_topic_storyboard(self, post: Mock) -> None:
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": '{"is_relevant": false, "reason": "It teaches Two Sum."}'}}]
        }
        post.return_value = response

        with self.assertRaisesRegex(TopicAlignmentError, "It teaches Two Sum"):
            _review_topic_alignment(
                "Valid Anagram",
                {"beats": [{"title": "Two Sum", "spoken_text": "Find the target complement."}]},
                {"Authorization": "Bearer test"},
                "mock-model",
            )

    @patch("ai_engine.plan_generator.requests.post")
    def test_topic_review_accepts_relevant_storyboard(self, post: Mock) -> None:
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": '{"is_relevant": true, "reason": "Explains letter counts."}'}}]
        }
        post.return_value = response

        _review_topic_alignment(
            "Valid Anagram",
            {"beats": [{"title": "Frequency Counts", "spoken_text": "Count each letter."}]},
            {"Authorization": "Bearer test"},
            "mock-model",
        )

    @patch("ai_engine.plan_generator.requests.post", side_effect=OSError("offline"))
    def test_topic_review_fails_closed_when_unavailable(self, _post: Mock) -> None:
        with self.assertRaisesRegex(TopicAlignmentError, "could not verify"):
            _review_topic_alignment(
                "OAuth",
                {"beats": [{"title": "OAuth", "spoken_text": "Tokens."}]},
                {"Authorization": "Bearer test"},
                "mock-model",
            )

    def test_demo_plan_normalizes(self):
        raw = build_demo_plan("Two Sum", 70)
        plan = validate_and_normalize(raw, "Two Sum")
        self.assertGreaterEqual(len(plan["beats"]), 4)
        self.assertEqual(plan["topic"], "Two Sum")
        self.assertTrue(all(beat["spoken_text"] for beat in plan["beats"]))

    def test_demo_rejects_topic_without_curated_plan(self):
        with self.assertRaises(CuratedPlanMissing):
            build_demo_plan("Apache Kafka", 70)

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

    def test_cta_keyword_picks_clean_speakable_word(self):
        self.assertEqual(cta_keyword("Valid Anagram"), "ANAGRAM")
        self.assertEqual(cta_keyword("Database Sharding"), "SHARDING")
        self.assertEqual(cta_keyword("Two Sum"), "SUM")

    def test_tts_text_spells_numbers_and_preserves_hindi_log(self):
        self.assertEqual(hindi_number(26), "छब्बीस")
        self.assertEqual(hindi_number(90), "नब्बे")
        tts = build_tts_text("90% log dono strings sort karte hain — O(n log n) time lagta hai!")
        self.assertIn("नब्बे परसेंट लोग", tts)
        self.assertIn("ओ ऑफ़ एन लॉग एन", tts)
        self.assertNotIn("लॉग दोनों", tts)

    def test_visual_router_rejects_ungrounded_ring_and_gate_on_dsa(self):
        plan = {
            "topic": "Valid Anagram",
            "beats": [
                {
                    "id": "hook",
                    "type": "kinetic_title",
                    "title": "Valid Anagram",
                    "spoken_text": "Interview mein Valid Anagram pucha toh 90% log sort bolte hain.",
                },
                {
                    "id": "model",
                    "type": "architecture_build",
                    "title": "26 Bucket Array",
                    "spoken_text": "26 size ka frequency array banao.",
                    "visual": {"kind": "ring"},
                },
            ],
        }
        assign_visuals(plan)
        self.assertEqual(plan["beats"][0]["visual"]["kind"], "hook")
        self.assertNotEqual(plan["beats"][1]["visual"]["kind"], "ring")

    def test_plan_auditor_strips_leaked_terms_and_unspoken_numbers(self):
        plan = {
            "topic": "Valid Anagram",
            "beats": [
                {
                    "id": "b1",
                    "type": "concept_visual",
                    "title": "26 Bucket Array",
                    "spoken_text": "26 size ka frequency array banao jisme har letter ka count zero ho.",
                    "nodes": [
                        {"label": "26 Buckets", "detail": "Count array"},
                        {"label": "429 Rate Limit", "detail": "Hash Ring Token Bucket"},
                    ],
                    "steps": [],
                    "metric": "HTTP 429 REJECTED",
                }
            ],
        }
        issues = audit_and_sanitize(plan, fix=True)
        self.assertTrue(len(issues) >= 2)
        labels = [n["label"] for n in plan["beats"][0]["nodes"]]
        self.assertEqual(labels, ["26 Buckets"])
        self.assertEqual(plan["beats"][0]["metric"], "")


if __name__ == "__main__":
    unittest.main()
