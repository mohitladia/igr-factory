from __future__ import annotations

import json
import os
import re
from typing import Any

from ai_engine.topic_classifier import classify_topic
from ai_engine.youtube_research import fetch_youtube_research
from ai_engine.cta import cta_keyword
from audio_engine.tts_text import build_tts_text

import requests


class TopicAlignmentError(ValueError):
    """Raised when generated content does not teach the requested topic."""


ALLOWED_TYPES = {
    "kinetic_title", "cinematic_visual", "concept_visual", "architecture_build",
    "data_flow", "comparison", "metric_callout", "summary",
}

SYSTEM_PROMPT = """CRITICAL TOPIC LOCK: Teach only the exact topic supplied by the user. Never substitute Kafka or any default topic. Choose a topic-specific teaching format. For DSA problems include problem statement, baseline approach, optimized approach, dry run, and complexity. For frameworks explain lifecycle and mechanisms. For infrastructure explain architecture and tradeoffs. Every beat must directly teach the requested topic. Separate viewer-facing title/spoken_text from internal visual_action and asset_prompt. NEVER display visual_action, asset_prompt, internal_notes, or production directions as on-screen text. Never use generic placeholders such as System component, Component, or Step. If unable to create accurate topic-specific content, fail rather than switch topics.

STORYTELLING & BENCHMARK RULES (@backendlore 9.5+/10 GOLD STANDARD):
1. EASY TO UNDERSTAND + FULL TECHNICAL CONTEXT (CRITICAL):
   - Explain like a senior Indian engineer talking to a friend in simple, relatable Hinglish, BUT NEVER water down the real engineering depth!
   - Always pair a vivid everyday analogy ("Socho jaise GPS map par coordinates...", "Memory Diary", "26-bucket tarazu") WITH the exact technical mechanism, real numbers, and algorithm names (e.g., for AI Embeddings: why SQL/Keyword search fails on 'sasta phone' vs 'budget mobile', 1536-dimension vector coordinates, King - Man + Woman = Queen vector math, Cosine Similarity angle check, and HNSW Graph Index in Vector DBs).
2. HOOK (Beat 1): Start with a concrete, high-stakes interview or production dilemma with numbers and a "?" question mark (14-20 words). MUST include one of: "Interview", "kaise", "kyun", "90%", "fail", "reject", "crash", "socho". Never start with textbook definitions.
3. PROBLEM & NAIVE TRAP (Beat 2, type="comparison" with 2 nodes: Naive Bottleneck vs Smart Solution): Show why the naive approach (e.g., Keyword Search / Brute Force / Sorting) fails in production with concrete numbers.
4. INTUITIVE MENTAL MODEL (Beat 3): Use "Socho jaise..." with a physical analogy (GPS map coordinates, diary, balance scale, clock ring) + concrete numbers (e.g., 1536 dimensions, 26 buckets, 360 degrees).
5. DRY RUN & VECTOR/DATA PROOF (Beat 4): Walk through a concrete example with real inputs and outputs (e.g., 'King' - 'Man' + 'Woman' = 'Queen', or 'sasta phone' matching 'budget mobile' with 0.94 Cosine Similarity).
6. CORE MECHANISM & PRODUCTION SCALE (Beats 5-6): Explain how similarity/lookup works under the hood (e.g., Cosine Similarity angle between vectors, and why HNSW Graph Index beats slow O(n) brute-force scan across 10 million vectors).
7. CONVERSATIONAL HINGLISH & PACING: Keep EVERY beat between 14 and 22 words (NO slashes "/", NO filler like "Simple hai!").
8. OUTRO CTA & SEAMLESS LOOP (Final Beat ONLY has type="summary"): Summarize the key takeaway + ask an engaging architectural question + "Comment [KEYWORD] for complete PDF interview notes!". Only the LAST beat may use type="summary". Never use generic labels like "Step 1", "Step 2" in steps.

OUTPUT FORMAT:
Return ONLY valid JSON. Do not add Markdown fences or commentary.
The JSON must have: title, topic, language, target_duration_seconds, beats.
Create 6 to 8 punchy beats targeting about 60-75 seconds total.
Each beat must have:
- id: short snake_case unique (use: hook, problem, core_model, data_flow, optimization, summary)
- type: one of kinetic_title, comparison, architecture_build, data_flow, concept_visual, metric_callout, summary
- title: max 5 words, punchy editorial title
- spoken_text: natural conversational narration in Roman Hinglish, 14-24 words (NO slashes "/"). This is the ONLY narration: the on-screen captions, the voice and the visuals are all generated from it, so every number, name and concept shown in nodes/steps/metric MUST also be said in spoken_text of the SAME beat.
- visual_action: specific animation instruction for motion graphics
- accent_words: array of 2-4 highlight words
- asset_prompt: null
- nodes: REQUIRED array of 2-4 objects {label, detail, color} with concrete numbers/examples that are mentioned in this beat's spoken_text (NEVER leave empty except on summary if steps are used)
- connections: array of pairs of node indexes e.g. [[0,1],[1,2]]
- steps: REQUIRED array of 3 objects {label, detail} for data_flow beats
- metric: REQUIRED short punchy callout string on EVERY beat (e.g., "90% CACHE MISS", "0° TO 360° RING", "ONLY 1/N KEYS MOVE", "VIRTUAL NODES"), must be grounded in the narration
- visual: optional object {"kind": one of "compare" (needs exactly 2 nodes: bad approach vs good approach), "stages" (2-4 nodes or 3 steps shown as a pipeline), or "metric" (one big number/claim)}. Omit "visual" to let the system choose from beat type. Never invent hash rings, rate-limit gates, token buckets or HTTP codes unless the topic itself is about them.
"""

_ROMAN_TO_DEVANAGARI: dict[str, str] = {
    "mein": "में", "hai": "है", "hain": "हैं", "tha": "था", "thi": "थी", "the": "थे",
    "toh": "तो", "kya": "क्या", "kyun": "क्यों", "kaise": "कैसे", "kab": "कब", "kahan": "कहाँ",
    "aur": "और", "ya": "या", "ek": "एक", "do": "दो", "teen": "तीन", "char": "चार",
    "hum": "हम", "aap": "आप", "aapka": "आपका", "aapki": "आपकी", "hamein": "हमें", "apne": "अपने",
    "ko": "को", "ka": "का", "ki": "की", "ke": "के", "se": "से", "par": "पर", "pe": "पे",
    "bhi": "भी", "hi": "ही", "nahi": "नहीं", "mat": "मत", "na": "ना",
    "karo": "करो", "karta": "करता", "karti": "करती", "karte": "करते", "kiya": "किया", "karenge": "करेंगे",
    "hota": "होता", "hoti": "होती", "hote": "होते", "hua": "हुआ", "hui": "हुई", "ho": "हो", "jaye": "जाए",
    "dekho": "देखो", "dekhte": "देखते", "samjho": "समझो", "samajhte": "समझते", "samajhna": "समझना", "socho": "सोचो",
    "agar": "अगर", "jab": "जब", "tab": "तब", "jahan": "जहाँ", "wahan": "वहाँ", "wahi": "वहीं",
    "yeh": "ये", "ye": "ये", "woh": "वो", "wo": "वो", "iska": "इसका", "iski": "इसकी", "iske": "इसके", "isi": "इसी",
    "isliye": "इसलिए", "kyunki": "क्योंकि", "lekin": "लेकिन", "balki": "बल्कि",
    "bada": "बड़ा", "bade": "बड़े", "chhota": "छोटा", "chhote": "छोटे", "zyada": "ज़्यादा", "kam": "कम",
    "pehle": "पहले", "baad": "बाद", "aage": "आगे", "peeche": "पीछे", "andar": "अंदर", "bahar": "बाहर",
    "sara": "सारा", "poora": "पूरा", "har": "हर", "sabse": "सबसे", "kuch": "कुछ", "koi": "कोई",
    "fayda": "फ़ायदा", "dikkat": "दिक्कत", "zaroori": "ज़रूरी", "namumkin": "नामुमकिन",
    "yaad": "याद", "rakho": "रखो", "rakhti": "रखती", "rakhna": "रखना", "padta": "पड़ता",
    "pucha": "पूछा", "poocha": "पूछा", "bolte": "बोलते", "boli": "बोली", "kehte": "कहते",
    "deta": "देता", "deti": "देती", "dete": "देते", "dena": "देना",
    "aata": "आता", "aati": "आती", "aate": "आते", "aaya": "आया", "aane": "आने", "aayega": "आएगा",
    "jata": "जाता", "jaata": "जाता", "ban": "बन", "gayi": "गई", "gaya": "गया", "banaya": "बनाया", "bana": "बना", "lo": "लो",
    "bina": "बिना", "saath": "साथ", "badle": "बदले", "bajaye": "बजाय", "yaani": "यानी", "matlab": "मतलब",
    "lakh": "लाख", "crore": "करोड़", "hazar": "हज़ार", "barabar": "बराबर", "achanak": "अचानक", "sidha": "सीधा",
    "khali": "खाली", "purane": "पुराने", "naye": "नए", "nya": "नया", "agla": "अगला", "akela": "अकेला",
    "kitna": "कितना", "kabhi": "कभी", "aaj": "आज", "ab": "अब", "bas": "बस", "khud": "ख़ुद", "kaam": "काम",
    "dhoondhna": "ढूँढना", "dhoondhne": "ढूँढने", "लगाते": "लगाते", "lagate": "लगाते", "lagta": "लगता", "laga": "लगा",
    "baant": "बाँट", "jodna": "जोड़ना", "bhej": "भेज", "badhne": "बढ़ने", "badhana": "बढ़ाना", "teeno": "तीनों",
    "ratta": "रट्टा", "baar": "बार", "baar-baar": "बार-बार",
    "dono": "दोनों", "kar": "कर", "karke": "करके", "karna": "करना", "karo": "करो", "leta": "लेता", "mana": "मना",
    "turant": "तुरंत", "idea": "आइडिया", "banao": "बनाओ", "hamari": "हमारी", "hamara": "हमारा", "liye": "लिए",
    "bacha": "बचा", "sach": "सच", "milenge": "मिलेंगे", "mile": "मिले", "milta": "मिलता", "milte": "मिलते",
    "log": "लोग", "waste": "वेस्ट", "kyun": "क्यों", "kaun": "कौन", "kitne": "कितने", "chahiye": "चाहिए",
    "chahta": "चाहता", "chahte": "चाहते", "dalte": "डालते", "dalo": "डालो", "dekhte": "देखते", "milao": "मिलाओ",
    "wala": "वाला", "wali": "वाली", "wale": "वाले", "sirf": "सिर्फ़", "bilkul": "बिल्कुल", "abhi": "अभी",
    "phir": "फिर", "fir": "फिर", "tak": "तक", "tha": "था", "the": "थे", "hoga": "होगा", "hogi": "होगी",
    "sakte": "सकते", "sakta": "सकता", "sakti": "सकती", "chalo": "चलो", "chalta": "चलता", "chalte": "चलते",
    "samajh": "समझ", "samjha": "समझा", "pata": "पता", "seedha": "सीधा", "ulta": "उल्टा", "pehla": "पहला",
    "doosra": "दूसरा", "doosre": "दूसरे", "tisra": "तीसरा", "aakhri": "आखिरी", "naya": "नया", "purana": "पुराना",
    "asli": "असली", "magic": "मैजिक", "tarika": "तरीका", "trick": "ट्रिक", "kaafi": "काफ़ी", "bahut": "बहुत",
    "thoda": "थोड़ा", "zyada": "ज़्यादा", "ghar": "घर", "kaam": "काम", "kaise": "कैसे", "kyunki": "क्योंकि",
    "isliye": "इसलिए", "jaisa": "जैसा", "waise": "वैसे", "agar": "अगर", "warna": "वरना", "nahi": "नहीं",
    "haan": "हाँ", "sab": "सब", "sabhi": "सभी", "koi": "कोई", "kuch": "कुछ", "unka": "उनका", "uska": "उसका",
    "interview": "इंटरव्यू", "interviewer": "इंटरव्यूअर", "server": "सर्वर", "servers": "सर्वर्स",
    "data": "डेटा", "database": "डेटाबेस", "crash": "क्रैश", "sab": "सब", "jaate": "जाते", "jate": "जाते",
    "hotey": "होते", "hota": "होता", "problem": "प्रॉब्लम", "jab": "जब", "ek": "एक", "do": "दो", "char": "चार",
    "augmented": "ऑगमेंटेड", "brute": "ब्रूट", "chatgpt": "चैट जी पी टी", "chunk": "चंक", "chunks": "चंक्स",
    "context": "कॉन्टेक्स्ट", "dhoondho": "ढूँढो", "downtime": "डाउनटाइम", "embedding": "एम्बेडिंग",
    "exactly": "एग्ज़ैक्टली", "generation": "जनरेशन", "hashmap": "हैशमैप", "inke": "इनके", "instant": "इंस्टेंट",
    "jodo": "जोड़ो", "likho": "लिखो", "model": "मॉडल", "photosynthesis": "फ़ोटोसिंथेसिस", "retrieval": "रिट्रीवल",
    "robin": "रॉबिन", "round": "राउंड", "scaling": "स्केलिंग", "stateless": "स्टेटलेस", "sum": "सम",
    "twosum": "टू सम", "target": "टारगेट", "tumne": "तुमने", "vector": "वेक्टर", "window": "विंडो",
    "zyadatar": "ज़्यादातर", "answer": "आंसर", "app": "ऐप", "approach": "अप्रोच", "beech": "बीच",
    "comparisons": "कम्पैरिज़न्स", "complement": "कॉम्प्लिमेंट", "current": "करंट", "diary": "डायरी",
    "down": "डाउन", "drop": "ड्रॉप", "force": "फ़ोर्स", "hokar": "होकर", "index": "इंडेक्स",
    "inhein": "इन्हें", "inhi": "इन्हीं", "isse": "इससे", "itna": "इतना", "jawab": "जवाब", "jo": "जो",
    "jod": "जोड़", "kaato": "काटो", "karoge": "करोगे", "kat": "कट", "lakho": "लाखों", "lata": "लाता",
    "lete": "लेते", "likhta": "लिखता", "limit": "लिमिट", "login": "लॉगिन", "lookup": "लुकअप",
    "loops": "लूप्स", "machines": "मशीन्स", "memory": "मेमोरी", "milata": "मिलाता", "ne": "ने",
    "nested": "नेस्टेड", "number": "नंबर", "numbers": "नंबर्स", "overload": "ओवरलोड", "paas": "पास",
    "paate": "पाते", "padh": "पढ़", "padhta": "पढ़ता", "page": "पेज", "pages": "पेजेस", "pair": "पेयर",
    "percent": "परसेंट", "poori": "पूरी", "rakh": "रख", "reject": "रिजेक्ट", "rule": "रूल",
    "rupaye": "रुपये", "saare": "सारे", "sahi": "सही", "sawal": "सवाल", "second": "सेकंड",
    "session": "सेशन", "smart": "स्मार्ट", "square": "स्क्वायर", "store": "स्टोर", "tukdon": "टुकड़ों",
    "yahi": "यही",
    "aapke": "आपके", "duniya": "दुनिया", "embeddings": "एम्बेडिंग्स", "jaise": "जैसे", "king": "किंग",
    "queen": "क्वीन", "billion": "बिलियन", "million": "मिलियन", "capture": "कैप्चर", "case": "केस",
    "clear": "क्लियर", "closely": "क्लोज़ली", "computation": "कम्प्यूटेशन", "cost": "कॉस्ट",
    "depend": "डिपेंड", "din": "दिन", "form": "फ़ॉर्म", "high": "हाई", "low": "लो", "madad": "मदद",
    "meaning": "मीनिंग", "neural": "न्यूरल", "numeric": "न्यूमेरिक", "opinion": "ओपिनियन",
    "powerful": "पावरफुल", "proximity": "प्रॉक्सिमिटी", "quality": "क्वालिटी",
    "relationships": "रिलेशनशिप्स", "relationship": "रिलेशनशिप", "represent": "रिप्रेज़ेंट",
    "samajhne": "समझने", "samajhta": "समझता", "samajhti": "समझती", "samjhe": "समझे",
    "searches": "सर्चेस", "search": "सर्च", "through": "थ्रू", "train": "ट्रेन", "training": "ट्रेनिंग",
    "unki": "उनकी", "unke": "उनके", "use": "यूज़", "vectors": "वेक्टर्स", "words": "वर्ड्स",
    "word": "वर्ड", "dimensions": "डायमेंशन्स", "dimension": "डायमेंशन", "cosine": "कोसाइन",
    "similarity": "सिमिलैरिटी", "distance": "डिस्टेंस", "space": "स्पेस", "coordinate": "कोऑर्डिनेट",
    "coordinates": "कोऑर्डिनेट्स", "map": "मैप", "token": "टोकन", "tokens": "टोकन्स", "semantic": "सिमेंटिक",
    "swiggy": "स्विगी", "gps": "जी पी एस", "latitude": "लैटिट्यूड", "longitude": "लॉन्गिट्यूड",
    "sasta": "सस्ता", "phone": "फ़ोन", "budget": "बजट", "mobile": "मोबाइल", "man": "मैन", "woman": "वुमन",
    "dot": "डॉट", "product": "प्रोडक्ट", "angle": "एंगल", "hnsw": "एच एन एस डब्ल्यू", "graph": "ग्राफ़",
    "keyword": "कीवर्ड", "exact": "एग्ज़ैक्ट", "match": "मैच", "miss": "मिस", "relevant": "रेलेवेंट",
    "results": "रिज़ल्ट्स", "milliseconds": "मिलीसेकंड्स", "ms": "मिलीसेकंड", "paas": "पास",
    "pass": "पास", "baith": "बैठ", "baithte": "बैठते", "kareeb": "क़रीब", "napna": "नापना",
    "bhasha": "भाषा", "computer": "कंप्यूटर", "computers": "कंप्यूटर्स", "id": "आई डी", "ids": "आई डीज़",
    "relation": "रिलेशन", "zero": "ज़ीरो", "nikalo": "निकालो", "nikalta": "निकलता", "land": "लैंड",
}


_ACRONYM_TO_DEVANAGARI: dict[str, str] = {
    "rag": "आर ए जी",
    "pdf": "पी डी एफ",
    "pdfs": "पी डी एफ्स",
    "ai": "ए आई",
    "db": "डी बी",
    "llm": "एल एल एम",
    "llms": "एल एल एम्स",
    "api": "ए पी आई",
    "cpu": "सी पी यू",
    "gpu": "जी पी यू",
    "ram": "रैम",
    "sql": "एस क्यू एल",
    "jwt": "जे डब्ल्यू टी",
    "dns": "डी एन एस",
    "http": "एच टी टी पी",
    "tcp": "टी सी पी",
    "dsa": "डी एस ए",
    "spof": "सिंगल पॉइंट ऑफ़ फेलियर",
}


def ensure_devanagari_tts_text(spoken_text: str, tts_text: str | None = None) -> str:
    """Ensure tts_text has 100% Devanagari Hindi phonetics via the pronunciation engine."""
    candidate = (tts_text or "").strip()
    source = candidate if (candidate and re.search(r"[\u0900-\u097F]", candidate)) else (candidate or spoken_text.strip())
    try:
        from audio_engine.voice_generator import ensure_pronounceable
        return ensure_pronounceable(source)
    except Exception:
        def _replace_token(match: re.Match[str]) -> str:
            word = match.group(0)
            low = word.lower()
            if low in _ACRONYM_TO_DEVANAGARI:
                return _ACRONYM_TO_DEVANAGARI[low]
            return _ROMAN_TO_DEVANAGARI.get(low, word)

        return re.sub(r"[A-Za-z]+(?:-[A-Za-z]+)?", _replace_token, source)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("LLM response did not contain a JSON object")
        value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("LLM response root must be a JSON object")
    return value


def _endpoint() -> str:
    base = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:31415/v1").rstrip("/")
    return base if base.endswith("/chat/completions") else f"{base}/chat/completions"


def _review_topic_alignment(topic: str, plan: dict[str, Any], headers: dict[str, str], model: str) -> None:
    """Use a topic-agnostic second pass to reject storyboards that teach a different subject."""
    review_beats = []
    for beat in plan.get("beats", []):
        if not isinstance(beat, dict):
            continue
        review_beats.append({
            key: beat.get(key)
            for key in ("title", "spoken_text", "visual_action", "metric", "nodes", "steps")
            if beat.get(key)
        })

    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict storyboard topic-alignment reviewer. Compare the requested topic with "
                    "the actual lesson taught across all beats. Ignore the plan's declared topic/title if its "
                    "narration, examples, visual directions, or steps teach something else. Related background "
                    "concepts are allowed only when they support the requested topic. Return JSON only with "
                    '"is_relevant" (boolean) and "reason" (short string).'
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"requested_topic": topic, "storyboard": review_beats},
                    ensure_ascii=False,
                ),
            },
        ],
    }
    timeout_s = int(os.getenv("LLM_TIMEOUT", "30"))
    try:
        response = requests.post(_endpoint(), headers=headers, json=payload, timeout=timeout_s)
        if response.status_code in {400, 404, 422}:
            payload.pop("response_format", None)
            response = requests.post(_endpoint(), headers=headers, json=payload, timeout=timeout_s)
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
        verdict = _extract_json(content)
        if verdict.get("is_relevant") is not True:
            reason = str(verdict.get("reason") or "The storyboard does not teach the requested topic.")
            raise TopicAlignmentError(f"Topic relevance review failed for '{topic}': {reason} No video was rendered.")
    except TopicAlignmentError:
        raise
    except Exception as exc:
        raise TopicAlignmentError(
            f"Topic relevance review could not verify '{topic}' ({exc}). No video was rendered."
        ) from exc


def generate_plan(topic: str, duration_seconds: int = 70) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("FREELLM_API_KEY")
    if not api_key:
        raise RuntimeError("No LLM key found. Set OPENAI_API_KEY or FREELLM_API_KEY in .env, or run with --demo.")

    is_official_openai = "api.openai.com" in _endpoint() or (api_key.startswith("sk-") and not api_key.startswith("freellm"))
    default_model = "gpt-4o-mini" if is_official_openai else "auto"
    preferred_model = os.getenv("OPENAI_MODEL", default_model)
    if preferred_model == "auto" and is_official_openai:
        preferred_model = "gpt-4o-mini"

    if is_official_openai:
        candidate_models = [preferred_model, "gpt-4o-mini", "gpt-4o"]
    else:
        candidate_models = [preferred_model, "claude-haiku-4-5", "auto"]
    profile = classify_topic(topic)
    yt_research = fetch_youtube_research(topic, max_results=3)
    yt_context = yt_research.get("context_block", "")
    if yt_context:
        print(f"[youtube-research] Grounded prompt with {len(yt_research.get('videos', []))} top YouTube references.")
    user_prompt = (
        f"EXACT USER TOPIC (must remain unchanged): {topic}\n"
        f"Detected family: {profile.family}\nTeaching format: {profile.format_name}\n"
        f"Required concepts: {', '.join(profile.required_concepts)}\n"
        f"Suggested flow: {', '.join(profile.teaching_flow)}\n"
        f"Target duration: {duration_seconds} seconds.\n"
        + (f"REAL YOUTUBE VIRAL RESEARCH CONTEXT (use for hook angles & concrete stats):\n{yt_context}\n" if yt_context else "")
        + "Audience: Indian software engineers and tech learners. Style: @backendlore style conversational Hinglish, punchy hook, concrete numbers, intuitive mental model, and interactive diagram nodes/steps on every beat. "
        "Return JSON only with at least 6 beats."
    )
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_exc: Exception | None = None
    content = ""
    selected_model = ""
    for model_name in dict.fromkeys(candidate_models):
        payload = {
            "model": model_name,
            "temperature": 0.65,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        timeout_s = int(os.getenv("LLM_TIMEOUT", "30"))
        try:
            response = requests.post(_endpoint(), headers=headers, json=payload, timeout=timeout_s)
            if response.status_code in {400, 404, 422}:
                retry_payload = dict(payload)
                retry_payload.pop("response_format", None)
                response = requests.post(_endpoint(), headers=headers, json=retry_payload, timeout=timeout_s)
            response.raise_for_status()
            body = response.json()
            raw_content = body["choices"][0]["message"]["content"]
            if isinstance(raw_content, list):
                raw_content = "\n".join(str(part.get("text", "")) for part in raw_content if isinstance(part, dict))
            parsed = _extract_json(raw_content)
            if isinstance(parsed.get("beats"), list) and len(parsed["beats"]) >= 5:
                content = raw_content
                selected_model = model_name
                print(f"[llm] Generated {len(parsed['beats'])} beats via model '{model_name}' (routed: {body.get('model', model_name)})")
                break
        except Exception as exc:
            last_exc = exc
            continue

    if not content:
        raise RuntimeError(f"LLM request failed across candidate models: {last_exc}")

    plan = _extract_json(content)
    try:
        from ai_engine.critic import evaluate_plan_quality
        report = evaluate_plan_quality(plan)
        if report.score < 9.5:
            refine_prompt = (
                f"Your previous storyboard for '{topic}' scored {report.score}/10, below the required 9.5/10 bar.\n"
                f"Critic feedback to fix: {'; '.join(report.feedback or ['Add a vivid everyday analogy (Socho jaise GPS map...) AND deeper technical context with numbers, and keep every beat 14-22 words'])}\n"
                "Rewrite the JSON storyboard so it scores 9.5+/10: keep language simple and relatable in Hinglish, "
                "include a vivid analogy ('Socho jaise...') + full engineering depth (naive keyword/brute-force failure, "
                "concrete numbers/dimensions, exact mechanism, production scale), keep every beat 14-22 words, "
                "and end with 'Comment [KEYWORD] for complete PDF interview notes!'. Return JSON only."
            )
            refine_payload = {
                "model": selected_model,
                "temperature": 0.5,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": content},
                    {"role": "user", "content": refine_prompt},
                ],
            }
            r2 = requests.post(_endpoint(), headers=headers, json=refine_payload, timeout=int(os.getenv("LLM_TIMEOUT", "30")))
            if r2.status_code == 200:
                c2 = r2.json()["choices"][0]["message"]["content"]
                p2 = _extract_json(c2)
                if isinstance(p2.get("beats"), list) and len(p2["beats"]) >= 5:
                    rep2 = evaluate_plan_quality(p2)
                    print(f"[critic-refine] Upgraded storyboard score: {report.score}/10 -> {rep2.score}/10")
                    if rep2.score >= report.score:
                        plan = p2
    except Exception as refine_exc:
        print(f"[critic-refine] Skipped refinement ({refine_exc})")

    _review_topic_alignment(topic, plan, headers, selected_model)
    print(f"[topic-review] Storyboard matches requested topic: {topic}")
    plan.setdefault("title", f"{topic}: explained")
    # Preserve the model's claimed topic. validate_and_normalize must inspect it;
    # silently replacing it here previously hid topic drift.
    plan.setdefault("topic", topic)
    plan.setdefault("language", "hinglish")
    plan.setdefault("target_duration_seconds", duration_seconds)
    return plan


def validate_and_normalize(plan: dict[str, Any], topic: str) -> dict[str, Any]:
    profile = classify_topic(topic)
    returned_topic = str(plan.get("topic", topic)).strip()
    if returned_topic and returned_topic.lower() != topic.strip().lower():
        raise ValueError(f"Topic lock failed: requested '{topic}', AI returned '{returned_topic}'.")
    beats = plan.get("beats")
    if not isinstance(beats, list) or not beats:
        raise ValueError("Plan must contain a non-empty 'beats' array")

    # Topic-specific semantic guard: Two Sum must actually teach Two Sum,
    # not merely carry a Two Sum title while narrating Kafka.
    if re.search(r"\btwo\s*sum\b", topic, re.I):
        corpus_parts = []
        for beat in beats:
            if isinstance(beat, dict):
                corpus_parts.extend([
                    str(beat.get("title", "")), str(beat.get("spoken_text", "")),
                    str(beat.get("visual_action", "")), str(beat.get("metric", "")),
                ])
                for key in ("nodes", "steps"):
                    values = beat.get(key, [])
                    if isinstance(values, list):
                        for value in values:
                            corpus_parts.append(str(value))
        corpus = " ".join(corpus_parts).lower()
        kafka_terms = ("kafka", "producer", "consumer group", "broker", "partition", "event streaming")
        leaked = [term for term in kafka_terms if term in corpus]
        # Accept common synonyms: hash map / hash table / dictionary, and O(n) in various forms
        required_patterns = [
            (r"hash[\s_-]?map|hash[\s_-]?table|\bdict(?:ionary)?\b", "hashmap/dict"),
            (r"\bcomplement\b|\bdifference\b|\btarget\s*-\s*\w+", "complement"),
            (r"\btarget\b", "target"),
            (r"o\s*\(\s*n\s*\)|linear\s*time|o of n", "O(n)"),
        ]
        missing = [label for pattern, label in required_patterns if not re.search(pattern, corpus, re.I)]
        if leaked:
            raise ValueError("Topic relevance check failed for Two Sum: Kafka concepts detected (" + ", ".join(leaked) + "). No video was rendered.")
        if missing:
            raise ValueError("Topic relevance check failed for Two Sum: missing core teaching concepts (" + ", ".join(missing) + "). No video was rendered.")

    clean_beats: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(beats, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Beat {index} must be an object")
        beat_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(item.get("id") or f"beat_{index}")).strip("_").lower()
        if not beat_id or beat_id in seen:
            beat_id = f"beat_{index}"
        seen.add(beat_id)
        beat_type = str(item.get("type", "concept_visual"))
        if beat_type not in ALLOWED_TYPES:
            beat_type = "concept_visual"
        spoken = str(item.get("spoken_text", "")).strip()
        raw_nodes = item.get("nodes", []) if isinstance(item.get("nodes"), list) else []
        viewer_text = " ".join([str(item.get("title", "")), spoken] +
            [str(n.get("label", "")) + " " + str(n.get("detail", "")) for n in raw_nodes if isinstance(n, dict)])
        forbidden = ("system component", "production note", "fast montage", "use a controlled slow zoom", "placeholder")
        if any(term in viewer_text.lower() for term in forbidden):
            raise ValueError(f"Content quality check failed in beat {index}: placeholder/production text found.")
        if not spoken:
            raise ValueError(f"Beat '{beat_id}' has no spoken_text")
        nodes = item.get("nodes") if isinstance(item.get("nodes"), list) else []
        steps = item.get("steps") if isinstance(item.get("steps"), list) else []
        connections = item.get("connections") if isinstance(item.get("connections"), list) else []
        clean_nodes = []
        for node in nodes[:5]:
            if isinstance(node, str):
                clean_nodes.append({"label": node, "detail": "", "color": "#55B9FF"})
            elif isinstance(node, dict):
                clean_nodes.append({
                    "label": str(node.get("label", "Component"))[:40],
                    "detail": str(node.get("detail", ""))[:70],
                    "color": str(node.get("color", "#55B9FF")),
                })
        clean_connections = []
        for edge in connections[:8]:
            if isinstance(edge, (list, tuple)) and len(edge) >= 2:
                try:
                    a, b = int(edge[0]), int(edge[1])
                    if 0 <= a < len(clean_nodes) and 0 <= b < len(clean_nodes) and a != b:
                        clean_connections.append([a, b])
                except (ValueError, TypeError):
                    pass
        clean_steps = []
        for step in steps[:5]:
            if isinstance(step, str):
                clean_steps.append({"label": step, "detail": ""})
            elif isinstance(step, dict):
                clean_steps.append({"label": str(step.get("label", "Step"))[:40], "detail": str(step.get("detail", ""))[:70]})
        clean_beats.append({
            "id": beat_id,
            "type": beat_type,
            "title": str(item.get("title") or topic)[:80],
            "spoken_text": spoken,
            "tts_text": build_tts_text(spoken),
            "visual": item.get("visual") if isinstance(item.get("visual"), dict) else None,
            "visual_action": str(item.get("visual_action", "Reveal the key concept with a purposeful motion."))[:300],
            "accent_words": [str(x)[:30] for x in (item.get("accent_words") or [])[:8]],
            "asset_prompt": str(item["asset_prompt"])[:700] if item.get("asset_prompt") else None,
            "nodes": clean_nodes,
            "connections": clean_connections,
            "steps": clean_steps,
            "metric": str(item.get("metric", ""))[:35],
        })
    kw = cta_keyword(topic)
    if clean_beats:
        last = clean_beats[-1]
        last_spoken = last["spoken_text"]
        if not any(w in last_spoken.lower() for w in ("comment", "pdf", "notes", "cheat sheet")):
            last["spoken_text"] = f"{last_spoken.rstrip('.!?')}. Comment {kw} for complete PDF interview notes!"
            last["tts_text"] = build_tts_text(last["spoken_text"])
            if not last.get("accent_words"):
                last["accent_words"] = ["Comment", kw]
            elif kw not in last["accent_words"]:
                last["accent_words"].append(kw)

    if len(clean_beats) < 4:
        raise ValueError(f"AI returned only {len(clean_beats)} beats; expected at least 4. Retry with a stronger prompt.")
    return {
        "title": str(plan.get("title", f"{topic}: explained")),
        "topic": topic,
        "topic_family": profile.family,
        "teaching_format": profile.format_name,
        "language": str(plan.get("language", "hinglish")),
        "target_duration_seconds": int(plan.get("target_duration_seconds", 70)),
        "cta_keyword": kw,
        "beats": clean_beats,
    }
