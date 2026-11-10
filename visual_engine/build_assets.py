from __future__ import annotations

import hashlib
import os
import re
import shutil
from pathlib import Path
from typing import Any

from visual_engine.replicate_image_provider import ReplicateImageProvider


def build_optional_assets(plan: dict[str, Any], root: Path, run_dir: Path) -> None:
    enabled = os.getenv("ENABLE_AI_IMAGES", "false").strip().lower() in {"1", "true", "yes"}
    token = os.getenv("REPLICATE_API_TOKEN", "")
    if not enabled or not token:
        print("[visuals] AI image generation disabled; Remotion visuals will be used.")
        return
    max_images = max(0, int(os.getenv("MAX_AI_IMAGES_PER_REEL", "4")))
    provider = ReplicateImageProvider()
    asset_dir = run_dir / "assets"
    public_dir = root / "my-video" / "public" / "assets"
    cache_dir = root / "output" / "asset_cache"
    asset_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    generated = 0
    for beat in plan["beats"]:
        prompt = beat.get("asset_prompt")
        if not prompt or generated >= max_images:
            continue
        cache_key = hashlib.sha256((provider.model + "|" + prompt).encode("utf-8")).hexdigest()[:24]
        filename = re.sub(r"[^a-zA-Z0-9_-]+", "_", beat["id"])[:40] + "_" + cache_key[:8] + ".webp"
        cached_path = cache_dir / f"{cache_key}.webp"
        local_path = asset_dir / filename
        public_path = public_dir / filename
        try:
            if cached_path.exists() and cached_path.stat().st_size > 10_000:
                shutil.copy2(cached_path, local_path)
                print(f"[visuals] cache hit for {beat['id']}")
            else:
                provider.generate(prompt, local_path)
                shutil.copy2(local_path, cached_path)
            shutil.copy2(local_path, public_path)
            beat["asset_file"] = f"assets/{filename}"
            generated += 1
        except Exception as exc:  # optional stage must never block deterministic render
            print(f"[visuals] warning: could not generate image for {beat['id']}: {exc}")
    print(f"[visuals] prepared {generated} supporting image(s)")
