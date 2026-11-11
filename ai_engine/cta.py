"""Single definition of the 'Comment <KEYWORD>' call-to-action word.

Voice, on-screen outro card, captions and the Instagram DM bot must all use the SAME keyword,
otherwise viewers comment a word the bot is not listening for.
"""
from __future__ import annotations

import re

_SKIP = {"valid", "the", "an", "a", "of", "in", "to", "and", "vs", "problem", "solution", "leetcode",
         "how", "what", "why", "design", "implementation"}


def cta_keyword(topic: str) -> str:
    """'Valid Anagram' -> ANAGRAM, 'Database Sharding' -> SHARDING, 'Two Sum' -> SUM."""
    words = [w for w in re.findall(r"[A-Za-z0-9]+", topic or "") if w.lower() not in _SKIP]
    return (words[-1] if words else "NOTES").upper()[:12]


def plan_keyword(plan: dict, topic: str = "") -> str:
    return str(plan.get("cta_keyword") or cta_keyword(topic or str(plan.get("topic", ""))))
