from __future__ import annotations

import unittest
from pathlib import Path

from ai_engine.post_inspector import inspect_and_optimize_video


class PostInspectorTests(unittest.TestCase):
    def test_missing_video_fails(self):
        fake_path = Path("output/final/does_not_exist.mp4")
        report = inspect_and_optimize_video(fake_path)
        self.assertFalse(report.passed)
        self.assertIn("does not exist", report.issues[0])

    def test_existing_rendered_mp4_passes_if_available(self):
        output_dir = Path(__file__).resolve().parent.parent / "output" / "final"
        mp4_files = list(output_dir.glob("*.mp4"))
        if not mp4_files:
            self.skipTest("No rendered MP4 available for testing")
        target_mp4 = mp4_files[-1]
        report = inspect_and_optimize_video(target_mp4, auto_normalize_audio=False)
        self.assertTrue(report.passed)
        self.assertEqual(report.width, 1080)
        self.assertEqual(report.height, 1920)
        self.assertTrue(report.has_audio)


if __name__ == "__main__":
    unittest.main()
