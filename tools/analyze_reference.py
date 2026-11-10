"""Download a reference reel (yt-dlp) and transcribe it (faster-whisper).

Usage:
    python tools/analyze_reference.py <url-or-local-file> [--model small]

Prints transcript, words-per-minute and pause stats so scripts/voice pacing can be
matched to a benchmark creator. Output JSON is saved to output/reference/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "reference"


def download(url: str) -> Path:
    from yt_dlp import YoutubeDL

    OUT.mkdir(parents=True, exist_ok=True)
    opts = {"outtmpl": str(OUT / "%(id)s.%(ext)s"), "format": "mp4/best", "quiet": True}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info))


def transcribe(media: Path, model_size: str) -> dict:
    from faster_whisper import WhisperModel

    import subprocess

    import numpy as np

    # Decode with ffmpeg ourselves; avoids PyAV version incompatibilities.
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(media), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
        capture_output=True, check=True,
    ).stdout
    audio = np.frombuffer(raw, dtype=np.float32)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio, word_timestamps=True, vad_filter=True)
    words = []
    for seg in segments:
        for w in seg.words or []:
            words.append({"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    if not words:
        return {"language": info.language, "words": [], "wpm": 0, "avg_pause": 0}
    span = words[-1]["end"] - words[0]["start"]
    gaps = [b["start"] - a["end"] for a, b in zip(words, words[1:]) if b["start"] - a["end"] > 0.12]
    return {
        "language": info.language,
        "text": " ".join(w["text"] for w in words),
        "words": words,
        "wpm": round(len(words) / span * 60) if span > 0 else 0,
        "avg_pause": round(sum(gaps) / len(gaps), 2) if gaps else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--model", default="small")
    args = parser.parse_args()
    media = Path(args.source) if Path(args.source).exists() else download(args.source)
    result = transcribe(media, args.model)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{media.stem}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"language={result['language']} wpm={result['wpm']} avg_pause={result['avg_pause']}s")
    print(result.get("text", ""))


if __name__ == "__main__":
    main()
