import json
import tempfile
import unittest
from pathlib import Path

from renderer.timeline import write_render_plan


class TimelineTests(unittest.TestCase):
    def test_local_paths_are_not_serialized(self):
        plan = {"topic": "Test", "beats": [{"id": "a", "audio_file_local": "C:/private/audio.mp3", "audio_file": "audio/a.mp3"}]}
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "plan.json"
            write_render_plan(plan, target)
            saved = json.loads(target.read_text(encoding="utf-8"))
            self.assertNotIn("audio_file_local", saved["beats"][0])
            self.assertEqual(saved["beats"][0]["audio_file"], "audio/a.mp3")


if __name__ == "__main__":
    unittest.main()
