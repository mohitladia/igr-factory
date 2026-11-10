from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from publisher.social_publisher import (
    discover_instagram_account_id,
    publish_instagram_reel,
    upload_youtube_short,
)


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Publish an existing rendered MP4 to Instagram Reels and/or YouTube Shorts.")
    parser.add_argument("--video", type=str, required=True, help="Path to MP4 file")
    parser.add_argument("--topic", type=str, default="Consistent Hashing", help="Topic name for caption/title")
    parser.add_argument("--instagram", action="store_true", help="Publish to Instagram Reels")
    parser.add_argument("--youtube", action="store_true", help="Upload to YouTube Shorts")
    args = parser.parse_args()

    video_path = Path(args.video).resolve()
    if not video_path.exists():
        print(f"[error] Video not found: {video_path}")
        return 1

    plan = {
        "topic": args.topic,
        "beats": [
            {"title": args.topic, "spoken_text": f"{args.topic} Explained in 60 Seconds! 🔥"},
            {"title": "Problem & Naive Trap", "metric": "BOTTLENECK"},
            {"title": "Production Architecture", "metric": "HIGH SCALE"},
            {"title": "Step-by-Step Flow", "metric": "LOW LATENCY"},
            {"title": "Summary", "metric": "CHEATSHEET"},
        ],
    }

    if args.instagram:
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        ig_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "").strip()
        if token and not ig_id:
            ig_id = discover_instagram_account_id(token)
            os.environ["INSTAGRAM_BUSINESS_ACCOUNT_ID"] = ig_id
        from publisher.social_publisher import build_instagram_caption

        caption = build_instagram_caption(plan)
        res = publish_instagram_reel(video_path, caption)
        print(f"[done] Instagram Reel Published: {res}")

    if args.youtube:
        res = upload_youtube_short(video_path, plan)
        print(f"[done] YouTube Short Uploaded: {res}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
