from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_engine.post_inspector import inspect_and_optimize_video
from run import render_video

RUNS_TO_RERENDER = [
    "20261110_160748_rag_architecture",
    "20261110_162350_consistent_hashing",
    "20261110_164042_two_sum",
    "20261110_153901_horizontal_scaling",
]


def main() -> int:
    public_audio = ROOT / "my-video" / "public" / "audio"
    public_audio.mkdir(parents=True, exist_ok=True)
    render_plan_path = ROOT / "my-video" / "src" / "data" / "plan.json"

    for run_name in RUNS_TO_RERENDER:
        run_dir = ROOT / "output" / "runs" / run_name
        plan_file = run_dir / "final_plan.json"
        audio_dir = run_dir / "audio"
        if not plan_file.exists() or not audio_dir.exists():
            print(f"[skip] Missing plan or audio for {run_name}")
            continue

        print(f"\n=== Re-rendering {run_name} with CONCEPT FIRST (@conceptfirstwithmohit) branding ===")
        for mp3 in audio_dir.glob("*.mp3"):
            shutil.copy2(mp3, public_audio / mp3.name)
        shutil.copy2(plan_file, render_plan_path)

        out_mp4 = ROOT / "output" / "final" / f"{run_name}.mp4"
        render_video(ROOT, out_mp4)
        report = inspect_and_optimize_video(out_mp4, expected_width=1080, expected_height=1920)
        print(f"[done] Updated {out_mp4} ({report.duration_seconds:.1f}s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
