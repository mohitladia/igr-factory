from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


class ReplicateImageProvider:
    """Optional hosted image adapter. Uses FLUX Schnell via Replicate HTTP API."""

    def __init__(self, token: str | None = None, model: str | None = None) -> None:
        self.token = token or os.getenv("REPLICATE_API_TOKEN", "")
        self.model = model or os.getenv("REPLICATE_MODEL", "black-forest-labs/flux-schnell")
        if not self.token:
            raise RuntimeError("REPLICATE_API_TOKEN is not configured")

    def generate(self, prompt: str, destination: Path, timeout_seconds: int = 240) -> Path:
        owner, name = self.model.split("/", 1)
        endpoint = f"https://api.replicate.com/v1/models/{owner}/{name}/predictions"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Prefer": "wait=60",
        }
        payload: dict[str, Any] = {
            "input": {
                "prompt": prompt + ". Vertical 9:16 composition, no text, no logos, clean premium technical art.",
                "go_fast": True,
                "num_outputs": 1,
                "aspect_ratio": "9:16",
                "output_format": "webp",
                "output_quality": 85,
            }
        }
        response = requests.post(endpoint, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        prediction = response.json()
        deadline = time.time() + timeout_seconds
        while prediction.get("status") not in {"succeeded", "failed", "canceled"}:
            if time.time() >= deadline:
                raise TimeoutError("Image generation timed out")
            poll_url = prediction.get("urls", {}).get("get")
            if not poll_url:
                raise RuntimeError("Replicate response did not include a polling URL")
            time.sleep(2)
            poll = requests.get(poll_url, headers=headers, timeout=30)
            poll.raise_for_status()
            prediction = poll.json()
        if prediction.get("status") != "succeeded":
            raise RuntimeError(f"Image generation {prediction.get('status')}: {prediction.get('error')}")
        outputs = prediction.get("output") or []
        if not outputs:
            raise RuntimeError("Image provider returned no output URLs")
        image_url = outputs[0] if isinstance(outputs[0], str) else outputs[0].get("url")
        if not image_url or urlparse(image_url).scheme != "https":
            raise RuntimeError("Image provider returned an invalid image URL")
        image_response = requests.get(image_url, timeout=90)
        image_response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(image_response.content)
        return destination
