"""Objective audio QA: transcribe the generated voice and compare it with what it should have said.

Instead of hoping the TTS pronounced everything right, every beat clip is sent to Sarvam
speech-to-text and the transcript is scored against the expected narration. Low-scoring takes
are re-synthesised by the caller; the best take wins and the result is stored in the plan.
"""
from __future__ import annotations

import difflib
import mimetypes
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

STT_URL = "https://api.sarvam.ai/speech-to-text"


def _expand_numbers(text: str) -> str:
    """STT may write 26 / 90% while the script says छब्बीस / नब्बे परसेंट - compare in words."""
    from audio_engine.tts_text import hindi_number

    text = re.sub(r"(\d+)\s*%", lambda m: hindi_number(int(m.group(1))) + " परसेंट", text or "")
    return re.sub(r"\d+", lambda m: hindi_number(int(m.group(0))), text)


def _norm(text: str) -> str:
    """Normalise Devanagari/Latin text so spelling variants of the same sound compare equal."""
    text = unicodedata.normalize("NFC", _expand_numbers(text)).lower()
    text = text.replace("\u093c", "")                      # nukta: फ़ == फ
    text = text.replace("\u0901", "\u0902")                # chandrabindu -> anusvara
    text = re.sub(r"[\u200c\u200d]", "", text)             # zero-width joiners
    text = re.sub(r"[^\w\s\u0900-\u097f]", " ", text)      # punctuation
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def similarity(expected: str, transcript: str) -> float:
    """0..1 score mixing character-level similarity and word recall."""
    e, t = _norm(expected), _norm(transcript)
    if not e or not t:
        return 0.0
    char_ratio = difflib.SequenceMatcher(None, e.replace(" ", ""), t.replace(" ", "")).ratio()
    t_words = t.split()
    hits = 0
    for w in e.split():
        best = max((difflib.SequenceMatcher(None, w, tw).ratio() for tw in t_words), default=0.0)
        if best >= 0.72:
            hits += 1
    recall = hits / max(1, len(e.split()))
    return round(0.5 * char_ratio + 0.5 * recall, 3)


def transcribe(audio_path: Path, language: str = "hi-IN") -> str | None:
    """Return the transcript, or None when STT is unavailable (no key/network)."""
    import requests

    api_key = os.getenv("SARVAM_API_KEY", "").strip()
    if not api_key:
        return None
    mime_type = mimetypes.guess_type(audio_path.name)[0] or "application/octet-stream"
    try:
        with open(audio_path, "rb") as fh:
            resp = requests.post(
                STT_URL,
                headers={"api-subscription-key": api_key},
                files={"file": (audio_path.name, fh, mime_type)},
                data={"model": os.getenv("SARVAM_STT_MODEL", "saarika:v2.5"), "language_code": language},
                timeout=(5.0, 90.0),
            )
        if resp.status_code == 200:
            return str(resp.json().get("transcript", "")).strip()
        print(f"    [audio-verify] STT HTTP {resp.status_code}: {resp.text[:140]}")
    except Exception as exc:
        print(f"    [audio-verify] STT unavailable ({exc})")
    return None


def verify_clip(audio_path: Path, expected_text: str) -> dict[str, Any] | None:
    transcript = transcribe(audio_path)
    if transcript is None:
        return None
    return {"score": similarity(expected_text, transcript), "transcript": transcript}
