"""Deterministic spoken-script builder: caption text -> text sent to the TTS engine.

Why this exists: the LLM used to write `spoken_text` (captions) and `tts_text` (voice) as two
independent strings, so the voice could say something different from what the screen shows.
Now the LLM writes ONE narration (`spoken_text`) and the voice script is derived from it here,
so captions, voice and visuals can never drift apart.
"""
from __future__ import annotations

import re

_UNITS = (
    "ज़ीरो एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस "
    "बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस "
    "छत्तीस सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चौवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस "
    "उनचास पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरसठ चौंसठ पैंसठ "
    "छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उनासी "
    "अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे इक्यानवे बानवे तिरानवे चौरानवे "
    "पंचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे"
).split()
assert len(_UNITS) == 100, len(_UNITS)


def hindi_number(n: int) -> str:
    """Spell an integer the way it is spoken in Hindi (supports up to arab)."""
    if n < 0:
        return "माइनस " + hindi_number(-n)
    if n < 100:
        return _UNITS[n]
    parts: list[str] = []
    for size, word in ((10**7, "करोड़"), (10**5, "लाख"), (1000, "हज़ार"), (100, "सौ")):
        if n >= size:
            parts.append(f"{hindi_number(n // size)} {word}")
            n %= size
    if n:
        parts.append(_UNITS[n])
    return " ".join(parts)


_BIG_O = [
    (re.compile(r"\bO\s*\(\s*n\s*(?:\^|\*\*)\s*2\s*\)|\bO\s*\(\s*n²\s*\)|\bO\s*\(\s*n\s*square\s*\)", re.I), "ओ ऑफ़ एन स्क्वायर"),
    (re.compile(r"\bO\s*\(\s*n\s*log\s*n\s*\)|\bO\s+of\s+n\s+log\s+n\b", re.I), "ओ ऑफ़ एन लॉग एन"),
    (re.compile(r"\bO\s*\(\s*log\s*n\s*\)|\bO\s+of\s+log\s+n\b", re.I), "ओ ऑफ़ लॉग एन"),
    (re.compile(r"\bO\s*\(\s*1\s*\)|\bO\s+of\s+(?:1|one)\b", re.I), "ओ ऑफ़ वन"),
    (re.compile(r"\bO\s*\(\s*n\s*\)|\bO\s+of\s+n\b", re.I), "ओ ऑफ़ एन"),
]


def normalise_symbols(text: str) -> str:
    """Spell out numbers, percentages, Big-O and symbols so the TTS never has to guess."""
    out = text
    for pat, repl in _BIG_O:
        out = pat.sub(repl, out)
    out = re.sub(r"(\d+(?:\.\d+)?)\s*%", lambda m: _num(m.group(1)) + " परसेंट", out)
    out = re.sub(r"(\d+)\s*[xX]\b", lambda m: _num(m.group(1)) + " गुना", out)
    out = re.sub(r"(?<![\w.])(\d+)(?:\.(\d+))?(?![\w])", lambda m: _num(m.group(0)), out)
    out = out.replace("->", " से ").replace("→", " से ")
    out = out.replace("+", " प्लस ").replace("=", " बराबर ").replace("&", " और ")
    out = re.sub(r"\s+-\s+", " माइनस ", out)
    out = re.sub(r"[\"'“”‘’`]", " ", out)
    out = re.sub(r"[()\[\]{}<>*_#|\\/]", " ", out)
    out = out.replace("—", ", ").replace("–", ", ").replace("·", ", ")
    out = re.sub(r"\s+([,.!?;:])", r"\1", out)
    return re.sub(r"\s{2,}", " ", out).strip()


def _num(token: str) -> str:
    if "." in token:
        whole, frac = token.split(".", 1)
        return f"{hindi_number(int(whole))} दशमलव " + " ".join(_UNITS[int(d)] for d in frac)
    return hindi_number(int(token))


def build_tts_text(spoken_text: str) -> str:
    """Single entry point: caption narration -> fully-phonetic Devanagari voice script."""
    from audio_engine.voice_generator import apply_tts_pronunciations, ensure_pronounceable

    text = normalise_symbols(spoken_text)
    text = _romanised_hindi_to_devanagari(text)
    text = apply_tts_pronunciations(text)
    return ensure_pronounceable(text)


def _romanised_hindi_to_devanagari(text: str) -> str:
    from ai_engine.plan_generator import _ACRONYM_TO_DEVANAGARI, _ROMAN_TO_DEVANAGARI

    def repl(m: re.Match[str]) -> str:
        low = m.group(0).lower()
        return _ACRONYM_TO_DEVANAGARI.get(low) or _ROMAN_TO_DEVANAGARI.get(low) or m.group(0)

    return re.sub(r"[A-Za-z]+", repl, text)
