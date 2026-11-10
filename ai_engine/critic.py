from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class QualityReport:
    score: float  # 0.0 to 10.0
    passed: bool
    hook_score: float
    intuition_score: float
    pacing_score: float
    cta_score: float
    feedback: list[str]


def evaluate_plan_quality(plan: dict[str, Any]) -> QualityReport:
    """Pre-render Quality Gate: Evaluates storyboard for viral storytelling,

    intuitive mental models, pacing, and engagement triggers.
    Runs in milliseconds BEFORE audio or video rendering begins.
    """
    beats = plan.get("beats", [])
    if not beats:
        return QualityReport(0.0, False, 0.0, 0.0, 0.0, 0.0, ["No beats in plan."])

    feedback: list[str] = []

    # 1. Hook Evaluation (Beat 1)
    hook_beat = beats[0]
    hook_text = str(hook_beat.get("spoken_text", "")).lower()
    hook_score = 5.0
    hook_cues = ["interview", "kaise", "kyun", "90%", "reject", "fail", "socho", "dilemma", "mistake"]
    if any(q in hook_text for q in hook_cues):
        hook_score += 4.0
    words_in_hook = len(hook_text.split())
    if words_in_hook > 22:
        hook_score -= 2.0
        feedback.append("Hook beat is too long. Keep under 18 words for an immediate scroll-stopping punch.")
    if hook_score < 6.5:
        feedback.append("Hook is too textbook-like. Start with a high-stakes interview question or common misconception.")

    # 2. Intuition & Mental Model Evaluation
    all_text = " ".join(str(b.get("spoken_text", "")) for b in beats).lower()
    intuition_score = 5.0
    mental_models = [
        "diary", "memory", "socho", "analogy", "metaphor", "example",
        "magic", "trick", "instantly", "single pass", "behind the scenes",
        "real life", "tape", "counter", "pukaaro", "khali"
    ]
    if any(m in all_text for m in mental_models):
        intuition_score += 4.0
    else:
        feedback.append("Script lacks a relatable mental model or physical analogy. Avoid purely academic definitions.")

    # 3. Pacing & Word Count Evaluation
    pacing_score = 9.0
    overlong = []
    for i, b in enumerate(beats, 1):
        count = len(str(b.get("spoken_text", "")).split())
        if count > 24:
            overlong.append(f"Beat {i} ({count} words)")
    if overlong:
        pacing_score -= min(4.0, len(overlong) * 1.5)
        feedback.append(f"Overlong beats detected: {', '.join(overlong)}. Split into punchier micro-beats.")

    # 4. CTA & Community Trigger Evaluation
    last_beat = beats[-1]
    last_text = str(last_beat.get("spoken_text", "")).lower()
    cta_score = 5.0
    cta_cues = ["comment", "pdf", "notes", "follow", "save", "cheat sheet"]
    if any(c in last_text for c in cta_cues):
        cta_score += 4.5
    else:
        feedback.append("Outro lacks an active engagement prompt (e.g. 'Comment [TOPIC] for complete PDF notes').")

    total_score = round(
        hook_score * 0.35 + intuition_score * 0.30 + pacing_score * 0.20 + cta_score * 0.15,
        1,
    )
    passed = total_score >= 7.5 and len(feedback) <= 1

    return QualityReport(
        score=total_score,
        passed=passed,
        hook_score=min(10.0, max(0.0, round(hook_score, 1))),
        intuition_score=min(10.0, max(0.0, round(intuition_score, 1))),
        pacing_score=min(10.0, max(0.0, round(pacing_score, 1))),
        cta_score=min(10.0, max(0.0, round(cta_score, 1))),
        feedback=feedback,
    )
