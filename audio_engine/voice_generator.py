from __future__ import annotations

import asyncio
import math
import re
import shutil
from pathlib import Path
from typing import Any

import edge_tts


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)[:60]


async def _synthesize(text: str, output_path: Path, voice: str, rate: str) -> tuple[list[dict[str, Any]], float]:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, boundary="WordBoundary")
    words: list[dict[str, Any]] = []
    audio_parts: list[bytes] = []
    async for chunk in communicate.stream():
        kind = chunk.get("type")
        if kind == "audio":
            audio_parts.append(chunk.get("data", b""))
        elif kind == "WordBoundary":
            offset = float(chunk.get("offset", 0)) / 10_000_000
            duration = float(chunk.get("duration", 0)) / 10_000_000
            words.append({
                "text": str(chunk.get("text", "")),
                "start": round(offset, 3),
                "end": round(offset + duration, 3),
            })
    if not audio_parts:
        raise RuntimeError("Edge TTS returned no audio data")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        for part in audio_parts:
            handle.write(part)
    estimated_duration = max((w["end"] for w in words), default=0.0)
    return words, estimated_duration


def _rate_to_int(rate: str) -> int:
    try:
        return int(rate.replace("%", "").replace("+", ""))
    except ValueError:
        return 0


def _split_phrases(text: str) -> list[str]:
    """Split narration into sentence-like phrases so each gets its own delivery."""
    parts = re.split(r"(?<=[.!?:—।])\s+", text.strip())
    return [p for p in (s.strip() for s in parts) if p]


def _phrase_prosody(phrase: str, position: int, total: int, base_rate: int) -> tuple[str, str]:
    """Vary rate/pitch like a real speaker: energetic creator cadence (~180 WPM)."""
    rate, pitch = base_rate, 0
    if phrase.endswith("!"):
        rate += 5
        pitch += 4
    elif phrase.endswith("?"):
        rate += 2
        pitch += 3
    elif position == total - 1 and total > 1:
        rate -= 2
        pitch -= 1
    if position % 2 == 1:
        pitch -= 1  # avoid a metronomic, repeated contour
    return f"{rate:+d}%", f"{pitch:+d}Hz"


def _pause_after(phrase: str) -> float:
    if phrase.endswith("?"):
        return 0.16
    if phrase.endswith("!"):
        return 0.10
    return 0.12


def _align_words_whisper_or_proportional(text: str, audio_path: Path, duration: float) -> list[dict[str, Any]]:
    """Extract word timings via faster-whisper when available, mapped cleanly to spoken_text tokens."""
    tokens = re.findall(r"\S+", text)
    if not tokens:
        return []
    try:
        import subprocess
        import numpy as np
        from faster_whisper import WhisperModel

        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            raw = subprocess.run(
                [ffmpeg, "-v", "error", "-i", str(audio_path), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                capture_output=True, check=True,
            ).stdout
            audio_np = np.frombuffer(raw, dtype=np.float32)
            model = getattr(_align_words_whisper_or_proportional, "_model", None)
            if model is None:
                model = WhisperModel("small", device="cpu", compute_type="int8")
                setattr(_align_words_whisper_or_proportional, "_model", model)
            segments, _ = model.transcribe(audio_np, word_timestamps=True, vad_filter=True)
            w_timings = [w for seg in segments for w in (seg.words or [])]
            if len(w_timings) == len(tokens):
                return [
                    {"text": tok, "start": round(float(w.start), 3), "end": round(float(w.end), 3)}
                    for tok, w in zip(tokens, w_timings)
                ]
            if w_timings:
                m = len(w_timings)
                n = len(tokens)
                aligned: list[dict[str, Any]] = []
                for i, tok in enumerate(tokens):
                    pos_s = (i / n) * m
                    pos_e = ((i + 1) / n) * m
                    idx_s = min(m - 1, int(pos_s))
                    idx_e = min(m - 1, max(idx_s, int(pos_e - 1e-6)))
                    frac_s = pos_s - idx_s
                    w_s = w_timings[idx_s]
                    start_t = float(w_s.start) + frac_s * max(0.0, float(w_s.end) - float(w_s.start))
                    w_e = w_timings[idx_e]
                    frac_e = min(1.0, max(0.1, pos_e - idx_e))
                    end_t = float(w_e.start) + frac_e * max(0.02, float(w_e.end) - float(w_e.start))
                    if end_t <= start_t:
                        end_t = start_t + 0.08
                    aligned.append({"text": tok, "start": round(start_t, 3), "end": round(end_t, 3)})
                return aligned
    except Exception:
        pass
    slot = duration / max(len(tokens), 1)
    return [
        {"text": token, "start": round(i * slot, 3), "end": round((i + 1) * slot, 3)}
        for i, token in enumerate(tokens)
    ]


def _try_elevenlabs(spoken_script: str, caption_text: str, output_path: Path) -> tuple[list[dict[str, Any]], float] | None:
    """Attempt synthesis via ElevenLabs Multilingual v2 API when ELEVENLABS_API_KEY is configured."""
    import os
    import requests

    provider = os.getenv("TTS_PROVIDER", "auto").strip().lower()
    if provider not in ("elevenlabs", "auto"):
        return None
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        return None
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "TX3LPaxmHKxFdv7VOQHJ").strip() or "TX3LPaxmHKxFdv7VOQHJ"
    model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip() or "eleven_multilingual_v2"
    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={
                "text": spoken_script,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.40,
                    "similarity_boost": 0.82,
                    "style": 0.40,
                    "use_speaker_boost": True,
                },
            },
            timeout=(5.0, 90.0),
        )
        if resp.status_code == 200 and len(resp.content) > 1000:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(resp.content)
            dur = _probe_duration(output_path)
            words = _align_words_whisper_or_proportional(caption_text, output_path, dur)
            print(f"    [ElevenLabs] Synthesized ({model_id}/{voice_id}) -> {dur:.2f}s")
            return words, dur
        print(f"    [ElevenLabs] HTTP {resp.status_code}: {resp.text[:160]}")
    except Exception as exc:
        print(f"    [ElevenLabs] Error: {exc}")
    return None


_DIGIT_WORDS = {"0": "ज़ीरो", "1": "वन", "2": "टू", "3": "थ्री", "4": "फ़ोर", "5": "फ़ाइव",
                "6": "सिक्स", "7": "सेवन", "8": "एट", "9": "नाइन"}


def _load_pronunciations() -> list[tuple["re.Pattern[str]", str]]:
    import json
    import re as _re
    path = Path(__file__).with_name("pronunciations.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rules = []
    # Longest phrases first so "Shard Key" wins over "Shard"
    for src, dst in sorted(((k, v) for k, v in data.items() if not k.startswith("_")), key=lambda kv: -len(kv[0])):
        if src.isalnum() or _re.fullmatch(r"[\w\- ]+", src):
            pat = _re.compile(r"(?<![\w])" + _re.escape(src) + r"(?![\w])", _re.IGNORECASE)
        else:
            pat = _re.compile(_re.escape(src), _re.IGNORECASE)
        rules.append((pat, dst))
    return rules


def apply_tts_pronunciations(text: str) -> str:
    """Rewrite English/tech tokens into Devanagari phonetics so Sarvam pronounces them correctly."""
    import re as _re
    out = text
    # Standard Big-O pronunciations in Devanagari
    out = _re.sub(r"\bO\s*\(?\s*[nN]\s*log\s*[nN]\s*\)?\b", "ओ ऑफ़ एन लॉग एन", out, flags=_re.I)
    out = _re.sub(r"\bO\s*\(?\s*[nN]\s*\)?\b", "ओ ऑफ़ एन", out)
    out = _re.sub(r"\bO\s*\(?\s*1\s*\)?\b", "ओ ऑफ़ वन", out)
    out = _re.sub(r"\bO\s+1\b", "ओ ऑफ़ वन", out)
    out = _re.sub(r"\bO\s+[nN]\b", "ओ ऑफ़ एन", out)
    # Clean quotes and parentheses that break pronunciation boundaries
    out = _re.sub(r"['\"]", " ", out)
    out = _re.sub(r"[()]", " ", out)
    # "Shard-2" / "DB-1" -> "Shard टू" (hyphen+digit glued tokens get misread)
    out = _re.sub(r"(?<=[A-Za-z])-(\d)\b", lambda m: " " + _DIGIT_WORDS[m.group(1)], out)
    # Common digit replacements for Hindi TTS
    out = _re.sub(r"\b26\b", "छब्बीस", out)
    out = _re.sub(r"\b90%\b", "नब्बे परसेंट", out)
    out = _re.sub(r"\b100%\b", "सौ परसेंट", out)
    for pat, dst in _load_pronunciations():
        out = pat.sub(dst, out)
    out = out.replace("—", ", ").replace("·", ", ")
    out = _re.sub(r"\s+,", ",", out)
    return _re.sub(r"\s{2,}", " ", out).strip()


def _leftover_latin_words(text: str) -> list[str]:
    import re as _re
    return sorted(set(_re.findall(r"[A-Za-z][A-Za-z_\-]*[A-Za-z]|[A-Za-z]", text)))


def _llm_transliterate(words: list[str]) -> dict[str, str]:
    """Ask the configured LLM for Devanagari phonetic spellings of leftover English words."""
    import json
    import os
    import requests
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("FREELLM_API_KEY")
    if not api_key or not words:
        return {}
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = (
        "Convert each English/tech word into how an Indian software engineer pronounces it, written in "
        "Devanagari script. Spell acronyms letter by letter (IOPS -> आई ओ पी एस). Return ONLY a JSON object "
        "mapping the exact input word to its Devanagari spelling.\nWords: " + json.dumps(words)
    )
    try:
        resp = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "temperature": 0, "response_format": {"type": "json_object"},
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        resp.raise_for_status()
        data = json.loads(resp.json()["choices"][0]["message"]["content"])
        return {k: str(v) for k, v in data.items() if isinstance(k, str) and v and k in words}
    except Exception as exc:
        print(f"    [pronunciation] LLM transliteration unavailable ({exc})")
        return {}


def ensure_pronounceable(text: str) -> str:
    """Pronunciation quality gate: no raw English token may reach the Hindi TTS voice.

    1. Apply pronunciations.json rules.
    2. If the text was written in Devanagari script and still has leftover English words,
       auto-transliterate them via LLM and save into pronunciations.json.
    """
    import json
    import os
    has_devanagari_input = bool(re.search(r"[\u0900-\u097F]", text))
    out = apply_tts_pronunciations(text)
    if not has_devanagari_input:
        return out
    leftovers = _leftover_latin_words(out)
    if leftovers and os.getenv("TTS_AUTO_LEARN", "0") == "1":
        learned = _llm_transliterate(leftovers)
        if learned:
            path = Path(__file__).with_name("pronunciations.json")
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                data.update(learned)
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"    [pronunciation] Learned {len(learned)} new words: " + ", ".join(f"{k}->{v}" for k, v in learned.items()))
            except Exception as exc:
                print(f"    [pronunciation] Could not save learned words ({exc})")
            out = apply_tts_pronunciations(text)
            for k, v in learned.items():
                out = out.replace(k, v)
        leftovers = _leftover_latin_words(out)
    if leftovers:
        msg = f"English words would be mispronounced by the Hindi voice: {', '.join(leftovers)}. Add them to audio_engine/pronunciations.json"
        if os.getenv("PRONUNCIATION_STRICT", "0") == "1":
            raise RuntimeError(f"[pronunciation-gate] {msg}")
        pass  # Latin leftovers are tolerated; the STT verifier decides whether the take is acceptable
    else:
        print("    [pronunciation] OK: 100% Devanagari phonetic script sent to TTS")
    return out


def _split_for_tts(script: str, limit: int = 450) -> list[str]:
    """Split on sentence boundaries so no clip exceeds the API limit (old code silently cut at 500 chars)."""
    if len(script) <= limit:
        return [script]
    sentences = re.split(r"(?<=[।.!?])\s+", script)
    chunks: list[str] = []
    cur = ""
    for s in sentences:
        if cur and len(cur) + len(s) + 1 > limit:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def _sarvam_request(script: str, pace: float) -> bytes | None:
    import base64
    import os
    import requests

    resp = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        headers={"api-subscription-key": os.getenv("SARVAM_API_KEY", "").strip(), "Content-Type": "application/json"},
        json={
            "inputs": [script],
            "target_language_code": "hi-IN",
            "speaker": os.getenv("SARVAM_VOICE", "shubh").strip().lower() or "shubh",
            "model": os.getenv("SARVAM_MODEL", "bulbul:v3").strip() or "bulbul:v3",
            "pace": pace,
            "enable_preprocessing": os.getenv("SARVAM_PREPROCESS", "1") == "1",
        },
        timeout=(5.0, 60.0),
    )
    if resp.status_code == 200:
        audios = resp.json().get("audios", [])
        if audios:
            return base64.b64decode(audios[0])
    print(f"    [SarvamAI] HTTP {resp.status_code}: {resp.text[:160]}")
    return None


def _sarvam_synthesize_wav(script: str, pace: float, work: Path) -> bytes | None:
    """Synthesize the whole script (possibly in chunks) and return one WAV."""
    chunks = _split_for_tts(script)
    blobs = [_sarvam_request(c, pace) for c in chunks]
    if any(b is None for b in blobs):
        return None
    if len(blobs) == 1:
        return blobs[0]
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    import subprocess

    parts = []
    for i, blob in enumerate(blobs):
        p = work.with_name(f"{work.stem}_chunk{i}.wav")
        p.write_bytes(blob)  # type: ignore[arg-type]
        parts.append(p)
    lst = work.with_name(f"{work.stem}_chunks.txt")
    lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts), encoding="utf-8")
    merged = work.with_name(f"{work.stem}_merged.wav")
    subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(merged)],
                   capture_output=True, check=False)
    data = merged.read_bytes() if merged.exists() else None
    for p in [*parts, lst, merged]:
        p.unlink(missing_ok=True)
    return data


def _sarvam_wav_to_mp3(wav_bytes: bytes, output_path: Path) -> bool:
    """Convert Sarvam WAV output to the MP3 format used by the renderer's audio paths."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("    [SarvamAI] ffmpeg is required to convert WAV output to the renderer's MP3 format")
        return False
    import subprocess

    wav_path = output_path.with_name(f"{output_path.stem}.sarvam-tmp.wav")
    mp3_path = output_path.with_name(f"{output_path.stem}.sarvam-tmp.mp3")
    try:
        wav_path.write_bytes(wav_bytes)
        result = subprocess.run(
            [ffmpeg, "-y", "-v", "error", "-i", str(wav_path), "-codec:a", "libmp3lame", "-q:a", "3", str(mp3_path)],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0 or not mp3_path.exists() or mp3_path.stat().st_size < 100:
            detail = result.stderr.decode("utf-8", errors="replace")[-240:]
            print(f"    [SarvamAI] WAV-to-MP3 conversion failed: {detail}")
            return False
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mp3_path.replace(output_path)
        return True
    except OSError as exc:
        print(f"    [SarvamAI] WAV-to-MP3 conversion failed: {exc}")
        return False
    finally:
        wav_path.unlink(missing_ok=True)
        mp3_path.unlink(missing_ok=True)


AUDIO_CHECKS: dict[str, dict[str, Any]] = {}
VERIFY_PASS = 0.85
VERIFY_FLOOR = 0.60


def _try_sarvam_tts(tts_script: str, caption_text: str, output_path: Path) -> tuple[list[dict[str, Any]], float] | None:
    """Sarvam synthesis with objective QA: transcribe the take, score it, retry at other paces, keep the best."""
    import os

    provider = os.getenv("TTS_PROVIDER", "auto").strip().lower()
    if provider in ("edge", "voicestudio", "elevenlabs") or not os.getenv("SARVAM_API_KEY", "").strip():
        return None

    from audio_engine.audio_verifier import verify_clip

    script = ensure_pronounceable(tts_script)
    base_pace = float(os.getenv("SARVAM_PACE", "1.0"))
    paces = list(dict.fromkeys([base_pace, 1.0, 0.94, 0.88]))
    verify = os.getenv("VERIFY_AUDIO", "1") == "1"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    best_bytes: bytes | None = None
    best: dict[str, Any] = {"score": -1.0}
    attempts: list[dict[str, Any]] = []
    try:
        for pace in paces:
            wav_bytes = _sarvam_synthesize_wav(script, pace, output_path)
            if wav_bytes is None:
                continue
            if not _sarvam_wav_to_mp3(wav_bytes, output_path):
                return None
            check = verify_clip(output_path, script) if verify else None
            if check is None:
                best_bytes, best = output_path.read_bytes(), {"score": None, "transcript": None, "pace": pace}
                attempts.append({"pace": pace, "score": None})
                break
            attempts.append({"pace": pace, "score": check["score"]})
            if best_bytes is None or check["score"] > (best["score"] or -1):
                best_bytes, best = output_path.read_bytes(), {**check, "pace": pace}
            if check["score"] >= VERIFY_PASS:
                break
            print(f"    [audio-verify] take @pace {pace}: score {check['score']} < {VERIFY_PASS}; retrying")
    except Exception as exc:
        print(f"    [SarvamAI] Error: {exc}")
    if best_bytes is None:
        return None

    output_path.write_bytes(best_bytes)
    score = best.get("score")
    AUDIO_CHECKS[output_path.name] = {"expected": script, "attempts": attempts, **best}
    if score is not None and score < VERIFY_FLOOR and os.getenv("VERIFY_AUDIO_STRICT", "1") == "1":
        raise RuntimeError(
            f"[audio-verify] {output_path.name} still mispronounced after {len(attempts)} takes "
            f"(best score {score}). Expected: {script!r} | Heard: {best.get('transcript')!r}"
        )
    dur = _probe_duration(output_path)
    words = _align_words_whisper_or_proportional(caption_text, output_path, dur)
    tag = "unverified" if score is None else f"verified {score}"
    print(f"    [SarvamAI] Synthesized -> {dur:.2f}s ({tag}, pace {best.get('pace')})")
    return words, dur


def _try_voicestudio(text: str, output_path: Path) -> tuple[list[dict[str, Any]], float] | None:
    """Attempt synthesis via local VoiceStudio OpenAI-compatible API (/v1/audio/speech)."""
    import os
    import requests

    provider = os.getenv("TTS_PROVIDER", "auto").strip().lower()
    if provider in ("edge", "elevenlabs"):
        return None

    candidate_urls = [
        os.getenv("VOICESTUDIO_URL", "").strip().rstrip("/"),
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3900",
    ]
    seen: set[str] = set()
    urls = [u for u in candidate_urls if u and not (u in seen or seen.add(u))]
    voice_name = os.getenv("VOICESTUDIO_VOICE", "expr-voice-3-m").strip() or "expr-voice-3-m"
    model_name = os.getenv("VOICESTUDIO_MODEL", "kittentts").strip() or "kittentts"
    speed = float(os.getenv("VOICESTUDIO_SPEED", "1.10"))
    api_key = os.getenv("VOICESTUDIO_API_KEY", "").strip()

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    for base_url in urls:
        try:
            resp = requests.post(
                f"{base_url}/v1/audio/speech",
                headers=headers,
                json={
                    "model": model_name,
                    "input": text,
                    "voice": voice_name,
                    "response_format": "mp3",
                    "speed": speed,
                },
                timeout=(3.0, 240),
            )
            if resp.status_code == 200 and len(resp.content) > 1000:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(resp.content)
                dur = _probe_duration(output_path)
                words = _align_words_whisper_or_proportional(text, output_path, dur)
                print(f"    [VoiceStudio] Synthesized via {base_url} ({model_name}/{voice_name}) -> {dur:.2f}s")
                return words, dur
        except Exception:
            continue
    return None


async def _synth_phrase(text: str, out: Path, voice: str, rate: str, pitch: str) -> tuple[list[dict[str, Any]], float]:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words: list[dict[str, Any]] = []
    parts: list[bytes] = []
    async for chunk in communicate.stream():
        kind = chunk.get("type")
        if kind == "audio":
            parts.append(chunk.get("data", b""))
        elif kind == "WordBoundary":
            offset = float(chunk.get("offset", 0)) / 10_000_000
            duration = float(chunk.get("duration", 0)) / 10_000_000
            words.append({"text": str(chunk.get("text", "")), "start": offset, "end": offset + duration})
    if not parts:
        raise RuntimeError("Edge TTS returned no audio data")
    out.write_bytes(b"".join(parts))
    return words, max((w["end"] for w in words), default=0.0)


def _map_phrase_words_to_caption_tokens(
    tts_words: list[dict[str, Any]],
    caption_phrase: str,
    clip_duration: float,
    cursor: float,
) -> list[dict[str, Any]]:
    rom_tokens = re.findall(r"\S+", caption_phrase)
    if not rom_tokens:
        return []
    if len(tts_words) == len(rom_tokens):
        return [
            {
                "text": tok,
                "start": round(cursor + float(w["start"]), 3),
                "end": round(cursor + float(w["end"]), 3),
            }
            for tok, w in zip(rom_tokens, tts_words)
        ]
    span_start = float(tts_words[0]["start"]) if tts_words else 0.0
    span_end = max(float(tts_words[-1]["end"]), clip_duration * 0.94) if tts_words else clip_duration
    span = max(span_end - span_start, 0.2)
    slot = span / len(rom_tokens)
    return [
        {
            "text": tok,
            "start": round(cursor + span_start + j * slot, 3),
            "end": round(cursor + span_start + (j + 1) * slot, 3),
        }
        for j, tok in enumerate(rom_tokens)
    ]


def _synthesize_human(
    text: str,
    output_path: Path,
    work_dir: Path,
    voice: str,
    rate: str,
    index: int,
    tts_text: str | None = None,
) -> tuple[list[dict[str, Any]], float]:
    """Try local VoiceStudio (/v1/audio/speech) first, then phrase-by-phrase Edge TTS with varied prosody."""
    import subprocess

    spoken_script = (tts_text or text).strip()
    sarvam_res = _try_sarvam_tts(spoken_script, text, output_path)
    if sarvam_res is not None:
        return sarvam_res

    el_res = _try_elevenlabs(spoken_script, text, output_path)
    if el_res is not None:
        return el_res

    vs_res = _try_voicestudio(spoken_script, output_path)
    if vs_res is not None:
        _, dur = vs_res
        words = _align_words_whisper_or_proportional(text, output_path, dur)
        return words, dur

    ffmpeg = shutil.which("ffmpeg")
    phrases_tts = _split_phrases(spoken_script)
    phrases_rom = _split_phrases(text)
    if len(phrases_tts) != len(phrases_rom):
        phrases_tts = [spoken_script]
        phrases_rom = [text]
    if not ffmpeg or len(phrases_tts) < 2:
        words, dur = asyncio.run(_synthesize(spoken_script, output_path, voice, rate))
        if tts_text and tts_text != text:
            words = _map_phrase_words_to_caption_tokens(words, text, dur, 0.0)
        return words, dur

    base = _rate_to_int(rate)
    clips: list[Path] = []
    all_words: list[dict[str, Any]] = []
    cursor = 0.0
    for i, (phrase_tts, phrase_rom) in enumerate(zip(phrases_tts, phrases_rom)):
        p_rate, p_pitch = _phrase_prosody(phrase_rom, i, len(phrases_tts), base)
        clip = work_dir / f"_tmp_{index:02d}_{i}.mp3"
        words, _ = asyncio.run(_synth_phrase(phrase_tts, clip, voice, p_rate, p_pitch))
        clip_duration = _probe_duration(clip)
        if tts_text and tts_text != text:
            all_words.extend(_map_phrase_words_to_caption_tokens(words, phrase_rom, clip_duration, cursor))
        else:
            for w in words:
                all_words.append({"text": w["text"], "start": round(cursor + w["start"], 3), "end": round(cursor + w["end"], 3)})
        clips.append(clip)
        cursor += clip_duration
        if i < len(phrases_tts) - 1:
            gap = _pause_after(phrase_rom)
            silence = work_dir / f"_tmp_{index:02d}_{i}_gap.mp3"
            subprocess.run(
                [ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(gap), "-q:a", "9", str(silence)],
                capture_output=True, check=False,
            )
            clips.append(silence)
            cursor += gap

    list_file = work_dir / f"_tmp_{index:02d}_list.txt"
    list_file.write_text("\n".join(f"file '{c.as_posix()}'" for c in clips), encoding="utf-8")
    result = subprocess.run(
        [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-ar", "24000", "-b:a", "96k", str(output_path)],
        capture_output=True, check=False,
    )
    for c in clips + [list_file]:
        c.unlink(missing_ok=True)
    if result.returncode != 0 or not output_path.exists():
        return asyncio.run(_synthesize(spoken_script, output_path, voice, rate))
    return all_words, cursor


def generate_beat_audio(plan: dict[str, Any], root: Path, run_dir: Path, voice: str, rate: str, fps: int) -> dict[str, Any]:
    audio_dir = run_dir / "audio"
    public_audio_dir = root / "my-video" / "public" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    public_audio_dir.mkdir(parents=True, exist_ok=True)
    # Clean up only past beat audio files, preserving background music
    for old in public_audio_dir.glob("[0-9]*_*.mp3"):
        old.unlink(missing_ok=True)

    beats = plan["beats"]
    from audio_engine.tts_text import build_tts_text

    for index, beat in enumerate(beats, start=1):
        beat_id = _safe_id(beat["id"])
        filename = f"{index:02d}_{beat_id}.mp3"
        source = audio_dir / filename
        # Single source of truth: the voice script is ALWAYS derived from the caption narration.
        beat["tts_text"] = build_tts_text(beat["spoken_text"])
        words, estimated = _synthesize_human(
            beat["spoken_text"],
            source,
            audio_dir,
            voice,
            rate,
            index,
            tts_text=beat.get("tts_text"),
        )
        beat["audio_check"] = AUDIO_CHECKS.get(filename)
        public_file = public_audio_dir / filename
        shutil.copy2(source, public_file)
        duration = _probe_duration(source)
        if duration <= 0:
            duration = estimated
        if duration <= 0:
            raise RuntimeError(f"Could not determine audio duration for beat {beat_id}")
        if not words:
            # Fallback caption timing if the speech service omits word-boundary events.
            tokens = re.findall(r"\S+", beat["spoken_text"])
            slot = duration / max(len(tokens), 1)
            words = [
                {"text": token, "start": round(i * slot, 3), "end": round((i + 1) * slot, 3)}
                for i, token in enumerate(tokens)
            ]
        beat["audio_file"] = f"audio/{filename}"
        beat["audio_duration_seconds"] = round(duration, 3)
        beat["word_timings"] = words
        beat["duration_frames"] = math.ceil(duration * fps) + 8
    plan["fps"] = fps
    plan.setdefault("width", 1080)
    plan.setdefault("height", 1920)
    plan["total_duration_frames"] = sum(int(b["duration_frames"]) for b in beats)
    plan["duration_seconds"] = round(plan["total_duration_frames"] / fps, 2)
    import json as _json

    report = [{"beat": b["id"], "narration": b["spoken_text"], "voice_script": b["tts_text"],
               "check": b.get("audio_check")} for b in beats]
    (run_dir / "audio_report.json").write_text(_json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan


def _probe_duration(path: Path) -> float:
    """Probe audio duration via ffprobe, then fall back to file-size estimation."""
    executable = shutil.which("ffprobe")
    if executable:
        import subprocess
        result = subprocess.run(
            [executable, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=False,
        )
        try:
            value = float(result.stdout.strip()) if result.returncode == 0 else 0.0
            if value > 0:
                return value
        except ValueError:
            pass
    # Fallback: estimate from file size using typical MP3 bitrate (128 kbps)
    try:
        size_bytes = path.stat().st_size
        if size_bytes > 0:
            estimated = size_bytes / (128 * 1024 / 8)  # bytes / (bits/s / 8)
            return max(0.5, round(estimated, 3))
    except OSError:
        pass
    return 0.0
