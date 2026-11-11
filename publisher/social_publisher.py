from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

def _graph_api_base(instagram_login: bool = False) -> str:
    version = os.getenv("META_GRAPH_API_VERSION", "v27.0").strip()
    if not version or "/" in version:
        raise ValueError("META_GRAPH_API_VERSION must be a version such as v27.0")
    host = "graph.instagram.com" if instagram_login else "graph.facebook.com"
    return f"https://{host}/{version}"


def _catbox_upload_allowed() -> bool:
    return os.getenv("ALLOW_PUBLIC_CATBOX_UPLOADS", "false").strip().lower() in {"1", "true", "yes"}


def _get_ig_api_base(access_token: str) -> str:
    return _graph_api_base(instagram_login=access_token.strip().startswith("IG"))


def discover_instagram_account_id(access_token: str) -> str:
    """
    Auto-discover Instagram Professional Account ID from either:
    1. An `IGAA...` token (Instagram API with Instagram Login — no Facebook Page needed)
    2. An `EAA...` token (Facebook Login / Graph API Explorer linked to a Facebook Page)
    """
    token = access_token.strip()
    if token.startswith("IG"):
        resp = requests.get(
            f"{_graph_api_base(instagram_login=True)}/me",
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
        f"{_graph_api_base()}/me/accounts",
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

    family = str(plan.get("topic_family", "general_technical")).lower()
    family_tags = {
        "dsa": "#codinginterview #leetcode",
        "distributed_messaging": "#kafka #distributedSystems",
        "caching": "#redis #caching",
        "backend_framework": "#backendengineering #softwaredevelopment",
        "programming_language": "#programming #softwareengineering",
        "system_design": "#systemdesign #softwarearchitecture",
        "general_technical": "#technology #softwareengineering",
    }
    tags = f"#{slug_tag} #conceptfirstwithmohit #techreels #indiandevs #hinglish {family_tags.get(family, family_tags['general_technical'])}"
    if plan.get("auto_dm_enabled") and plan.get("cheatsheet_url"):
        call_to_action = f"\n\n💬 Comment '{keyword}' aur main aapko {topic} ki PDF notes DM karunga! 🚀"
    else:
        call_to_action = "\n\n🔖 Save kar lo aur aise explainers ke liye follow karo."
    caption = (
        f"{hook_text}\n\n"
        f"📌 {topic} breakdown:\n"
        + "\n".join(bullet_lines)
        + call_to_action
        + f"\n\n👉 Follow @conceptfirstwithmohit — Technology yaad rakhne se nahi, sochne se aati hai.\n\n"
        + tags
    )
    return caption


def write_instagram_metadata(plan: dict[str, Any], destination: Path) -> str:
    topic = plan.get("topic", "System Design")
    keyword = "".join(ch for ch in topic if ch.isalnum()).upper()[:12] or "NOTES"
    caption = build_instagram_caption(plan)
    dm_status = "Enabled for this run" if plan.get("auto_dm_enabled") and plan.get("cheatsheet_url") else "Disabled (manual CTA only)"
    content = (
        "=== INSTAGRAM REEL PUBLISH & DM AUTOMATION METADATA ===\n\n"
        f"DM TRIGGER KEYWORD:\n{keyword}\n\n"
        f"AUTO-DM STATUS:\n{dm_status}\n\n"
        f"AUTO-DM MESSAGE TEMPLATE:\n"
        f"Hey! 👋 Yeh raha aapka {topic} PDF Interview Cheat Sheet & Architecture Guide: "
        f"{plan.get('cheatsheet_url') or '[PDF link not configured]'} 🚀 All the best for your interviews!\n\n"
        f"CAPTION (Copy-Paste or Auto-Published via Graph API):\n"
        f"{caption}\n"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return caption


def write_youtube_shorts_metadata(
    plan: dict[str, Any],
    destination: Path,
    cheatsheet_url: str | None = None,
) -> dict[str, Any]:
    topic = plan.get("topic", "System Design")
    beats = plan.get("beats", [])
    hook_text = beats[0].get("spoken_text", "") if beats else ""
    slug_tag = "".join(ch for ch in topic if ch.isalnum()).lower()
    pdf_link = (cheatsheet_url or plan.get("cheatsheet_url") or os.getenv("CHEATSHEET_DEFAULT_URL", "")).strip()
    cursor_sec = 0.0
    chapters = []
    for b in beats:
        mm = int(cursor_sec // 60)
        ss = int(cursor_sec % 60)
        chapters.append(f"{mm:02d}:{ss:02d} - {b.get('title', 'Concept')}")
        cursor_sec += float(b.get("audio_duration_seconds") or 8.0)

    pdf_banner = f"📄 Free {topic} PDF Interview Cheat Sheet: {pdf_link}\n\n" if pdf_link else ""
    family = str(plan.get("topic_family", "general_technical")).lower()
    family_label = family.replace("_", " ")
    title_tag = {
        "dsa": "#codinginterview",
        "distributed_messaging": "#distributedSystems",
        "caching": "#caching",
        "backend_framework": "#backendengineering",
        "programming_language": "#programming",
        "system_design": "#systemdesign",
        "general_technical": "#technology",
    }.get(family, "#technology")
    title = f"{topic[:60]} Explained in Hinglish {title_tag} #Shorts"[:100]
    description = (
        f"{pdf_banner}"
        f"{hook_text}\n\n"
        f"In this Hinglish {family_label} Short, we break down {topic} with a concise visual explanation:\n"
        + "\n".join(chapters)
        + f"\n\n💡 Concept First with Mohit (@ConceptFirstWithMohit)\n"
        f"Technology yaad rakhne se nahi, sochne se aati hai.\n\n"
        f"#shorts #youtubeshorts #{slug_tag} #conceptfirstwithmohit {title_tag} #softwareengineering #hinglish #techshorts"
    )
    tags = [
        topic,
        f"{topic} explained",
        f"{topic} explained in hindi",
        f"{topic} interview questions",
        f"{family_label} hinglish",
        "coding interview preparation" if family == "dsa" else "software engineering",
        "software architecture" if family == "system_design" else "technology explained",
        "tech shorts india",
    ]
    pinned = (
        f"📌 Free {topic} PDF Interview Cheat Sheet & Architecture Notes: {pdf_link} 🚀"
        if pdf_link
        else f"📌 Free {topic} PDF Interview Cheat Sheet & Architecture Notes! Subscribe & reply '{topic.upper()}' below to get the link! 🚀"
    )

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
    If PUBLIC_VIDEO_URL is not set, Catbox upload requires explicit opt-in.
    """
    explicit_url = os.getenv("PUBLIC_VIDEO_URL", "").strip()
    if explicit_url:
        if not explicit_url.startswith("https://"):
            raise ValueError("PUBLIC_VIDEO_URL must be a publicly reachable HTTPS URL")
        return explicit_url

    if not _catbox_upload_allowed():
        raise RuntimeError(
            "Instagram needs a public HTTPS video URL. Set PUBLIC_VIDEO_URL to your own hosted MP4, "
            "or explicitly enable ALLOW_PUBLIC_CATBOX_UPLOADS=true to send it to Catbox."
        )

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

    api_base = _get_ig_api_base(access_token)
    if not media_id:
        media_resp = requests.get(
            f"{api_base}/{ig_user_id}/media",
            params={"fields": "id,caption,timestamp", "limit": 1, "access_token": access_token},
            timeout=30,
        )
        media_resp.raise_for_status()
        items = media_resp.json().get("data", [])
        if not items:
            return {"checked": 0, "dms_sent": 0}
        media_id = items[0]["id"]

    state_dir = Path(__file__).resolve().parent.parent / "output" / "state" / "instagram_dm"
    state_dir.mkdir(parents=True, exist_ok=True)
    safe_media_id = "".join(ch for ch in str(media_id) if ch.isalnum() or ch in "-_")
    if not safe_media_id:
        raise ValueError("Instagram returned an invalid media ID")
    state_path = state_dir / f"{safe_media_id}.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"Instagram DM state is unreadable ({state_path}); refusing to risk duplicate DMs.") from exc
    if not isinstance(state, dict):
        raise RuntimeError(f"Instagram DM state has an invalid format ({state_path}); refusing to risk duplicate DMs.")
    sent_ids = set(str(item) for item in state.get("sent_comment_ids", []))
    processed_ids = set(str(item) for item in state.get("processed_comment_ids", []))

    comments: list[dict[str, Any]] = []
    after: str | None = None
    while True:
        params: dict[str, Any] = {"fields": "id,text,username", "limit": 100, "access_token": access_token}
        if after:
            params["after"] = after
        comments_resp = requests.get(f"{api_base}/{media_id}/comments", params=params, timeout=30)
        comments_resp.raise_for_status()
        page = comments_resp.json()
        page_comments = page.get("data", [])
        unseen = [comment for comment in page_comments if str(comment.get("id", "")) not in processed_ids]
        if not unseen:
            break
        comments.extend(unseen)
        paging = page.get("paging", {})
        next_after = paging.get("cursors", {}).get("after")
        if not paging.get("next") or not next_after or next_after == after:
            break
        after = str(next_after)

    kw_upper = "".join(ch for ch in keyword.upper() if ch.isalnum())
    dms_sent = 0
    processed_this_run = 0
    for c in comments:
        cid = c.get("id")
        text = "".join(ch for ch in str(c.get("text", "")).upper() if ch.isalnum())
        if kw_upper and kw_upper in text and cid and str(cid) not in sent_ids:
            # Send Private Reply DM linked to the comment
            dm_resp = requests.post(
                f"{api_base}/{ig_user_id}/messages",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={
                    "recipient": {"comment_id": cid},
                    "message": {
                        "text": f"Hey @{c.get('username', 'dev')}! 🚀 Yeh raha aapka PDF Interview Cheat Sheet & Notes: {cheatsheet_url}"
                    },
                },
                timeout=30,
            )
            if dm_resp.status_code not in {200, 201}:
                raise RuntimeError(f"Instagram DM failed for comment {cid}: HTTP {dm_resp.status_code} {dm_resp.text[:300]}")
            sent_ids.add(str(cid))
            dms_sent += 1
        if cid:
            processed_ids.add(str(cid))
            processed_this_run += 1
        state_tmp = state_path.with_suffix(".json.tmp")
        state_tmp.write_text(
            json.dumps(
                {
                    "media_id": media_id,
                    "sent_comment_ids": sorted(sent_ids),
                    "processed_comment_ids": sorted(processed_ids),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        state_tmp.replace(state_path)
    return {"media_id": media_id, "checked": processed_this_run, "dms_sent": dms_sent}


def upload_public_asset(file_path: Path, mime_type: str = "application/pdf") -> str:
    """Uploads a local PDF Cheat Sheet or MP4 to catbox.moe and returns a public HTTPS URL."""
    if not _catbox_upload_allowed():
        raise RuntimeError(
            "Catbox is a public third-party host. Set ALLOW_PUBLIC_CATBOX_UPLOADS=true to opt in, "
            "or provide your own public asset URL."
        )
    with file_path.open("rb") as fh:
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (file_path.name, fh, mime_type)},
            timeout=120,
        )
        if resp.status_code == 200 and resp.text.strip().startswith("https://"):
            return resp.text.strip()
    raise RuntimeError(f"Could not upload {file_path.name} to public storage.")


def ensure_cheatsheet_url(plan: dict[str, Any], pdf_path: Path) -> str:
    """Resolve a public link for the generated PDF only when the user enabled DM delivery."""
    configured = os.getenv("CHEATSHEET_DEFAULT_URL", "").strip()
    if configured:
        if not configured.startswith("https://"):
            raise ValueError("CHEATSHEET_DEFAULT_URL must be a publicly reachable HTTPS URL")
        plan["cheatsheet_url"] = configured
        return configured
    if not pdf_path.exists():
        raise RuntimeError(f"Generated PDF not found: {pdf_path}")
    url = upload_public_asset(pdf_path, "application/pdf")
    plan["cheatsheet_url"] = url
    return url


def refresh_youtube_access_token() -> str:
    """
    Exchanges YOUTUBE_REFRESH_TOKEN in .env for a fresh YOUTUBE_ACCESS_TOKEN.

    Preferred (permanent): if YOUTUBE_CLIENT_ID + YOUTUBE_CLIENT_SECRET are set (your own
    Google Cloud OAuth client), refresh directly against oauth2.googleapis.com.
    Fallback: Google OAuth Playground's refresh endpoint. Note that refresh tokens issued to the
    Playground's default client are auto-revoked by Google after ~24 hours.
    """
    refresh_tok = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()
    if not refresh_tok:
        raise RuntimeError("Missing YOUTUBE_REFRESH_TOKEN in .env for automatic token refresh.")
    client_id = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
    if client_id and client_secret:
        resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_tok,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
    else:
        resp = requests.post(
            "https://developers.google.com/oauthplayground/refreshAccessToken",
            json={"token_uri": "https://oauth2.googleapis.com/token", "refresh_token": refresh_tok},
            timeout=30,
        )
    body_text = resp.text
    if "invalid_grant" in body_text:
        raise RuntimeError(
            "YouTube refresh token expired or revoked (invalid_grant). Tokens from OAuth Playground's "
            "default client expire after ~24h. Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET from your "
            "own Google Cloud OAuth client (app published 'In production') and generate a new refresh token."
        )
    resp.raise_for_status()
    new_token = str(resp.json().get("access_token") or "").strip()
    if not new_token:
        raise RuntimeError(f"OAuth token refresh did not return an access_token: {body_text}")
    os.environ["YOUTUBE_ACCESS_TOKEN"] = new_token
    return new_token


def upload_youtube_short(
    video_path: Path,
    plan: dict[str, Any],
    pdf_path: Path | None = None,
    cover_path: Path | None = None,
) -> dict[str, Any]:
    """
    Upload the rendered YouTube Short MP4 directly to YouTube via YouTube Data API v3,
    automatically refreshing YOUTUBE_ACCESS_TOKEN if expired, attaching the public
    PDF Cheat Sheet download link in the description, and setting the custom cover thumbnail.
    """
    yt_token = os.getenv("YOUTUBE_ACCESS_TOKEN", "").strip()
    if not yt_token and os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip():
        yt_token = refresh_youtube_access_token()
    if not yt_token:
        raise RuntimeError(
            "Missing YOUTUBE_ACCESS_TOKEN in .env. Add a valid OAuth2 access token with "
            "'https://www.googleapis.com/auth/youtube.upload' scope to auto-upload Shorts."
        )

    # Auto-discover matching *_cheatsheet.pdf and *_cover.png if not explicitly passed
    base_stem = video_path.stem.replace("_shorts", "").replace("_reel", "")
    if pdf_path is None:
        candidate_pdf = video_path.with_name(f"{base_stem}_cheatsheet.pdf")
        if candidate_pdf.exists():
            pdf_path = candidate_pdf
    if cover_path is None:
        candidate_cover = video_path.with_name(f"{base_stem}_cover.png")
        if candidate_cover.exists():
            cover_path = candidate_cover

    cheatsheet_url = str(plan.get("cheatsheet_url") or "").strip()
    if not cheatsheet_url and pdf_path and pdf_path.exists():
        try:
            print(f"[youtube] Uploading {pdf_path.name} for public download link in description...")
            cheatsheet_url = upload_public_asset(pdf_path, "application/pdf")
            plan["cheatsheet_url"] = cheatsheet_url
            print(f"[youtube] Public PDF Cheat Sheet link ready: {cheatsheet_url}")
        except Exception as pdf_exc:
            print(f"[youtube-warn] Could not stage PDF link ({pdf_exc})")

    meta = write_youtube_shorts_metadata(
        plan,
        video_path.with_name(f"{base_stem}_youtube_metadata.txt"),
        cheatsheet_url=cheatsheet_url,
    )
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

    def _initiate_resumable(token: str) -> requests.Response:
        return requests.post(
            "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Length": str(video_path.stat().st_size),
                "X-Upload-Content-Type": "video/mp4",
            },
            data=json.dumps(metadata_body),
            timeout=60,
        )

    init_resp = _initiate_resumable(yt_token)
    if init_resp.status_code == 401 and os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip():
        print("[youtube] Access token expired (401); auto-refreshing via YOUTUBE_REFRESH_TOKEN...")
        yt_token = refresh_youtube_access_token()
        init_resp = _initiate_resumable(yt_token)
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

    # Optional Step: Upload custom cover thumbnail via thumbnails.set API
    thumbnail_set = False
    if video_id and cover_path and cover_path.exists():
        try:
            with cover_path.open("rb") as img_fh:
                thumb_resp = requests.post(
                    f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}",
                    headers={"Authorization": f"Bearer {yt_token}", "Content-Type": "image/png"},
                    data=img_fh,
                    timeout=60,
                )
            if thumb_resp.status_code in {200, 201}:
                thumbnail_set = True
                print(f"[youtube] Custom thumbnail attached ({cover_path.name})")
            else:
                print(f"[youtube-note] Custom thumbnail API returned {thumb_resp.status_code} (Shorts use vertical frame or require youtube.force-ssl scope)")
        except Exception as th_exc:
            print(f"[youtube-note] Thumbnail attach skipped: {th_exc}")

    return {
        "video_id": video_id,
        "url": f"https://youtube.com/shorts/{video_id}",
        "cheatsheet_url": cheatsheet_url,
        "thumbnail_set": thumbnail_set,
    }
