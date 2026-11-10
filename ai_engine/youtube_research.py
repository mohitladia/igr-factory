from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote_plus

import requests


def fetch_youtube_research(topic: str, max_results: int = 3) -> dict[str, Any]:
    """
    Search YouTube for top viral videos/Shorts on `topic` (without requiring an official YouTube API key,
    inspired by ia-programming/youtube-mcp) and extract titles, view counts, and transcript snippets
    when available to ground LLM reel script generation.
    """
    query = f"{topic} system design explained"
    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    videos: list[dict[str, str]] = []
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            match = re.search(r"var ytInitialData = (\{.*?\});</script>", resp.text)
            if match:
                data = json.loads(match.group(1))
                contents = (
                    data.get("contents", {})
                    .get("twoColumnSearchResultsRenderer", {})
                    .get("primaryContents", {})
                    .get("sectionListRenderer", {})
                    .get("contents", [])
                )
                for section in contents:
                    items = section.get("itemSectionRenderer", {}).get("contents", [])
                    for item in items:
                        vr = item.get("videoRenderer")
                        if not vr:
                            continue
                        vid = vr.get("videoId", "")
                        title_runs = vr.get("title", {}).get("runs", [])
                        title = "".join(r.get("text", "") for r in title_runs).strip()
                        snippet_runs = []
                        for snip in vr.get("detailedMetadataSnippets", []):
                            snippet_runs.extend(snip.get("snippetText", {}).get("runs", []))
                        description = "".join(r.get("text", "") for r in snippet_runs).strip()
                        views = vr.get("shortViewCountText", {}).get("simpleText", "")
                        if vid and title:
                            videos.append(
                                {
                                    "video_id": vid,
                                    "title": title,
                                    "views": views,
                                    "snippet": description,
                                }
                            )
                        if len(videos) >= max_results:
                            break
                    if len(videos) >= max_results:
                        break
    except Exception:
        pass

    # Optionally enrich with youtube_transcript_api if installed
    transcript_excerpts: list[str] = []
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore

        for v in videos[:2]:
            try:
                t_list = YouTubeTranscriptApi.get_transcript(v["video_id"], languages=["hi", "en", "en-IN"])
                snippet_text = " ".join(part.get("text", "") for part in t_list[:25]).strip()
                if snippet_text:
                    transcript_excerpts.append(f"[{v['title']}]: {snippet_text[:350]}")
            except Exception:
                continue
    except ImportError:
        pass

    summary_lines = []
    for v in videos:
        line = f"- {v['title']} ({v['views']}): {v['snippet']}"
        summary_lines.append(line.strip())
    if transcript_excerpts:
        summary_lines.extend(transcript_excerpts)

    return {
        "topic": topic,
        "videos": videos,
        "context_block": "\n".join(summary_lines)[:1200] if summary_lines else "",
    }
