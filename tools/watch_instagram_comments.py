from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from publisher.social_publisher import auto_dm_keyword_comments


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Poll one Instagram Reel and DM each matching commenter once.")
    parser.add_argument("--media-id", required=True, help="Instagram media ID printed after publishing the Reel")
    parser.add_argument("--keyword", required=True, help="Comment keyword to match, e.g. TWOSUM")
    parser.add_argument("--cheatsheet-url", default="", help="Public PDF URL; defaults to CHEATSHEET_DEFAULT_URL in .env")
    parser.add_argument("--interval-seconds", type=int, default=120, help="Polling interval (minimum 30 seconds)")
    args = parser.parse_args()

    cheatsheet_url = args.cheatsheet_url.strip() or os.getenv("CHEATSHEET_DEFAULT_URL", "").strip()
    if not cheatsheet_url:
        parser.error("Set --cheatsheet-url or CHEATSHEET_DEFAULT_URL in .env")
    interval = max(30, args.interval_seconds)
    print(f"[instagram-dm] Watching media {args.media_id} every {interval}s. Press Ctrl+C to stop.")
    try:
        while True:
            try:
                result = auto_dm_keyword_comments(
                    args.keyword,
                    cheatsheet_url,
                    media_id=args.media_id,
                )
                print(f"[instagram-dm] Checked {result['checked']} new comments; sent {result['dms_sent']} DMs.")
            except Exception as exc:
                print(f"[instagram-dm] Poll failed; will retry: {exc}", file=sys.stderr)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[instagram-dm] Watch stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
