from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_engine.demo_plan import build_demo_plan
from publisher.social_publisher import (
    build_instagram_caption,
    write_instagram_metadata,
    write_youtube_shorts_metadata,
)


class SocialPublisherTests(unittest.TestCase):
    def test_instagram_metadata_generation(self) -> None:
        plan = build_demo_plan("Consistent Hashing", 70)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "ig_meta.txt"
            caption = write_instagram_metadata(plan, dest)
            self.assertTrue(dest.exists())
            text = dest.read_text(encoding="utf-8")
            self.assertIn("HASHING", text)
            self.assertIn("#systemdesign", caption)

    def test_youtube_shorts_metadata_generation(self) -> None:
        plan = build_demo_plan("RAG Architecture", 70)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "yt_meta.txt"
            meta = write_youtube_shorts_metadata(plan, dest)
            self.assertTrue(dest.exists())
            self.assertIn("#shorts", meta["title"])
            self.assertIn("00:00", meta["description"])
            self.assertTrue(len(meta["tags"]) >= 5)


if __name__ == "__main__":
    unittest.main()
