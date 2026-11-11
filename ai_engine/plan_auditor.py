"""Narration <-> visual consistency audit.

Checks that everything a viewer SEES in a beat (node labels, steps, metric, numbers) is something
the narrator actually SAYS somewhere in the script, and that known cross-topic leak terms never
appear unless the topic is about them. Offending visual items are removed (and reported) so the
renderer falls back to a smaller but truthful visual instead of showing unrelated content.
"""
from __future__ import annotations

import re
from typing import Any

LEAK_TERMS = [
    "429", "hash ring", "token bucket", "leaky bucket", "kafka", "load balancer",
    "http 200", "partition", "consumer group", "vector db", "embedding",
]
_STOP = set(
    "the and for with that this from into over only each every same what when then than also your about "
    "time data core fast slow high low full step stage layer engine state output input result "
    "count total value values item items index list size".split()
)
_WORD = re.compile(r"[a-z][a-z0-9]+")
_NUM = re.compile(r"\d{2,}")


def _words(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def _visual_strings(beat: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for i, n in enumerate(beat.get("nodes") or []):
        out.append((f"nodes[{i}]", f"{n.get('label', '')} {n.get('detail', '')}"))
    for i, s in enumerate(beat.get("steps") or []):
        out.append((f"steps[{i}]", f"{s.get('label', '')} {s.get('detail', '')}"))
    return out


def audit_and_sanitize(plan: dict[str, Any], fix: bool = True) -> dict[str, Any]:
    """Return {errors, warnings, removed}. With fix=True ungrounded visual items are dropped from the plan;
    fix=False (hand-written curated plans) only reports."""
    errors: list[str] = []
    warnings: list[str] = []
    removed = 0
    topic_low = str(plan.get("topic", "")).lower()
    all_spoken = " ".join(str(b.get("spoken_text", "")) for b in plan.get("beats", [])).lower()
    active_leak_terms = [
        t for t in LEAK_TERMS
        if t not in topic_low and not any(w in topic_low for w in t.split() if len(w) >= 5)
        and t not in all_spoken
    ]

    for beat in plan.get("beats", []):
        bid = beat.get("id")
        spoken = str(beat.get("spoken_text", "")).lower()
        # Check against this beat only; a number/concept spoken elsewhere does not ground this visual.
        script_words = _words(spoken) | _words(topic_low)
        script_nums = set(_NUM.findall(spoken))
        # 1) metric grounding
        metric = str(beat.get("metric", ""))
        for term in active_leak_terms:
            if term in metric.lower() and term not in spoken:
                warnings.append(f"beat '{bid}': metric '{metric}' mentions '{term}' which is never said; metric cleared")
                beat["metric"] = "" if fix else beat.get("metric", "")
                break
        else:
            bad_nums = [n for n in _NUM.findall(metric) if n not in script_nums]
            if bad_nums:
                warnings.append(f"beat '{bid}': metric number(s) {bad_nums} not in narration; metric cleared")
                if fix:
                    beat["metric"] = ""

        # 2) nodes / steps grounding
        for key in ("nodes", "steps"):
            keep = []
            for i, item in enumerate(beat.get(key) or []):
                label_str = str(item.get("label", "")).strip()
                detail_str = str(item.get("detail", "")).strip()
                if key == "steps" and re.fullmatch(r"step\s*\d+", label_str, re.I) and not detail_str:
                    if fix:
                        removed += 1
                        continue
                text = f"{label_str} {detail_str}"
                low = text.lower()
                leaked = [t for t in active_leak_terms if t in low and t not in spoken]
                bad_nums = [n for n in _NUM.findall(low) if n not in script_nums]
                content = [w for w in _words(low) if len(w) >= 4 and w not in _STOP]
                grounded = sum(1 for w in content if w in script_words or any(w.startswith(s[:5]) for s in script_words if len(s) >= 5))
                ratio = grounded / len(content) if content else 1.0
                if (leaked or bad_nums) and fix:
                    errors.append(f"beat '{bid}' {key}[{i}] '{item.get('label')}': unrelated to narration "
                                  f"(leak={leaked}, numbers={bad_nums}) - removed")
                    removed += 1
                    continue
                if leaked or bad_nums:
                    warnings.append(f"beat '{bid}' {key}[{i}] '{item.get('label')}': not grounded (leak={leaked}, numbers={bad_nums})")
                if ratio < 0.34:
                    warnings.append(f"beat '{bid}' {key}[{i}] '{item.get('label')}': only {int(ratio*100)}% of its words appear in the script")
                keep.append(item)
            if len(keep) != len(beat.get(key) or []):
                beat[key] = keep
                if beat.get("connections"):
                    beat["connections"] = []

        # 3) caption/voice divergence guard (tts is derived, so only a defensive check)
        if not str(beat.get("spoken_text", "")).strip():
            errors.append(f"beat '{bid}': empty narration")

    plan["audit"] = {"errors": errors, "warnings": warnings, "removed_visual_items": removed}
    return plan["audit"]
