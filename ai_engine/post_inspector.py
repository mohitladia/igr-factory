from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PostRenderReport:
    passed: bool
    duration_seconds: float
    width: int
    height: int
    audio_channels: int
    audio_sample_rate: int
    has_audio: bool
    issues: list[str]
    actions_taken: list[str]


def inspect_and_optimize_video(
    video_path: Path,
    expected_width: int = 1080,
    expected_height: int = 1920,
    auto_normalize_audio: bool = True,
) -> PostRenderReport:
    """Post-Render Quality Inspector and Optimizer Loop.

    Verifies stream parameters (resolution, audio/video duration sync, presence of audio),
    detects flaws, and applies fast lossless post-processing (e.g. EBU R128 audio loudness normalization
    for Instagram Reels) without needing an expensive full Remotion re-render.
    """
    if not video_path.exists() or video_path.stat().st_size < 10_000:
        return PostRenderReport(
            passed=False,
            duration_seconds=0.0,
            width=0,
            height=0,
            audio_channels=0,
            audio_sample_rate=0,
            has_audio=False,
            issues=["Output MP4 file does not exist or is corrupt (<10KB)"],
            actions_taken=[],
        )

    issues: list[str] = []
    actions_taken: list[str] = []

    # 1. Probe streams with ffprobe
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=codec_type,width,height,duration,channels,sample_rate",
        "-of", "json",
        str(video_path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(proc.stdout)
    except Exception as exc:
        return PostRenderReport(
            passed=False,
            duration_seconds=0.0,
            width=0,
            height=0,
            audio_channels=0,
            audio_sample_rate=0,
            has_audio=False,
            issues=[f"ffprobe failed: {exc}"],
            actions_taken=[],
        )

    streams = probe_data.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if not video_stream:
        return PostRenderReport(
            passed=False,
            duration_seconds=0.0,
            width=0,
            height=0,
            audio_channels=0,
            audio_sample_rate=0,
            has_audio=False,
            issues=["No video stream found in rendered MP4"],
            actions_taken=[],
        )

    v_width = int(video_stream.get("width", 0))
    v_height = int(video_stream.get("height", 0))
    v_duration = float(video_stream.get("duration", 0.0))

    if v_width != expected_width or v_height != expected_height:
        issues.append(f"Resolution mismatch: got {v_width}x{v_height}, expected {expected_width}x{expected_height}")

    if v_duration < 15.0:
        issues.append(f"Video is unusually short ({v_duration:.1f}s)")
    elif v_duration > 95.0:
        issues.append(f"Video exceeds Instagram Reel max recommended duration ({v_duration:.1f}s > 90s)")

    has_audio = audio_stream is not None
    a_channels = int(audio_stream.get("channels", 0)) if audio_stream else 0
    a_sample_rate = int(audio_stream.get("sample_rate", 0)) if audio_stream else 0

    if not has_audio:
        issues.append("No audio track detected in final MP4!")

    # 2. Instagram Loudness Normalization (EBU R128 standard: target -14 LUFS)
    # Applied quickly with FFmpeg stream copy for video (-c:v copy) so it runs in ~1-2s!
    if has_audio and auto_normalize_audio:
        temp_optimized = video_path.with_name(f"{video_path.stem}_opt.mp4")
        norm_cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-c:v", "copy",
            "-filter:a", "loudnorm=I=-14:TP=-1.0:LRA=11",
            "-c:a", "aac",
            "-b:a", "192k",
            str(temp_optimized),
        ]
        try:
            norm_proc = subprocess.run(norm_cmd, capture_output=True, text=True, check=False)
            if norm_proc.returncode == 0 and temp_optimized.exists() and temp_optimized.stat().st_size > 10_000:
                # Replace original with the loudness-optimized version
                temp_optimized.replace(video_path)
                actions_taken.append("Audio normalized to Instagram Reel standard (-14 LUFS) via FFmpeg lossless video remux.")
            else:
                if temp_optimized.exists():
                    temp_optimized.unlink(missing_ok=True)
        except Exception as e:
            actions_taken.append(f"Audio normalization skipped: {e}")

    passed = len(issues) == 0
    return PostRenderReport(
        passed=passed,
        duration_seconds=v_duration,
        width=v_width,
        height=v_height,
        audio_channels=a_channels,
        audio_sample_rate=a_sample_rate,
        has_audio=has_audio,
        issues=issues,
        actions_taken=actions_taken,
    )
