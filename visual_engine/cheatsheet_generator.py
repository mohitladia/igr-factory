from __future__ import annotations

import base64
import html
import os
import subprocess
from pathlib import Path
from typing import Any


def _find_browser_executable() -> str | None:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _get_logo_data_uri(root: Path) -> str:
    logo_candidates = [
        root / "my-video" / "public" / "branding" / "channel_avatar.jpg",
        root / "output" / "branding" / "channel_avatar_1080.jpg",
    ]
    for p in logo_candidates:
        if p.exists():
            encoded = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:image/jpeg;base64,{encoded}"
    return ""


def _build_cheatsheet_html(plan: dict[str, Any], logo_uri: str) -> str:
    topic = html.escape(str(plan.get("topic", "System Design")))
    family = html.escape(str(plan.get("topic_family", "SYSTEM DESIGN")).replace("_", " ").upper())
    beats = plan.get("beats", [])
    hook_text = html.escape(str(beats[0].get("spoken_text", f"{topic} Explained from First Principles"))) if beats else ""

    # Extract problem vs solution from beats
    problem_beat = next((b for b in beats if b.get("id") in {"problem", "baseline", "vertical_limits"} or b.get("type") == "comparison"), beats[1] if len(beats) > 1 else {})
    solution_beat = next((b for b in beats[2:] if b.get("id") not in {"summary"}), beats[2] if len(beats) > 2 else {})

    prob_title = html.escape(str(problem_beat.get("title", "Naive / Bottleneck Approach")))
    prob_desc = html.escape(str(problem_beat.get("spoken_text", "High latency, single point of failure, or expensive O(n²) bottleneck under production load.")))
    prob_metric = html.escape(str(problem_beat.get("metric") or "HIGH LATENCY / BOTTLENECK"))

    sol_title = html.escape(str(solution_beat.get("title", "Production Architecture")))
    sol_desc = html.escape(str(solution_beat.get("spoken_text", "Low-latency indexed pipeline with horizontal scalability and zero bottleneck.")))
    sol_metric = html.escape(str(solution_beat.get("metric") or "OPTIMIZED PRODUCTION FLOW"))

    # Build step cards for middle beats
    step_cards_html = []
    for idx, b in enumerate(beats[1:-1], start=1):
        b_title = html.escape(str(b.get("title", f"Stage {idx}")))
        b_metric = html.escape(str(b.get("metric") or f"STEP 0{idx}"))
        b_speech = html.escape(str(b.get("spoken_text", "")))
        nodes = b.get("nodes") or []
        pills = "".join(
            f'<span class="node-pill">{html.escape(str(n.get("label", "")))}'
            + (f' <small>({html.escape(str(n.get("detail", "")))})</small>' if n.get("detail") else "")
            + "</span>"
            for n in nodes[:4]
        )
        step_cards_html.append(
            f"""
            <div class="step-card">
              <div class="step-num">0{idx}</div>
              <div class="step-body">
                <div class="step-header">
                  <span class="step-title">{b_title}</span>
                  <span class="step-badge">{b_metric}</span>
                </div>
                <div class="step-desc">{b_speech}</div>
                {f'<div class="node-row">{pills}</div>' if pills else ''}
              </div>
            </div>
            """
        )

    logo_img = f'<img src="{logo_uri}" class="brand-logo" />' if logo_uri else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,700;1,9..144,800&family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@600;700;800&display=swap');
  @page {{
    size: A4 portrait;
    margin: 0;
  }}
  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  html, body {{
    margin: 0;
    padding: 0;
    width: 210mm;
    height: 297mm;
    background: #07090E;
    color: #F5F7FA;
    font-family: 'Inter', sans-serif;
    overflow: hidden;
  }}
  .page {{
    width: 210mm;
    height: 297mm;
    padding: 12mm 14mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background:
      radial-gradient(circle at 85% 12%, rgba(255, 159, 42, 0.12), transparent 40%),
      radial-gradient(circle at 15% 88%, rgba(46, 204, 113, 0.10), transparent 40%),
      #07090E;
  }}
  .top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 10px;
    border-bottom: 1.5px solid rgba(255,255,255,0.12);
  }}
  .brand-left {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .brand-logo {{
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: 2px solid #2ECC71;
  }}
  .brand-name {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #FFFFFF;
  }}
  .brand-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #2ECC71;
  }}
  .category-pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 800;
    padding: 6px 14px;
    border-radius: 999px;
    background: rgba(255, 159, 42, 0.14);
    border: 1.5px solid #FF9F2A;
    color: #FF9F2A;
    letter-spacing: 1.5px;
  }}
  .hero {{
    margin-top: 10px;
    padding: 16px 20px;
    border-radius: 16px;
    background: rgba(18, 22, 31, 0.92);
    border: 1.5px solid rgba(255, 159, 42, 0.45);
  }}
  .hero-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #FF9F2A;
    letter-spacing: 2px;
    text-transform: uppercase;
  }}
  .hero-title {{
    font-family: 'Fraunces', serif;
    font-style: italic;
    font-size: 36px;
    font-weight: 800;
    color: #FFFFFF;
    margin: 4px 0 8px 0;
  }}
  .hero-hook {{
    font-size: 13.5px;
    color: #C9D1D9;
    line-height: 1.45;
  }}
  .vs-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 12px;
  }}
  .vs-card {{
    padding: 14px 16px;
    border-radius: 14px;
    background: rgba(16, 20, 28, 0.95);
  }}
  .vs-bad {{
    border: 1.5px solid rgba(255, 77, 77, 0.65);
  }}
  .vs-good {{
    border: 1.5px solid rgba(46, 204, 113, 0.75);
  }}
  .vs-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 99px;
    display: inline-block;
    margin-bottom: 6px;
  }}
  .vs-bad .vs-tag {{
    background: rgba(255, 77, 77, 0.15);
    color: #FF5555;
  }}
  .vs-good .vs-tag {{
    background: rgba(46, 204, 113, 0.15);
    color: #2ECC71;
  }}
  .vs-title {{
    font-size: 15px;
    font-weight: 800;
    margin-bottom: 4px;
  }}
  .vs-desc {{
    font-size: 12px;
    color: #B0B8C4;
    line-height: 1.4;
  }}
  .section-heading {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #FF9F2A;
    margin: 14px 0 8px 0;
    text-transform: uppercase;
  }}
  .steps-list {{
    display: flex;
    flex-direction: column;
    gap: 9px;
  }}
  .step-card {{
    display: flex;
    gap: 12px;
    padding: 11px 14px;
    border-radius: 12px;
    background: rgba(18, 22, 30, 0.92);
    border: 1px solid rgba(255,255,255,0.10);
    align-items: flex-start;
  }}
  .step-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    font-weight: 800;
    color: #FF9F2A;
    background: rgba(255, 159, 42, 0.12);
    border: 1px solid rgba(255, 159, 42, 0.4);
    border-radius: 8px;
    padding: 6px 9px;
    min-width: 38px;
    text-align: center;
  }}
  .step-body {{
    flex: 1;
  }}
  .step-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }}
  .step-title {{
    font-size: 14px;
    font-weight: 800;
    color: #FFFFFF;
  }}
  .step-badge {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    color: #58A6FF;
    background: rgba(88, 166, 255, 0.12);
    border: 1px solid rgba(88, 166, 255, 0.4);
    padding: 2px 8px;
    border-radius: 99px;
  }}
  .step-desc {{
    font-size: 11.8px;
    color: #C9D1D9;
    line-height: 1.4;
  }}
  .node-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 6px;
  }}
  .node-pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.14);
    color: #E6EDF3;
    padding: 3px 8px;
    border-radius: 6px;
  }}
  .node-pill small {{
    color: #2ECC71;
  }}
  .footer {{
    margin-top: 12px;
    padding: 12px 16px;
    border-radius: 12px;
    background: rgba(46, 204, 113, 0.08);
    border: 1.5px solid rgba(46, 204, 113, 0.4);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .quote {{
    font-size: 12.5px;
    font-weight: 700;
    color: #2ECC71;
  }}
  .socials {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #FFFFFF;
    font-weight: 700;
  }}
</style>
</head>
<body>
  <div class="page">
    <div>
      <div class="top-bar">
        <div class="brand-left">
          {logo_img}
          <div>
            <div class="brand-name">CONCEPT FIRST WITH MOHIT</div>
            <div class="brand-sub">@conceptfirstwithmohit · First Principles Engineering</div>
          </div>
        </div>
        <div class="category-pill">{family} · PDF CHEAT SHEET</div>
      </div>

      <div class="hero">
        <div class="hero-label">● 60-SECOND INTERVIEW REVISION NOTES</div>
        <div class="hero-title">{topic}</div>
        <div class="hero-hook">{hook_text}</div>
      </div>

      <div class="vs-grid">
        <div class="vs-card vs-bad">
          <span class="vs-tag">✕ NAIVE TRAP · {prob_metric}</span>
          <div class="vs-title">{prob_title}</div>
          <div class="vs-desc">{prob_desc}</div>
        </div>
        <div class="vs-card vs-good">
          <span class="vs-tag">✔ PRODUCTION FIX · {sol_metric}</span>
          <div class="vs-title">{sol_title}</div>
          <div class="vs-desc">{sol_desc}</div>
        </div>
      </div>

      <div class="section-heading">⚡ Step-by-Step Production Architecture & Interview Walkthrough</div>
      <div class="steps-list">
        {"".join(step_cards_html)}
      </div>
    </div>

    <div class="footer">
      <div class="quote">💡 "Technology yaad rakhne se nahi, sochne se aati hai."</div>
      <div class="socials">YouTube & Instagram: @ConceptFirstWithMohit</div>
    </div>
  </div>
</body>
</html>
"""


def _build_cover_html(plan: dict[str, Any], logo_uri: str) -> str:
    topic = html.escape(str(plan.get("topic", "System Design")))
    family = html.escape(str(plan.get("topic_family", "SYSTEM DESIGN")).replace("_", " ").upper())
    beats = plan.get("beats", [])

    # Collect 3 key badges for the center 1:1 grid safe-zone
    pills = []
    for b in beats[1:4]:
        m = b.get("metric") or b.get("title")
        if m:
            pills.append(html.escape(str(m)))
    if not pills:
        pills = ["BOTTLENECK ✕", "ARCHITECTURE", "PRODUCTION ✔"]

    pills_html = "".join(
        f'<div class="pill pill-{i}">{p}</div>' for i, p in enumerate(pills[:3])
    )
    logo_img = f'<img src="{logo_uri}" class="logo" />' if logo_uri else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,800;1,9..144,900&family=Inter:wght@600;800;900&family=JetBrains+Mono:wght@700;800&display=swap');
  * {{
    box-sizing: border-box;
  }}
  html, body {{
    margin: 0;
    padding: 0;
    width: 1080px;
    height: 1920px;
    background: #07090E;
    color: #FFFFFF;
    font-family: 'Inter', sans-serif;
    overflow: hidden;
  }}
  .canvas {{
    width: 1080px;
    height: 1920px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background:
      radial-gradient(circle at 50% 42%, rgba(255, 159, 42, 0.22), transparent 48%),
      radial-gradient(circle at 50% 65%, rgba(46, 204, 113, 0.16), transparent 45%),
      linear-gradient(180deg, #05070B 0%, #0B101B 50%, #05070B 100%);
    position: relative;
  }}
  /* Centered 1080x1080 Square Safe Zone for Instagram Profile Grid */
  .safe-square {{
    width: 940px;
    height: 940px;
    border-radius: 44px;
    background: rgba(14, 18, 26, 0.94);
    border: 3px solid rgba(255, 159, 42, 0.65);
    box-shadow: 0 30px 100px rgba(0,0,0,0.85), 0 0 80px rgba(255, 159, 42, 0.18);
    padding: 64px 58px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    text-align: center;
  }}
  .top-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 3px;
    color: #FF9F2A;
    background: rgba(255, 159, 42, 0.14);
    border: 2px solid #FF9F2A;
    padding: 12px 32px;
    border-radius: 999px;
  }}
  .title {{
    font-family: 'Fraunces', serif;
    font-style: italic;
    font-size: 108px;
    font-weight: 900;
    line-height: 1.04;
    color: #FFFFFF;
    text-shadow: 0 8px 40px rgba(255, 159, 42, 0.35);
    margin: 10px 0;
  }}
  .subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 36px;
    font-weight: 800;
    color: #2ECC71;
    letter-spacing: 0.5px;
  }}
  .pills {{
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    justify-content: center;
    margin: 16px 0;
  }}
  .pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 23px;
    font-weight: 800;
    padding: 14px 26px;
    border-radius: 18px;
  }}
  .pill-0 {{
    background: rgba(255, 77, 77, 0.16);
    border: 2px solid #FF4D4D;
    color: #FF6B6B;
  }}
  .pill-1 {{
    background: rgba(88, 166, 255, 0.16);
    border: 2px solid #58A6FF;
    color: #58A6FF;
  }}
  .pill-2 {{
    background: rgba(46, 204, 113, 0.16);
    border: 2px solid #2ECC71;
    color: #2ECC71;
  }}
  .brand-row {{
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 16px 34px;
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    border: 1.5px solid rgba(255,255,255,0.16);
  }}
  .logo {{
    width: 56px;
    height: 56px;
    border-radius: 50%;
    border: 2.5px solid #2ECC71;
  }}
  .handle {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 26px;
    font-weight: 800;
    color: #FFFFFF;
  }}
</style>
</head>
<body>
  <div class="canvas">
    <div class="safe-square">
      <div class="top-tag">● {family} INTERVIEW</div>
      <div>
        <div class="title">{topic}</div>
        <div class="subtitle">Explained in 60 Seconds ⚡</div>
      </div>
      <div class="pills">
        {pills_html}
      </div>
      <div class="brand-row">
        {logo_img}
        <div class="handle">@conceptfirstwithmohit</div>
      </div>
    </div>
  </div>
</body>
</html>
"""


def generate_cheatsheet_and_cover(
    plan: dict[str, Any],
    root: Path,
    run_dir: Path,
    pdf_dest: Path,
    cover_dest: Path,
) -> dict[str, Path]:
    """
    Renders:
    1. A 1-page A4 Dark-Mode Engineering Interview Cheat Sheet PDF (`pdf_dest`)
    2. A 1080x1920 High-CTR Reel/Short Cover PNG (`cover_dest`) with 1:1 grid safe-zone
    """
    browser = _find_browser_executable()
    if not browser:
        raise RuntimeError("No Chromium/Edge/Chrome browser found for headless PDF & Cover generation.")

    logo_uri = _get_logo_data_uri(root)
    run_dir.mkdir(parents=True, exist_ok=True)
    pdf_dest.parent.mkdir(parents=True, exist_ok=True)
    cover_dest.parent.mkdir(parents=True, exist_ok=True)

    cs_html_path = run_dir / "cheatsheet.html"
    cs_html_path.write_text(_build_cheatsheet_html(plan, logo_uri), encoding="utf-8")

    cover_html_path = run_dir / "cover.html"
    cover_html_path.write_text(_build_cover_html(plan, logo_uri), encoding="utf-8")

    # 1. Print Cheat Sheet HTML to A4 PDF
    subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_dest.resolve()}",
            cs_html_path.resolve().as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 2. Render 1080x1920 Reel Cover PNG
    subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--window-size=1080,1920",
            f"--screenshot={cover_dest.resolve()}",
            cover_html_path.resolve().as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return {"pdf": pdf_dest, "cover": cover_dest}
