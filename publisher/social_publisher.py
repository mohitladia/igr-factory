from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
IG_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"


def _get_ig_api_base(access_token: str) -> str:
    return IG_GRAPH_API_BASE if access_token.strip().startswith("IG") else GRAPH_API_BASE


def discover_instagram_account_id(access_token: str) -> str:
    """
    Auto-discover Instagram Professional Account ID from either:
    1. An `IGAA...` token (Instagram API with Instagram Login — no Facebook Page needed)
    2. An `EAA...` token (Facebook Login / Graph API Explorer linked to a Facebook Page)
    """
    token = access_token.strip()
    if token.startswith("IG"):
        resp = requests.get(
            f"{IG_GRAPH_API_BASE}/me",
            params={"fields": "user_id,id,username", "access_token": token},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        ig_id = str(data.get("user_id") or data.get("id") or "")
        if ig_id:
            print(f"[instagram] Found Instagram account @{data.get('username')} (ID: {ig_id}) via Instagram Login token")
            return ig_id

    resp = requests.get(
        f"{GRAPH_API_BASE}/me/accounts",
        params={"fields": "id,name,instagram_business_account{id,username}", "access_token": token},
        timeout=20,
    )
    resp.raise_for_status()
    pages = resp.json().get("data", [])
    for page in pages:
        ig = page.get("instagram_business_account")
        if ig and ig.get("id"):
            print(f"[instagram] Found Instagram account @{ig.get('username')} (ID: {ig['id']}) linked to Page '{page.get('name')}'")
            return str(ig["id"])
    raise RuntimeError(
        "Could not auto-discover Instagram Professional Account ID. "
        "Ensure your Instagram account is switched to Creator/Business."
    )


def build_instagram_caption(plan: dict[str, Any]) -> str:
    topic = plan.get("topic", "System Design")
    beats = plan.get("beats", [])
    hook_text = beats[0].get("spoken_text", "") if beats else f"{topic} Explained!"
    keyword = "".join(ch for ch in topic if ch.isalnum()).upper()[:12] or "NOTES"
    slug_tag = keyword.lower()

    bullet_lines = []
    for b in beats[1:-1]:
        title = b.get("title", "Core Stage")
        metric = b.get("metric", "")
        bullet_lines.append(f"⚡ {title}" + (f" ({metric})" if metric else ""))

    caption = (
        f"{hook_text}\n\n"
        f"📌 {topic} Production Breakdown:\n"
        + "\n".join(bullet_lines)
        + f"\n\n💬 Comment '{keyword}' aur main aapko {topic} ka complete PDF Interview Cheat Sheet & Architecture Notes सीधा DM bhej dunga! 🚀\n\n"
        f"🔖 Save kar lo — agle System Design interview mein 100% kaam aayega!\n"
        f"👉 Follow @conceptfirstwithmohit — Technology yaad rakhne se nahi, sochne se aati hai.\n\n"
        f"#{slug_tag} #conceptfirstwithmohit #systemdesign #backendengineering #softwareengineering #codinginterview "
        f"#techreels #indiandevs #leetcode #microservices #scalability #devops #dsa #hinglish"
    )
    return caption


def write_instagram_metadata(plan: dict[str, Any], destination: Path) -> str:
    topic = plan.get("topic", "System Design")
    keyword = "".join(ch for ch in topic if ch.isalnum()).upper()[:12] or "NOTES"
    caption = build_instagram_caption(plan)
    content = (
        "=== INSTAGRAM REEL PUBLISH & DM AUTOMATION METADATA ===\n\n"
        f"DM TRIGGER KEYWORD:\n{keyword}\n\n"
        f"AUTO-DM MESSAGE TEMPLATE:\n"
        f"Hey! 👋 Yeh raha aapka {topic} PDF Interview Cheat Sheet & Architecture Guide: "
        f"{os.getenv('CHEATSHEET_DEFAULT_URL', 'https://github.com/mohitladia/igr-factory')} 🚀 All the best for your interviews!\n\n"
        f"CAPTION (Copy-Paste or Auto-Published via Graph API):\n"
        f"{caption}\n"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return caption


def write_youtube_shorts_metadata(plan: dict[str, Any], destination: Path) -> dict[str, Any]:
    topic = plan.get("topic", "System Design")
    beats = plan.get("beats", [])
    hook_text = beats[0].get("spoken_text", "") if beats else ""
    slug_tag = "".join(ch for ch in topic if ch.isalnum()).lower()
    cursor_sec = 0.0
    chapters = []
    for b in beats:
        mm = int(cursor_sec // 60)
        ss = int(cursor_sec % 60)
        chapters.append(f"{mm:02d}:{ss:02d} - {b.get('title', 'Concept')}")
        cursor_sec += float(b.get("audio_duration_seconds") or 8.0)

    title = f"{topic} Explained in 60 Seconds! 🔥 (Interview Trick) #shorts #systemdesign"[:100]
    description = (
        f"{hook_text}\n\n"
        f"In this Hinglish System Design & Backend Engineering Short, we break down {topic} with real production architecture and motion graphics:\n"
        + "\n".join(chapters)
        + f"\n\n💡 Concept First with Mohit (@ConceptFirstWithMohit)\n"
        f"Technology yaad rakhne se nahi, sochne se aati hai.\n\n"
        f"#shorts #youtubeshorts #{slug_tag} #conceptfirstwithmohit #systemdesign #backendengineering #codinginterview #softwareengineering #hinglish #techshorts"
    )
    tags = [
        topic,
        f"{topic} system design",
        f"{topic} explained in hindi",
        f"{topic} interview questions",
        "system design hinglish",
        "backend engineering shorts",
        "coding interview preparation",
        "software architecture",
        "tech shorts india",
    ]
    pinned = f"📌 Free {topic} PDF Interview Cheat Sheet & Architecture Notes! Subscribe & reply '{topic.upper()}' below to get the link! 🚀"

    meta_text = (
        f"=== YOUTUBE SHORTS UPLOAD METADATA ===\n\n"
        f"TITLE (Copy-Paste):\n{title}\n\n"
        f"DESCRIPTION (Copy-Paste):\n{description}\n\n"
        f"PINNED COMMENT (Copy-Paste):\n{pinned}\n\n"
        f"TAGS (Copy-Paste):\n{', '.join(tags)}\n"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(meta_text, encoding="utf-8")
    return {"title": title, "description": description, "tags": tags, "pinned_comment": pinned}


def _upload_temp_public_video(video_path: Path) -> str:
    """
    Instagram Graph API requires a publicly reachable HTTPS URL for the MP4 video.
    If PUBLIC_VIDEO_URL is not set, uploads temporarily to catbox.moe / 0x0.st.
    """
    explicit_url = os.getenv("PUBLIC_VIDEO_URL", "").strip()
    if explicit_url:
        return explicit_url

    with video_path.open("rb") as fh:
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (video_path.name, fh, "video/mp4")},
            timeout=180,
        )
        if resp.status_code == 200 and resp.text.strip().startswith("https://"):
            return resp.text.strip()

    raise RuntimeError(
        "Could not stage local MP4 to a public URL automatically. Set PUBLIC_VIDEO_URL in .env or check network."
    )


def publish_instagram_reel(video_path: Path, caption: str, share_to_feed: bool = True) -> dict[str, Any]:
    """
    Publish an MP4 Reel to an Instagram Business/Creator account using Meta's official Graph API
    (same workflow as @mcpware/instagram-mcp `publish_media`).
    """
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    ig_user_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "").strip()
    if not access_token:
        raise RuntimeError(
            "Missing INSTAGRAM_ACCESS_TOKEN in .env. "
            "Add your Meta Graph API credentials to auto-publish Reels."
        )
    if not ig_user_id:
        ig_user_id = discover_instagram_account_id(access_token)
        os.environ["INSTAGRAM_BUSINESS_ACCOUNT_ID"] = ig_user_id
    api_base = _get_ig_api_base(access_token)

    print("[instagram] Staging MP4 to public URL for Meta Graph API ingestion...")
    video_url = _upload_temp_public_video(video_path)
    print(f"[instagram] Public video URL ready: {video_url}")

    # Step 1: Create Reel Media Container
    create_resp = requests.post(
        f"{api_base}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true" if share_to_feed else "false",
            "access_token": access_token,
        },
        timeout=60,
    )
    create_resp.raise_for_status()
    creation_id = create_resp.json().get("id")
    if not creation_id:
        raise RuntimeError(f"Instagram media container creation failed: {create_resp.text}")
    print(f"[instagram] Created Reel container ID: {creation_id}. Waiting for Meta video processing...")

    # Step 2: Poll Container Status until FINISHED
    for _ in range(30):
        time.sleep(5)
        status_resp = requests.get(
            f"{api_base}/{creation_id}",
            params={"fields": "status_code,status", "access_token": access_token},
            timeout=30,
        )
        status_resp.raise_for_status()
        status_data = status_resp.json()
        code = status_data.get("status_code")
        print(f"[instagram] Container status: {code}")
        if code == "FINISHED":
            break
        if code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram container processing failed: {status_data}")
    else:
        raise RuntimeError("Timed out waiting for Instagram Reel container processing.")

    # Step 3: Publish Container
    pub_resp = requests.post(
        f"{api_base}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=60,
    )
    pub_resp.raise_for_status()
    media_id = pub_resp.json().get("id")
    print(f"[instagram] Reel published! Media ID: {media_id}")
    return {"creation_id": creation_id, "media_id": media_id, "video_url": video_url}


def auto_dm_keyword_comments(keyword: str, cheatsheet_url: str, media_id: str | None = None) -> dict[str, Any]:
    """
    Scan comments on the latest Instagram Reel (or specified `media_id`) for `keyword`
    and send an automated Private Reply DM + public comment reply via Instagram Graph API
    (matching @mcpware/instagram-mcp DM & comment management).
    """
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    ig_user_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "").strip()
    if not access_token or not ig_user_id:
        raise RuntimeError("Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ACCOUNT_ID in .env.")

    if not media_id:
        media_resp = requests.get(
            f"{GRAPH_API_BASE}/{ig_user_id}/media",
            params={"fields": "id,caption,timestamp", "limit": 1, "access_token": access_token},
            timeout=30,
        )
        media_resp.raise_for_status()
        items = media_resp.json().get("data", [])
        if not items:
            return {"checked": 0, "dms_sent": 0}
        media_id = items[0]["id"]

    comments_resp = requests.get(
        f"{GRAPH_API_BASE}/{media_id}/comments",
        params={"fields": "id,text,username", "limit": 50, "access_token": access_token},
        timeout=30,
    )
    comments_resp.raise_for_status()
    comments = comments_resp.json().get("data", [])

    kw_upper = keyword.strip().upper()
    dms_sent = 0
    for c in comments:
        text = str(c.get("text", "")).upper()
        cid = c.get("id")
        if kw_upper in text and cid:
            # Send Private Reply DM linked to the comment
            dm_resp = requests.post(
                f"{GRAPH_API_BASE}/{ig_user_id}/messages",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={
                    "recipient": {"comment_id": cid},
                    "message": {
                        "text": f"Hey @{c.get('username', 'dev')}! 🚀 Yeh raha aapka PDF Interview Cheat Sheet & Notes: {cheatsheet_url}"
                    },
                },
                timeout=30,
            )
            if dm_resp.status_code in {200, 201}:
                dms_sent += 1
    return {"media_id": media_id, "checked": len(comments), "dms_sent": dms_sent}


def upload_youtube_short(video_path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    """
    Upload the rendered YouTube Short MP4 directly to YouTube via YouTube Data API v3
    using YOUTUBE_ACCESS_TOKEN in .env.
    """
    yt_token = os.getenv("YOUTUBE_ACCESS_TOKEN", "").strip()
    if not yt_token:
        raise RuntimeError(
            "Missing YOUTUBE_ACCESS_TOKEN in .env. Add a valid OAuth2 access token with "
            "'https://www.googleapis.com/auth/youtube.upload' scope to auto-upload Shorts."
        )

    meta = write_youtube_shorts_metadata(plan, video_path.with_name(f"{video_path.stem}_youtube_metadata.txt"))
    privacy = os.getenv("YOUTUBE_PRIVACY_STATUS", "public")
    metadata_body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": "28",  # Science & Technology
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Resumable upload initiation
    init_resp = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization": f"Bearer {yt_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(video_path.stat().st_size),
            "X-Upload-Content-Type": "video/mp4",
        },
        data=json.dumps(metadata_body),
        timeout=60,
    )
    init_resp.raise_for_status()
    upload_url = init_resp.headers.get("Location")
    if not upload_url:
        raise RuntimeError("YouTube resumable upload did not return a Location header.")

    with video_path.open("rb") as fh:
        up_resp = requests.put(
            upload_url,
            headers={"Content-Type": "video/mp4"},
            data=fh,
            timeout=300,
        )
    up_resp.raise_for_status()
    video_id = up_resp.json().get("id")
    print(f"[youtube] Short uploaded! URL: https://youtube.com/shorts/{video_id}")
    return {"video_id": video_id, "url": f"https://youtube.com/shorts/{video_id}"}
