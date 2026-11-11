import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from audio_engine.audio_verifier import transcribe


class AudioVerifierTests(unittest.TestCase):
    @patch("requests.post")
    def test_transcribe_uses_mime_matching_audio_extension(self, post: Mock) -> None:
        response = Mock(status_code=200)
        response.json.return_value = {"transcript": "नमस्ते"}
        post.return_value = response
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"SARVAM_API_KEY": "test-key"}):
            path = Path(tmp) / "voice.mp3"
            path.write_bytes(b"test")
            self.assertEqual(transcribe(path), "नमस्ते")
        uploaded = post.call_args.kwargs["files"]["file"]
        self.assertEqual(uploaded[2], "audio/mpeg")


if __name__ == "__main__":
    unittest.main()
