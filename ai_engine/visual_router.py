"""Decide which visual template each beat uses - in ONE place, from the beat's own data.

Old design: the renderer guessed the visual from substrings of the topic/narration
("ring" matched "string", "bucket" matched "26-bucket array"), and had hard-coded diagrams per
topic, so every new topic needed code changes and produced video unrelated to the audio.

New design: every beat leaves this module with `beat["visual"] = {"kind": ..., "data": ...}`.
The renderer is a dumb switch on `kind` and only draws what the data contains.

Kinds
  generic, data driven (safe for ANY topic): hook, compare, stages, metric, summary
  curated-only scan: the current renderer draws the LeetCode 242 / 26-letter counter diagram
  grounded specials (only when the beat narration itself talks about them): ring, gate
  curated legacy diagrams (hard-coded content, ONLY for hand-written curated plans):
      array_tape, hashmap, pool, log_stream, partition_lanes, rag
"""
from __future__ import annotations

import re
from typing import Any

GENERIC_KINDS = {"hook", "compare", "stages", "metric", "summary"}
GROUNDED_KINDS = {
    # kind -> (topic must match, beat narration must match)  - word boundaries, never substrings
    "ring": (re.compile(r"\b(consistent\s+hash\w*|hash\s+ring)\b", re.I),
             re.compile(r"\b(ring|clockwise|virtual\s+nodes?|hash\s+ring)\b", re.I)),
    "gate": (re.compile(r"\b(rate\s+limit\w*|token\s+bucket|leaky\s+bucket|throttl\w*)\b", re.I),
             re.compile(r"\b(rate\s+limit\w*|token\s+bucket|leaky\s+bucket|429|throttl\w*)\b", re.I)),
}
CURATED_KINDS = {"array_tape", "hashmap", "pool", "log_stream", "partition_lanes", "rag"}

_CURATED_TOPICS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\btwo\s*sum\b", re.I), "two_sum"),
    (re.compile(r"\bkafka\b", re.I), "kafka"),
    (re.compile(r"\b(rag|retrieval|vector)\b", re.I), "rag"),
    (re.compile(r"\b(horizontal|vertical)\s+scaling\b", re.I), "scaling"),
]


def _curated_kind(topic: str, beat: dict[str, Any]) -> str | None:
    for pat, family in _CURATED_TOPICS:
        if not pat.search(topic):
            continue
        bid, btype = str(beat.get("id", "")), str(beat.get("type", ""))
        if family == "rag":
            return "rag"
        if family == "two_sum":
            if bid in ("baseline", "complexity") or btype == "comparison":
                return "compare"
            if bid in ("hashmap", "idea") or btype in ("architecture_build", "metric_callout"):
                return "hashmap"
            return "array_tape"
        if family == "kafka":
            return "partition_lanes" if ("partition" in bid or btype == "architecture_build") else "log_stream"
        if family == "scaling":
            return "compare" if (btype == "comparison" or bid == "vertical_limits") else "pool"
    return None


def _valid(kind: str, beat: dict[str, Any]) -> bool:
    nodes, steps = beat.get("nodes") or [], beat.get("steps") or []
    if kind == "compare":
        btype = str(beat.get("type", "")).lower()
        bid = str(beat.get("id", "")).lower()
        node_text = " ".join(f"{n.get('label', '')} {n.get('detail', '')}" for n in nodes if isinstance(n, dict))
        combined = f"{beat.get('title', '')} {beat.get('spoken_text', '')} {node_text}"
        has_contrast = (
            btype == "comparison"
            or bid in {"problem", "problem_or_motivation", "naive_trap", "baseline", "tradeoffs", "complexity", "vertical_limits"}
            or bool(
                re.search(
                    r"\b(vs|versus|naive|brute|slow|fail|fails|miss|loss|bottleneck|overload|without|cost|limit|crash|sort|lekin|par)\b",
                    combined,
                    re.I,
                )
            )
        )
        return len(nodes) >= 2 and has_contrast
    if kind == "stages":
        return len(nodes) >= 2 or len(steps) >= 2
    if kind == "scan":
        data = (beat.get("visual") or {}).get("data") or {}
        return bool(data.get("rows"))
    if kind == "metric":
        return bool(beat.get("metric") or beat.get("title"))
    return kind in {"hook", "summary"}


def _by_type(beat: dict[str, Any], is_first: bool = False, is_last: bool = False) -> str:
    btype, bid = str(beat.get("type", "")), str(beat.get("id", ""))
    if is_last and (btype == "summary" or bid in ("summary", "takeaway", "outro")):
        return "summary"
    if is_first and (btype == "kinetic_title" or bid == "hook"):
        return "hook"
    if btype == "comparison" and _valid("compare", beat):
        return "compare"
    if _valid("stages", beat):
        return "stages"
    if btype in ("kinetic_title",) and is_first:
        return "hook"
    return "metric"


def assign_visuals(plan: dict[str, Any], source: str = "llm") -> dict[str, Any]:
    """Annotate every beat with a validated visual kind. Mutates and returns the plan."""
    topic = str(plan.get("topic", ""))
    plan["source"] = source
    notes: list[str] = []
    beats = plan.get("beats", [])
    total = len(beats)
    for idx, beat in enumerate(beats):
        is_first = idx == 0
        is_last = idx == total - 1
        requested = str((beat.get("visual") or {}).get("kind", "")).strip().lower()
        if requested == "summary" and not is_last:
            requested = ""
        kind: str | None = None

        if source == "curated":
            kind = requested if requested in GENERIC_KINDS | CURATED_KINDS | {"scan"} and (
                requested in CURATED_KINDS or _valid(requested, beat)) else None
            kind = kind or _curated_kind(topic, beat)

        if kind is None and requested in GENERIC_KINDS and _valid(requested, beat):
            kind = requested
        if kind is None and requested in GROUNDED_KINDS:
            topic_re, beat_re = GROUNDED_KINDS[requested]
            if topic_re.search(topic) and beat_re.search(str(beat.get("spoken_text", ""))):
                kind = requested
            else:
                notes.append(f"beat '{beat.get('id')}': '{requested}' visual rejected (not grounded in narration)")
        if kind is None and requested and requested not in GENERIC_KINDS | set(GROUNDED_KINDS) | CURATED_KINDS:
            notes.append(f"beat '{beat.get('id')}': unknown visual kind '{requested}' ignored")
        if kind is None:
            kind = _auto_special(topic, beat) or _by_type(beat, is_first=is_first, is_last=is_last)

        data = (beat.get("visual") or {}).get("data") if isinstance(beat.get("visual"), dict) else None
        beat["visual"] = {"kind": kind, **({"data": data} if data else {})}
    plan["visual_notes"] = notes
    return plan


def _auto_special(topic: str, beat: dict[str, Any]) -> str | None:
    """Pick ring/gate automatically, but only when topic AND this beat's narration both talk about it."""
    if str(beat.get("type")) in ("kinetic_title", "summary", "comparison"):
        return None
    for kind, (topic_re, beat_re) in GROUNDED_KINDS.items():
        if topic_re.search(topic) and beat_re.search(str(beat.get("spoken_text", ""))):
            return kind
    return None
