#!/usr/bin/env python3
"""
Concept First Studio Dashboard
A local web interface to inspect generated technical reels/shorts, verify video frames,
listen to audio tracks, check pronunciations, and run local renders with zero auto-upload.
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_RUNS = ROOT / "output" / "runs"
OUTPUT_FINAL = ROOT / "output" / "final"
PORT = int(os.getenv("STUDIO_PORT", "8088"))

_active_process: subprocess.Popen | None = None
_process_logs: list[str] = []


def _extract_frames_for_video(video_path: Path, output_dir: Path) -> list[str]:
    """Extract 6 evenly spaced still frames from a video using ffmpeg."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not video_path.exists():
        return []

    # Get duration
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, check=True
        )
        total_dur = float(probe.stdout.strip())
    except Exception:
        total_dur = 45.0

    stills: list[str] = []
    # 6 checkpoints: 5%, 20%, 40%, 60%, 80%, 95%
    ratios = [0.05, 0.20, 0.40, 0.60, 0.80, 0.95]
    labels = ["01_hook", "02_problem", "03_core_model", "04_dryrun", "05_complexity", "06_outro"]
    for ratio, label in zip(ratios, labels):
        t = round(total_dur * ratio, 2)
        out_img = output_dir / f"frame_{label}_{int(t)}s.png"
        if not out_img.exists():
            subprocess.run(
                [ffmpeg, "-y", "-ss", str(t), "-i", str(video_path), "-vframes", "1", "-q:v", "2", str(out_img)],
                capture_output=True, check=False
            )
        if out_img.exists():
            stills.append(f"/media/frames/{output_dir.name}/{out_img.name}")
    return stills


def get_all_runs() -> list[dict]:
    runs = []
    if not OUTPUT_RUNS.exists():
        return []
    for run_dir in sorted(OUTPUT_RUNS.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        plan_path = run_dir / "final_plan.json"
        if not plan_path.exists():
            plan_path = run_dir / "plan_before_audio.json"
        topic = run_dir.name
        duration = 0
        beats_count = 0
        quality_score = None
        if plan_path.exists():
            try:
                data = json.loads(plan_path.read_text(encoding="utf-8"))
                topic = data.get("topic", topic)
                duration = data.get("duration_seconds", 0)
                beats_count = len(data.get("beats", []))
            except Exception:
                pass

        # Check matching final video
        video_files = list(OUTPUT_FINAL.glob(f"{run_dir.name}*.mp4")) if OUTPUT_FINAL.exists() else []
        pdf_files = list(OUTPUT_FINAL.glob(f"{run_dir.name}*.pdf")) if OUTPUT_FINAL.exists() else []
        cover_files = list(OUTPUT_FINAL.glob(f"{run_dir.name}*cover.png")) if OUTPUT_FINAL.exists() else []

        runs.append({
            "id": run_dir.name,
            "topic": topic,
            "duration": duration,
            "beats_count": beats_count,
            "has_video": len(video_files) > 0,
            "videos": [v.name for v in video_files],
            "covers": [c.name for c in cover_files],
            "pdfs": [p.name for p in pdf_files],
        })
    return runs


def get_run_details(run_id: str) -> dict | None:
    run_dir = OUTPUT_RUNS / run_id
    if not run_dir.exists():
        return None
    plan_path = run_dir / "final_plan.json"
    if not plan_path.exists():
        plan_path = run_dir / "plan_before_audio.json"
    plan_data = {}
    if plan_path.exists():
        try:
            plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    video_files = list(OUTPUT_FINAL.glob(f"{run_id}*.mp4")) if OUTPUT_FINAL.exists() else []
    cover_files = list(OUTPUT_FINAL.glob(f"{run_id}*cover.png")) if OUTPUT_FINAL.exists() else []
    pdf_files = list(OUTPUT_FINAL.glob(f"{run_id}*.pdf")) if OUTPUT_FINAL.exists() else []

    # Frame stills extraction
    frame_stills = []
    if video_files:
        frames_dir = ROOT / "output" / "frames" / run_id
        frame_stills = _extract_frames_for_video(video_files[0], frames_dir)

    # Audio files
    audio_files = []
    audio_dir = run_dir / "audio"
    if audio_dir.exists():
        for a in sorted(audio_dir.glob("*.mp3")):
            audio_files.append(f"/media/audio/{run_id}/{a.name}")

    return {
        "id": run_id,
        "plan": plan_data,
        "videos": [f"/media/final/{v.name}" for v in video_files],
        "covers": [f"/media/final/{c.name}" for c in cover_files],
        "pdfs": [f"/media/final/{p.name}" for p in pdf_files],
        "frame_stills": frame_stills,
        "audio_files": audio_files,
    }


class StudioHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.serve_dashboard()
            return
        elif path == "/api/runs":
            runs = get_all_runs()
            self.send_json({"runs": runs})
            return
        elif path.startswith("/api/run/"):
            run_id = path.replace("/api/run/", "").strip()
            details = get_run_details(run_id)
            if details:
                self.send_json(details)
            else:
                self.send_error(404, "Run not found")
            return
        elif path == "/api/logs":
            global _process_logs
            self.send_json({"logs": "\n".join(_process_logs[-100:])})
            return
        elif path.startswith("/media/"):
            self.serve_media(path)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}

        if path == "/api/generate":
            topic = str(data.get("topic", "")).strip()
            platform = str(data.get("platform", "both")).strip()
            script_only = bool(data.get("script_only", False))
            if not topic:
                self.send_json({"error": "Topic is required"}, status=400)
                return

            def _run_worker():
                global _active_process, _process_logs
                _process_logs.clear()
                cmd = [sys.executable, str(ROOT / "run.py"), "--topic", topic, "--platform", platform]
                if script_only:
                    cmd.append("--script-only")
                _process_logs.append(f"[studio] Starting: {' '.join(cmd)}")
                try:
                    proc = subprocess.Popen(
                        cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
                    )
                    _active_process = proc
                    for line in iter(proc.stdout.readline, ""):
                        _process_logs.append(line.rstrip())
                    proc.stdout.close()
                    proc.wait()
                    _process_logs.append(f"[studio] Finished with exit code {proc.returncode}")
                except Exception as exc:
                    _process_logs.append(f"[studio-error] {exc}")

            threading.Thread(target=_run_worker, daemon=True).start()
            self.send_json({"status": "started", "topic": topic})
            return

        elif path == "/api/publish-youtube":
            run_id = str(data.get("run_id", "")).strip()
            details = get_run_details(run_id)
            if not details or not details["videos"]:
                self.send_json({"error": "No video found for this run"}, status=400)
                return

            from publisher.social_publisher import upload_youtube_short
            video_name = Path(details["videos"][0]).name
            video_path = OUTPUT_FINAL / video_name
            try:
                info = upload_youtube_short(video_path, details["plan"])
                self.send_json({"status": "published", "url": info.get("url")})
            except Exception as exc:
                self.send_json({"error": str(exc)}, status=500)
            return

        self.send_error(404, "Unknown endpoint")

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_media(self, path: str):
        # /media/final/<file>
        # /media/audio/<run_id>/<file>
        # /media/frames/<run_id>/<file>
        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[1] == "final":
            target = OUTPUT_FINAL / parts[2]
        elif len(parts) >= 4 and parts[1] == "audio":
            target = OUTPUT_RUNS / parts[2] / "audio" / parts[3]
        elif len(parts) >= 4 and parts[1] == "frames":
            target = ROOT / "output" / "frames" / parts[2] / parts[3]
        else:
            self.send_error(404, "Media not found")
            return

        if not target.exists() or not target.is_file():
            self.send_error(404, f"File {target.name} not found")
            return

        mime, _ = mimetypes.guess_type(str(target))
        mime = mime or "application/octet-stream"
        file_size = target.stat().st_size

        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        with open(target, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def serve_dashboard(self):
        html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Concept First Studio — Verification Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0A0D12;
      --card-bg: #121721;
      --card-border: rgba(255, 255, 255, 0.08);
      --gold: #FF9F2A;
      --green: #3CEB8B;
      --blue: #58A6FF;
      --red: #FF4D4D;
      --text: #F7F8FA;
      --muted: #8B949E;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      padding: 18px 36px;
      background: #0E131C;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }
    .brand span { color: var(--gold); }
    .badge-safe {
      padding: 4px 12px;
      border-radius: 99px;
      background: rgba(60, 235, 139, 0.12);
      border: 1px solid var(--green);
      color: var(--green);
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 700;
    }
    main {
      flex: 1;
      display: grid;
      grid-template-columns: 320px 1fr;
      height: calc(100vh - 65px);
    }
    .sidebar {
      background: #0E131C;
      border-right: 1px solid var(--card-border);
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }
    .sidebar-header {
      padding: 16px 20px;
      font-size: 13px;
      font-weight: 800;
      color: var(--muted);
      letter-spacing: 1.5px;
      text-transform: uppercase;
      border-bottom: 1px solid var(--card-border);
    }
    .run-item {
      padding: 16px 20px;
      border-bottom: 1px solid var(--card-border);
      cursor: pointer;
      transition: background 0.15s ease;
    }
    .run-item:hover, .run-item.active {
      background: rgba(255, 159, 42, 0.08);
      border-left: 3px solid var(--gold);
    }
    .run-title { font-size: 15px; font-weight: 700; margin-bottom: 4px; color: #FFF; }
    .run-meta { font-size: 12px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }
    .content-area {
      overflow-y: auto;
      padding: 28px 36px;
      display: flex;
      flex-direction: column;
      gap: 28px;
    }
    .panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 24px;
    }
    .panel-header {
      font-size: 16px;
      font-weight: 800;
      margin-bottom: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .panel-header span { color: var(--gold); }
    .preview-grid {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 24px;
    }
    video {
      width: 100%;
      border-radius: 16px;
      background: #000;
      border: 1px solid rgba(255,255,255,0.1);
      box-shadow: 0 16px 50px rgba(0,0,0,0.8);
    }
    .frames-gallery {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-top: 14px;
    }
    .frame-card {
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid var(--card-border);
      background: #000;
      position: relative;
    }
    .frame-card img {
      width: 100%;
      height: auto;
      display: block;
    }
    .frame-label {
      position: absolute;
      bottom: 6px;
      left: 6px;
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(0,0,0,0.75);
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #FFF;
    }
    .beats-list {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .beat-card {
      padding: 16px 20px;
      border-radius: 14px;
      background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.06);
    }
    .beat-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
    }
    .beat-spoken {
      font-size: 15px;
      color: #FFF;
      line-height: 1.4;
      margin-bottom: 6px;
    }
    .beat-tts {
      font-size: 14px;
      color: var(--gold);
      line-height: 1.4;
      font-family: 'Inter', sans-serif;
    }
    .btn {
      padding: 10px 20px;
      border-radius: 12px;
      border: none;
      font-weight: 700;
      font-size: 14px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: opacity 0.15s;
    }
    .btn-gold { background: var(--gold); color: #000; }
    .btn-green { background: var(--green); color: #000; }
    .btn-outline { background: transparent; border: 1px solid var(--card-border); color: #FFF; }
    .btn:hover { opacity: 0.88; }
    .render-form {
      display: flex;
      gap: 12px;
      align-items: center;
    }
    input[type="text"] {
      flex: 1;
      padding: 12px 18px;
      border-radius: 12px;
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--card-border);
      color: #FFF;
      font-size: 14px;
    }
    input[type="text"]:focus { outline: 1px solid var(--gold); }
    .log-box {
      background: #06090E;
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 16px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: #A0AAB8;
      max-height: 220px;
      overflow-y: auto;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>⚡ Concept First</span> Studio Dashboard
    </div>
    <div style="display:flex; gap:16px; align-items:center;">
      <div class="badge-safe">🛡️ LOCAL SAFE MODE (AUTO-UPLOAD DISABLED)</div>
    </div>
  </header>
  <main>
    <div class="sidebar">
      <div class="sidebar-header">Recent Generation Runs</div>
      <div id="runsList">Loading runs...</div>
    </div>
    <div class="content-area">
      <!-- Quick Generator Bar -->
      <div class="panel">
        <div class="panel-header">Launch New Local Run <span>(Preview / Render)</span></div>
        <div class="render-form">
          <input type="text" id="topicInput" placeholder="Enter topic name (e.g. Valid Anagram, LRU Cache, Database Sharding)..." value="Valid Anagram">
          <button class="btn btn-outline" onclick="triggerRun(true)">Script Preview</button>
          <button class="btn btn-gold" onclick="triggerRun(false)">Render Locally</button>
        </div>
      </div>

      <!-- Live Terminal Output -->
      <div class="panel" id="logPanel" style="display:none;">
        <div class="panel-header">Pipeline Terminal Output <button class="btn btn-outline" style="padding:4px 10px; font-size:11px;" onclick="pollLogs()">Refresh</button></div>
        <div class="log-box" id="logBox">Waiting for output...</div>
      </div>

      <!-- Active Run Detail View -->
      <div id="activeRunContent" style="display:flex; flex-direction:column; gap:24px;">
        <div style="color:var(--muted); text-align:center; padding:60px 0;">Select a run from the left panel to inspect video frames and audio.</div>
      </div>
    </div>
  </main>

  <script>
    let currentRunId = null;
    let logTimer = null;

    async function loadRuns() {
      const res = await fetch('/api/runs');
      const data = await res.json();
      const list = document.getElementById('runsList');
      list.innerHTML = '';
      if (!data.runs.length) {
        list.innerHTML = '<div style="padding:20px; color:var(--muted);">No runs found yet.</div>';
        return;
      }
      data.runs.forEach((r, idx) => {
        const item = document.createElement('div');
        item.className = 'run-item' + (idx === 0 ? ' active' : '');
        item.innerHTML = `
          <div class="run-title">${r.topic}</div>
          <div class="run-meta">${r.id} · ${r.beats_count} beats · ${r.has_video ? '🎬 Rendered' : '📝 Plan'}</div>
        `;
        item.onclick = () => selectRun(r.id, item);
        list.appendChild(item);
      });
      if (data.runs.length > 0) {
        selectRun(data.runs[0].id, list.children[0]);
      }
    }

    async function selectRun(runId, elem) {
      currentRunId = runId;
      document.querySelectorAll('.run-item').forEach(e => e.classList.remove('active'));
      if (elem) elem.classList.add('active');

      const res = await fetch('/api/run/' + runId);
      const data = await res.json();
      renderRunDetails(data);
    }

    function renderRunDetails(data) {
      const container = document.getElementById('activeRunContent');
      const videoSrc = data.videos.length ? data.videos[0] : '';
      const coverSrc = data.covers.length ? data.covers[0] : '';
      const pdfSrc = data.pdfs.length ? data.pdfs[0] : '';
      const plan = data.plan || {};
      const beats = plan.beats || [];

      let framesHtml = '';
      if (data.frame_stills && data.frame_stills.length) {
        framesHtml = data.frame_stills.map((src, i) => `
          <div class="frame-card">
            <img src="${src}" alt="Frame ${i+1}" />
            <div class="frame-label">Checkpoint 0${i+1}</div>
          </div>
        `).join('');
      } else {
        framesHtml = '<div style="color:var(--muted); font-size:13px; grid-column:span 3;">No extracted frame stills available yet.</div>';
      }

      let beatsHtml = beats.map((b, i) => `
        <div class="beat-card">
          <div class="beat-header">
            <span style="color:var(--gold); font-weight:800;">BEAT 0${i+1} · ${b.id.toUpperCase()}</span>
            <span style="color:var(--blue);">${b.type} · ${b.duration_frames || 0} frames</span>
          </div>
          <div class="beat-spoken"><strong>Narration:</strong> "${b.spoken_text}"</div>
          <div class="beat-tts"><strong>Devanagari TTS:</strong> ${b.tts_text || '—'}</div>
        </div>
      `).join('');

      container.innerHTML = `
        <div class="preview-grid">
          <div>
            ${videoSrc ? `
              <video src="${videoSrc}" controls></video>
              <div style="margin-top:16px; display:flex; gap:10px;">
                <a href="${videoSrc}" download class="btn btn-outline" style="flex:1; justify-content:center;">Download MP4</a>
                ${pdfSrc ? `<a href="${pdfSrc}" target="_blank" class="btn btn-outline" style="flex:1; justify-content:center;">Cheat Sheet PDF</a>` : ''}
              </div>
            ` : `<div style="padding:40px; border-radius:16px; background:#000; border:1px solid var(--card-border); text-align:center; color:var(--muted);">No MP4 rendered for this plan yet.</div>`}
          </div>
          <div style="display:flex; flex-direction:column; gap:20px;">
            <div class="panel">
              <div class="panel-header">Visual Frame Verification <span>(6 Video Timelines)</span></div>
              <div class="frames-gallery">${framesHtml}</div>
            </div>
            <div class="panel">
              <div class="panel-header">Manual Publishing Gate <span>(Only On Your Click)</span></div>
              <p style="font-size:13px; color:var(--muted); margin-bottom:14px;">Once you verify that audio pronunciation and all visual frames are 100% correct, you can publish to YouTube Shorts with a single click:</p>
              <button class="btn btn-green" onclick="publishYouTube('${data.id}')">Publish to YouTube Shorts</button>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">Story & Pronunciation Verification <span>(${beats.length} Beats)</span></div>
          <div class="beats-list">${beatsHtml}</div>
        </div>
      `;
    }

    async function triggerRun(scriptOnly) {
      const topic = document.getElementById('topicInput').value.trim();
      if (!topic) return alert('Enter a topic');
      document.getElementById('logPanel').style.display = 'block';
      document.getElementById('logBox').innerText = 'Starting pipeline...';
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, platform: 'both', script_only: scriptOnly })
      });
      if (logTimer) clearInterval(logTimer);
      logTimer = setInterval(pollLogs, 1500);
    }

    async function pollLogs() {
      const res = await fetch('/api/logs');
      const data = await res.json();
      const box = document.getElementById('logBox');
      box.innerText = data.logs || 'Running...';
      box.scrollTop = box.scrollHeight;
      if (data.logs.includes('Finished with exit code') || data.logs.includes('[done]')) {
        clearInterval(logTimer);
        loadRuns();
      }
    }

    async function publishYouTube(runId) {
      if (!confirm('Are you sure you want to upload this Short to YouTube (@ConceptFirstWithMohit)?')) return;
      alert('Uploading Short to YouTube... Check terminal/logs.');
      const res = await fetch('/api/publish-youtube', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: runId })
      });
      const data = await res.json();
      if (data.url) {
        alert('Short published successfully! URL: ' + data.url);
      } else {
        alert('Upload response: ' + (data.error || JSON.stringify(data)));
      }
    }

    window.onload = loadRuns;
  </script>
</body>
</html>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def run_server():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), StudioHandler)
    print(f"[studio] Concept First Studio Dashboard running at: http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[studio] Dashboard stopped.")


if __name__ == "__main__":
    run_server()
