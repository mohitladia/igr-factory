from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from ai_engine.critic import evaluate_plan_quality
from ai_engine.demo_plan import build_demo_plan
from ai_engine.plan_generator import generate_plan, validate_and_normalize
from ai_engine.post_inspector import inspect_and_optimize_video
from audio_engine.voice_generator import generate_beat_audio
from publisher.social_publisher import (
    auto_dm_keyword_comments,
    publish_instagram_reel,
    upload_youtube_short,
    write_instagram_metadata,
    write_youtube_shorts_metadata,
)
from renderer.timeline import write_render_plan
from visual_engine.build_assets import build_optional_assets

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a universal, JSON-driven technical Instagram Reel & YouTube Short.")
    parser.add_argument("--topic", type=str, help="Topic to explain, e.g. Apache Kafka")
    parser.add_argument("--duration", type=int, default=None, help="Target duration in seconds (default from .env or 70)")
    parser.add_argument("--platform", type=str, choices=["reel", "shorts", "both"], default="reel", help="Target platform: reel (Instagram), shorts (YouTube Shorts), or both")
    parser.add_argument("--publish-instagram", action="store_true", help="Auto-publish rendered Reel to Instagram via Meta Graph API (mcpware/instagram-mcp flow)")
    parser.add_argument("--auto-dm", action="store_true", help="Scan recent Reel comments for trigger keyword and send PDF Cheat Sheet via Instagram DM")
    parser.add_argument("--upload-youtube", action="store_true", help="Auto-upload rendered Short to YouTube via YouTube Data API v3")
    parser.add_argument("--demo", action="store_true", help="Use topic-aware sample plan without the LLM API")
    parser.add_argument("--plan-only", action="store_true", help="Generate plan/audio/assets but do not render MP4")
    parser.add_argument("--skip-images", action="store_true", help="Skip optional hosted AI image generation")
    return parser.parse_args()


def run_command(command: list[str], cwd: Path) -> None:
    print("\n[render] " + " ".join(command))
    # Windows .cmd launchers (npx.cmd) need cmd.exe; this also avoids the earlier WinError 2 issue.
    if os.name == "nt":
        process = subprocess.run(subprocess.list2cmdline(command), cwd=str(cwd), shell=True, check=False)
    else:
        process = subprocess.run(command, cwd=str(cwd), check=False)
    if process.returncode != 0:
        raise RuntimeError(f"Remotion render failed with exit code {process.returncode}")


def render_video(root: Path, output_path: Path) -> None:
    my_video = root / "my-video"
    if not (my_video / "node_modules").exists():
        raise RuntimeError("Remotion dependencies are not installed. Run setup_windows.bat first.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    executable = "npx.cmd" if os.name == "nt" else "npx"
    command = [executable, "remotion", "render", "src/index.ts", "Reel", str(output_path), "--codec", os.getenv("REMOTION_CODEC", "h264")]
    run_command(command, my_video)
    if not output_path.exists() or output_path.stat().st_size < 50_000:
        raise RuntimeError("Render command completed but output MP4 is missing or unexpectedly small")


def main() -> int:
    load_dotenv(ROOT / ".env")
    args = parse_args()
    topic = (args.topic or input("Enter Reel topic: ")).strip()
    if not topic:
        print("[error] Topic cannot be empty.")
        return 2

    duration = args.duration or int(os.getenv("TARGET_DURATION_SECONDS", "70"))
    fps = int(os.getenv("VIDEO_FPS", "30"))
    width = int(os.getenv("VIDEO_WIDTH", "1080"))
    height = int(os.getenv("VIDEO_HEIGHT", "1920"))
    voice = os.getenv("TTS_VOICE", "hi-IN-MadhurNeural")
    rate = os.getenv("TTS_RATE", "+8%")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in topic)[:36].strip("_") or "reel"
    run_dir = ROOT / "output" / "runs" / f"{stamp}_{slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 64)
    print("INSTAGRAM REEL FACTORY — UNIVERSAL BEAT-DRIVEN PIPELINE")
    print(f"Topic: {topic}\nTarget: {duration}s | {width}x{height} @ {fps}fps")
    print("=" * 64)

    try:
        print("\n[1/5] Generating story and visual beats...")
        if args.demo:
            raw_plan = build_demo_plan(topic, duration)
            plan = validate_and_normalize(raw_plan, topic)
        else:
            try:
                raw_plan = generate_plan(topic, duration)
                plan = validate_and_normalize(raw_plan, topic)
            except Exception as llm_exc:
                print(f"[plan-fallback] LLM response incomplete or unavailable ({llm_exc}); using high-retention topic storyboard generator.")
                raw_plan = build_demo_plan(topic, duration)
                plan = validate_and_normalize(raw_plan, topic)
        print(f"[topic-lock] family={plan.get('topic_family')} format={plan.get('teaching_format')}")
        print(f"[topic-lock] validated exact topic: {plan['topic']}")

        # Pre-render quality gate evaluation
        report = evaluate_plan_quality(plan)
        print(f"[critic] Story Quality Score: {report.score}/10 (Hook: {report.hook_score} | Intuition: {report.intuition_score} | Pacing: {report.pacing_score} | CTA: {report.cta_score})")
        if report.feedback:
            for tip in report.feedback:
                print(f"[critic-tip] {tip}")
        if not report.passed:
            print("[critic-warn] Quality gate flagged potential engagement issues, proceeding with best effort.")
        plan["fps"] = fps
        plan["width"] = width
        plan["height"] = height
        (run_dir / "plan_before_audio.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[plan] {len(plan['beats'])} beats generated")

        print("\n[2/5] Generating voice and word timings...")
        plan = generate_beat_audio(plan, ROOT, run_dir, voice, rate, fps)
        print(f"[audio] total timeline: {plan['duration_seconds']}s")

        print("\n[3/5] Generating optional supporting visuals...")
        if args.skip_images:
            print("[visuals] skipped by command line")
        else:
            build_optional_assets(plan, ROOT, run_dir)

        print("\n[4/5] Writing renderer plan...")
        platforms_to_render = ["reel", "shorts"] if args.platform == "both" else [args.platform]
        plan["platform"] = platforms_to_render[0]
        render_plan_path = ROOT / "my-video" / "src" / "data" / "plan.json"
        write_render_plan(plan, render_plan_path)
        (run_dir / "final_plan.json").write_text(render_plan_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[plan] {render_plan_path}")

        ig_meta_path = ROOT / "output" / "final" / f"{stamp}_{slug}_instagram_metadata.txt"
        ig_caption = write_instagram_metadata(plan, ig_meta_path)
        write_instagram_metadata(plan, run_dir / "instagram_metadata.txt")
        print(f"[instagram-meta] Generated Caption, Hashtags & DM Trigger: {ig_meta_path}")

        yt_meta_path = ROOT / "output" / "final" / f"{stamp}_{slug}_youtube_metadata.txt"
        write_youtube_shorts_metadata(plan, yt_meta_path)
        write_youtube_shorts_metadata(plan, run_dir / "youtube_metadata.txt")
        print(f"[youtube-meta] Generated ready-to-paste Title, Description, Pinned Comment & Tags: {yt_meta_path}")

        if args.plan_only:
            print("\n[done] Plan and audio are ready. Rendering skipped (--plan-only).")
            print(f"Run folder: {run_dir}")
            return 0

        rendered_outputs: list[Path] = []
        for plat in platforms_to_render:
            plan["platform"] = plat
            write_render_plan(plan, render_plan_path)
            suffix = "_shorts" if plat == "shorts" else ("" if args.platform == "reel" else "_reel")
            output_path = ROOT / "output" / "final" / f"{stamp}_{slug}{suffix}.mp4"
            print(f"\n[5/6] Rendering vertical MP4 ({plat.upper()}) with Remotion...")
            render_video(ROOT, output_path)

            print(f"\n[6/6] Inspecting video quality and optimizing audio ({plat.upper()})...")
            post_report = inspect_and_optimize_video(output_path, expected_width=width, expected_height=height)
            for act in post_report.actions_taken:
                print(f"[post-opt] {act}")
            if post_report.issues:
                for issue in post_report.issues:
                    print(f"[post-warn] {issue}")
            else:
                print(f"[post-opt] Video passed all quality checks ({post_report.width}x{post_report.height}, {post_report.duration_seconds:.1f}s, stereo {post_report.audio_sample_rate}Hz).")
            rendered_outputs.append(output_path)
            if plat == "reel" and args.publish_instagram:
                pub_info = publish_instagram_reel(output_path, ig_caption)
                print(f"[instagram-published] Media ID: {pub_info.get('media_id')}")
            if plat == "shorts" and args.upload_youtube:
                yt_info = upload_youtube_short(output_path, plan)
                print(f"[youtube-uploaded] URL: {yt_info.get('url')}")

        if args.auto_dm:
            kw = "".join(ch for ch in topic if ch.isalnum()).upper()[:12] or "NOTES"
            dm_url = os.getenv("CHEATSHEET_DEFAULT_URL", "https://github.com/mohitladia/igr-factory")
            dm_stats = auto_dm_keyword_comments(kw, dm_url)
            print(f"[instagram-dm] Checked {dm_stats.get('checked')} comments, sent {dm_stats.get('dms_sent')} PDF DMs.")

        print("\n" + "=" * 64)
        print("GENERATION COMPLETED SUCCESSFULLY")
        for out_file in rendered_outputs:
            print(f"Video: {out_file}")
        if "shorts" in platforms_to_render:
            print(f"YouTube SEO Metadata: {ROOT / 'output' / 'final' / f'{stamp}_{slug}_youtube_metadata.txt'}")
        print(f"Plan:  {run_dir / 'final_plan.json'}")
        print("=" * 64)
        return 0
    except KeyboardInterrupt:
        print("\n[stopped] User cancelled the pipeline.")
        return 130
    except Exception as exc:
        print(f"\n[error] {exc}")
        print(f"[debug] Check run files in: {run_dir}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
