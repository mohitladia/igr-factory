from __future__ import annotations

import json
import os
import re
from typing import Any

from ai_engine.topic_classifier import classify_topic
from ai_engine.youtube_research import fetch_youtube_research

import requests

ALLOWED_TYPES = {
    "kinetic_title", "cinematic_visual", "concept_visual", "architecture_build",
    "data_flow", "comparison", "metric_callout", "summary",
}

SYSTEM_PROMPT = """CRITICAL TOPIC LOCK: Teach only the exact topic supplied by the user. Never substitute Kafka or any default topic. Choose a topic-specific teaching format. For DSA problems include problem statement, baseline approach, optimized approach, dry run, and complexity. For frameworks explain lifecycle and mechanisms. For infrastructure explain architecture and tradeoffs. Every beat must directly teach the requested topic. Separate viewer-facing title/spoken_text from internal visual_action and asset_prompt. NEVER display visual_action, asset_prompt, internal_notes, or production directions as on-screen text. Never use generic placeholders such as System component, Component, or Step. If unable to create accurate topic-specific content, fail rather than switch topics.

STORYTELLING & BENCHMARK RULES (@backendlore style):
1. HOOK (Beat 1): Start with a concrete, high-stakes production dilemma with numbers (e.g., "Interviewer ne poocha: 4 Redis servers mein se 1 crash hua toh Modulo Hashing se 90% cache miss kyun ho jata hai?"). For DSA: "Interview mein [Problem] pucha toh 90% log [Naive/Sorting] bolte hain aur turant reject!". Never start with "Today we will discuss".
2. PROBLEM & NAIVE TRAP (Beat 2): Show exactly why the naive approach fails in production with concrete numbers (e.g., in System Design: "hash(key) % N mein N=4 se N=3 hote hi Cache Stampede!", in DSA: "Dono strings sort karna O(n log n) leta hai — interviewer O(n) single pass chahta hai!").
3. INTUITIVE MENTAL MODEL (Beats 3-4): Explain the core mechanism through a visual physical analogy (e.g., System Design: "360-degree Clock / Hash Ring", DSA: "26-bucket balance scale jahan string 1 aate hi +1, string 2 aate hi -1", "Memory Diary"). NEVER recommend slow Sorting O(n log n) when O(n) Hash/Frequency array exists!
4. DRY RUN & PROOF (Beat 4-5): Walk through a concrete, vivid example (e.g. 'listen' vs 'silent' showing buckets zeroing out, or key routing).
5. COMPLEXITY & WIN: Emphasize the exact algorithmic leap (e.g., O(n log n) dropped to O(n) time, O(1) space).
6. CONVERSATIONAL HINGLISH: Narration must sound like an enthusiastic senior Indian tech lead explaining 1-on-1 in natural Hinglish. Never use "/" slashes in spoken_text or tts_text (write "aur" or "ya" instead).
7. PACING: Keep each spoken_text beat concise and punchy (14-24 words).
8. OUTRO CTA & INFINITE SEAMLESS LOOP: Final beat summarizes the key takeaway + asks a clever edge-case question + "Comment [KEYWORD] for PDF notes!". Crucially, the last sentence must flow seamlessly back into Beat 1's hook so viewers watch it twice on loop without noticing the cut!

OUTPUT FORMAT:
Return ONLY valid JSON. Do not add Markdown fences or commentary.
The JSON must have: title, topic, language, target_duration_seconds, beats.
Create 6 to 8 punchy beats targeting about 60-75 seconds total.
Each beat must have:
- id: short snake_case unique (use: hook, problem, core_model, data_flow, optimization, summary)
- type: one of kinetic_title, comparison, architecture_build, data_flow, concept_visual, metric_callout, summary
- title: max 5 words, punchy editorial title
- spoken_text: natural conversational narration in Roman Hinglish for on-screen captions, 14-24 words (NO slashes "/")
- tts_text: REQUIRED Devanagari Hindi + English tech terms version of spoken_text for native Hindi TTS pronunciation (write ALL Hindi words in Devanagari script like इंटरव्यू, पूछा, सर्वर, क्रैश, डेटा, कैसे, क्यों, and spell out acronyms like RAG as आर ए जी, DB as डी बी, API as ए पी आई)
- visual_action: specific animation instruction for motion graphics
- accent_words: array of 2-4 highlight words
- asset_prompt: null
- nodes: REQUIRED array of 2-4 objects {label, detail, color} with concrete numbers/examples (NEVER leave empty except on summary if steps are used)
- connections: array of pairs of node indexes e.g. [[0,1],[1,2]]
- steps: REQUIRED array of 3 objects {label, detail} for data_flow beats
- metric: REQUIRED short punchy callout string on EVERY beat (e.g., "90% CACHE MISS", "0° TO 360° RING", "ONLY 1/N KEYS MOVE", "VIRTUAL NODES")
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
    "interview": "इंटरव्यू", "interviewer": "इंटरव्यूअर", "server": "सर्वर", "servers": "सर्वर्स",
    "data": "डेटा", "database": "डेटाबेस", "crash": "क्रैश", "sab": "सब", "jaate": "जाते", "jate": "जाते",
    "hotey": "होते", "hota": "होता", "problem": "प्रॉब्लम", "jab": "जब", "ek": "एक", "do": "दो", "char": "चार",
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
                print(f"[llm] Generated {len(parsed['beats'])} beats via model '{model_name}' (routed: {body.get('model', model_name)})")
                break
        except Exception as exc:
            last_exc = exc
            continue

    if not content:
        raise RuntimeError(f"LLM request failed across candidate models: {last_exc}")

    plan = _extract_json(content)
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

    # Keep a correctly named Anagram plan from carrying over the adjacent Two Sum lesson.
    if re.search(r"\banagrams?\b", topic, re.I):
        anagram_corpus_parts: list[str] = []
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            anagram_corpus_parts.extend(
                str(beat.get(key, ""))
                for key in ("id", "title", "spoken_text", "tts_text", "visual_action", "metric")
            )
            for key in ("nodes", "steps"):
                values = beat.get(key, [])
                if isinstance(values, list):
                    anagram_corpus_parts.extend(str(value) for value in values)
        anagram_corpus = " ".join(anagram_corpus_parts)
        two_sum_markers = (
            r"\btwo\s*sum\b",
            r"\bleetcode\s*#?\s*1\b",
            r"\bcomplement\b.{0,80}\btarget\b",
            r"\btarget\b.{0,80}\bcomplement\b",
        )
        if any(re.search(pattern, anagram_corpus, re.I) for pattern in two_sum_markers):
            raise ValueError(
                "Topic relevance check failed for Anagram: Two Sum content detected. No video was rendered."
            )
        if not re.search(r"\banagram\b|frequen(?:cy|cies)|character count|letter count", anagram_corpus, re.I):
            raise ValueError(
                "Topic relevance check failed for Anagram: no anagram/frequency-count teaching content found. No video was rendered."
            )

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
            "tts_text": ensure_devanagari_tts_text(spoken, item.get("tts_text")),
            "visual_action": str(item.get("visual_action", "Reveal the key concept with a purposeful motion."))[:300],
            "accent_words": [str(x)[:30] for x in (item.get("accent_words") or [])[:8]],
            "asset_prompt": str(item["asset_prompt"])[:700] if item.get("asset_prompt") else None,
            "nodes": clean_nodes,
            "connections": clean_connections,
            "steps": clean_steps,
            "metric": str(item.get("metric", ""))[:35],
        })
    if clean_beats:
        last = clean_beats[-1]
        last_spoken = last["spoken_text"]
        last_tts = last.get("tts_text") or ""
        # Choose a clean, pronounceable keyword: if topic has multiple words, pick the main noun
        topic_words = [w for w in re.findall(r"[A-Za-z]+", topic) if w.lower() not in ("valid", "the", "an", "a", "problem", "solution")]
        kw = topic_words[-1].upper() if topic_words else "NOTES"
        if not any(w in last_spoken.lower() for w in ("comment", "pdf", "notes", "cheat sheet")):
            last["spoken_text"] = f"{last_spoken.rstrip('.!')}. Comment {kw} for complete PDF interview notes!"
            if last_tts and re.search(r"[\u0900-\u097F]", last_tts):
                last["tts_text"] = f"{last_tts.rstrip('।!.')}। कमेंट {kw} करो और कंप्लीट पी डी एफ नोट्स सेव कर लो!"
                last["tts_text"] = ensure_devanagari_tts_text(last["spoken_text"], last["tts_text"])
            else:
                last["tts_text"] = ensure_devanagari_tts_text(last["spoken_text"], None)
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
        "beats": clean_beats,
    }
