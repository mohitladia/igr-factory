# Instagram Reel Factory

A Python + TypeScript pipeline that turns a single topic into a technical short-form video: it generates a storyboard, validates topic relevance, synthesizes beat-level narration, builds visual assets, renders a vertical MP4 with Remotion, and can optionally publish to Instagram and YouTube.

This project is designed for creator workflows where the output is a short, highly structured, technical explainer reel. It is especially tuned for DSA, system design, backend engineering, distributed systems, and concept-first educational topics.

## What this project does

The repository is a full end-to-end factory for `reel` creation:

- Generate a plan from a user topic using an OpenAI-compatible LLM endpoint
- Validate the returned plan for topic drift and teaching correctness
- Score the story quality and sanitize the plan before rendering
- Route each beat to a matching visual style (architecture, metric, comparison, data flow, summary, etc.)
- Generate per-beat narration with Edge TTS and optional SFX
- Create a cheat sheet PDF/cover and metadata files
- Render a vertical MP4 in Remotion
- Optionally publish the final reel to Instagram or YouTube

From a high-level perspective, the system behaves like a content-ops pipeline: prompt -> plan -> validate -> audio -> visuals -> render -> publish.

## Stack

- Python 3.12 recommended
- OpenAI-compatible API endpoint via `.env` (`OPENAI_BASE_URL`, `OPENAI_API_KEY`)
- Edge TTS for voice generation
- Remotion + React + TypeScript for the renderer
- Optional Replicate image generation for supporting visuals
- Meta Graph API / YouTube Data API for publishing

## Architecture at a glance

```text
run.py
  -> generate / validate storyboard
  -> criticize / audit plan
  -> assign visuals
  -> generate voice + SFX + word timings
  -> generate cover / cheatsheet / metadata
  -> write Remotion render plan
  -> render MP4 with my-video/
  -> publish to Instagram / YouTube (optional)
```

## Repository layout

```text
.
├── .env.example                # sample environment variables
├── .gitignore
├── README.md                   # project documentation
├── NOTES.md                    # creator notes / cheat-sheet highlights
├── PROJECT_STATUS.txt          # release status and verification notes
├── requirements.txt            # Python runtime dependencies
├── requirements-dev.txt        # dev/test dependencies
├── run.py                     # command entry point and orchestration
├── run_demo.bat               # demo render launcher
├── run_reel.bat               # main reel launcher
├── setup_windows.bat          # first-time install flow
├── mcp_config.json             # MCP-related configuration
├── ai_engine/                  # story generation, validation, auditing, visual routing
├── audio_engine/               # TTS, pronunciation, SFX, audio verification
├── visual_engine/             # asset generation and PDF/cover generation
├── renderer/                  # timeline writer for the render layer
├── publisher/                 # Instagram / YouTube publishing automation
├── config/                    # runtime config file(s)
├── my-video/                  # Remotion app (React + TypeScript)
├── output/                    # generated plans, videos, metadata, run folders
├── tests/                     # automated tests for planner and pipeline logic
├── tools/                     # utility scripts for automation / monitoring
├── visual_engine/             # generated/utility visual helpers
└── dashboard/                 # project dashboard area if present in the repo
```

## Core modules

### `run.py`

This is the main orchestrator. It:

- loads environment variables via `dotenv`
- parses CLI flags such as `--topic`, `--demo`, `--platform`, `--plan-only`, `--publish-instagram`, `--upload-youtube`
- builds or generates the technical storyboard
- validates the plan against topic constraints
- calculates story quality and enforces quality gates
- creates audio assets and metadata
- writes the render plan used by Remotion
- renders MP4 outputs and optionally publishes them

This file is the best place to trace the full lifecycle of a single generated reel.

### `ai_engine/`

The AI/planning layer is responsible for story generation and quality control.

Key files:

- `plan_generator.py` — generates the storyboard / beat structure from the topic
- `topic_classifier.py` — identifies topic family and teaching format
- `critic.py` — judges story quality with scoring and feedback
- `visual_router.py` — maps beat types to visual templates
- `plan_auditor.py` — sanitizes the plan against narrative/visual constraints
- `demo_plan.py` — deterministic sample plans for testing without LLM access
- `post_inspector.py` — checks the output video after rendering

### `audio_engine/`

The audio pipeline converts story beats to synthetic speech and timing metadata.

Key files:

- `voice_generator.py` — generates voice files and beat timings
- `sfx_generator.py` — injects sound effects or ambience
- `tts_text.py` — prepares TTS text and pronunication handling
- `pronunciations.json` — custom pronunciation rules
- `audio_verifier.py` — validates generated audio consistency

### `visual_engine/`

This layer manages supporting visuals, cover generation, and exported notes.

Key files:

- `build_assets.py` — optional supporting imagery or asset generation
- `cheatsheet_generator.py` — creates the PDF interview/cheat-sheet style output and cover
- `replicate_image_provider.py` — integrates hosted image generation via Replicate

### `renderer/`

The render architecture is intentionally separate from Python generation. The Python side writes a `plan.json` consumed by the Remotion app.

Key file:

- `timeline.py` — writes the timeline plan for the video renderer

### `my-video/`

This is the TypeScript UI + render app based on Remotion.

Key files:

- `package.json` — scripts and dependencies
- `src/index.ts` — Remotion entry point
- `remotion.config.ts` — Remotion config
- `tsconfig.json` — TypeScript config

The `my-video` folder is where visual templates are rendered as a final MP4 output.

### `publisher/`

This handles social publishing and metadata flows.

Key file:

- `social_publisher.py` — Instagram and YouTube publishing logic, metadata writers, and DM automation helpers

## How the pipeline works

The core flow in `run.py` is fairly direct:

1. Read `.env` and parse flags.
2. Determine the topic and platform selection.
3. Generate a story plan using either:
   - the LLM flow (`generate_plan`), or
   - the demo plan (`build_demo_plan`) when `--demo` is passed
4. Validate the plan against topic-specific constraints.
5. Run a story-quality critic and fix or reject issues.
6. Sanitize and route the plan to beat-level visual templates.
7. Generate TTS narration per beat and keep timing metadata.
8. Generate optional cheat-sheet PDF, cover, metadata and supporting assets.
9. Write the render plan consumed by Remotion.
10. Render MP4(s) with `my-video`.
11. Optionally publish to Instagram / YouTube and trigger auto-DM logic.

This is not a pure LLM-only project; it is a deterministic content engineering system with explicit quality gates and a render engine.

## Requirements

### Local setup

- Windows 10/11 recommended
- Python 3.12 recommended
- Node.js + npm
- FFmpeg/ffprobe on PATH recommended
- Internet access for Edge TTS and optional hosted image generation
- OpenAI-compatible API or local FreeLLM gateway for AI plans

### Environment variables

The repo includes a `.env.example` file. Copy it to `.env` and fill in the relevant values.

```dotenv
OPENAI_BASE_URL=http://127.0.0.1:31415/v1
OPENAI_API_KEY=
FREELLM_API_KEY=
OPENAI_MODEL=mistral-large-3

TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=TX3LPaxmHKxFdv7VOQHJ
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
TTS_VOICE=hi-IN-MadhurNeural
TTS_RATE=+15%

INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=
PUBLIC_VIDEO_URL=
CHEATSHEET_DEFAULT_URL=
ALLOW_PUBLIC_CATBOX_UPLOADS=false

YOUTUBE_ACCESS_TOKEN=
YOUTUBE_PRIVACY_STATUS=public

VIDEO_FPS=30
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920
TARGET_DURATION_SECONDS=70
REPLICATE_API_TOKEN=
REPLICATE_MODEL=black-forest-labs/flux-schnell
ENABLE_AI_IMAGES=false
MAX_AI_IMAGES_PER_REEL=4
REMOTION_CODEC=h264
```

## Installation

Use the bundled Windows setup script:

```powershell
setup_windows.bat
```

This creates a virtual environment, installs Python requirements, copies `.env.example` to `.env`, and runs `npm install` in `my-video`.

## Running the project

### Demo mode (no LLM API required)

```powershell
.\.venv\Scripts\python.exe run.py --demo --topic "Two Sum" --skip-images
```

This is useful when you want to validate the full rendering flow without a live LLM endpoint.

### Full AI mode

```powershell
.\.venv\Scripts\python.exe run.py --topic "Apache Kafka"
```

### Render only one platform

```powershell
.\.venv\Scripts\python.exe run.py --topic "How Redis works" --platform reel
```

### Run both Instagram Reel and YouTube Short

```powershell
.\.venv\Scripts\python.exe run.py --topic "System Design Basics" --platform both
```

### Generate storyboard only

```powershell
.\.venv\Scripts\python.exe run.py --topic "Kafka partitions" --script-only
```

### Stop before rendering MP4

```powershell
.\.venv\Scripts\python.exe run.py --topic "Spring Boot internals" --plan-only
```

### Publish after rendering

```powershell
.\.venv\Scripts\python.exe run.py --topic "Two Sum" --publish-instagram --auto-dm
```

Note: `--auto-dm` requires a Reel upload target and is intended to be used with `--publish-instagram`.

## Output structure

Every run creates a timestamped directory under `output/runs/`:

```text
output/
├── final/
│   ├── <timestamp>_<slug>.mp4
│   ├── <timestamp>_<slug>_cover.png
│   ├── <timestamp>_<slug>_cheatsheet.pdf
│   ├── <timestamp>_<slug>_instagram_metadata.txt
│   └── <timestamp>_<slug>_youtube_metadata.txt
└── runs/
    └── <timestamp>_<slug>/
        ├── plan_before_audio.json
        ├── final_plan.json
        ├── instagram_metadata.txt
        ├── youtube_metadata.txt
        └── ...audio and asset files
```

The generated run directory is the easiest place to debug plan drift, timing issues, or visual mismatches.

## TypeScript Remotion app

The renderer app lives in `my-video/` and is launched with:

```powershell
cd my-video
npm run dev
```

This opens Remotion Studio so you can preview the generated plan and fix composition issues interactively.

Type-checking:

```powershell
cd my-video
npx.cmd tsc --noEmit
```

## Testing

Use standard Python unittest discovery:

```powershell
python -m unittest discover -s tests -v
```

This repository includes tests for:

- topic classification
- quality critic scoring
- audio verification
- post-render inspection
- publisher logic
- timeline generation
- visual routing
- dashboard safety checks

## Topic-aware design

A notable feature of this repo is its topic-family guardrail logic. It does not blindly accept any AI output. It attempts to ensure that the generated plan stays aligned with the requested topic.

Examples include:

- DSA / algorithm walkthroughs
- distributed messaging / Kafka-style explanations
- caching / Redis concepts
- backend frameworks and system design
- generic technical explainers

The project includes a `TopicAlignmentError` flow and quality checks to stop invalid plans before they reach the render phase.

## Publishing flow

The repo can optionally publish finished videos to social platforms:

- Instagram Reel publishing via Meta Graph API
- YouTube Shorts upload via YouTube Data API v3
- comment scanning + DM automation using a cheatsheet URL

This is handled by the `publisher` module and is conditioned behind environment credentials and feature flags.

## Troubleshooting

### No LLM key found

Update `.env` with either:

- `OPENAI_API_KEY`, or
- `FREELLM_API_KEY`, or use `--demo` mode

### Local FreeLLM connection refused

Ensure the gateway is running at the configured `OPENAI_BASE_URL`.

### `edge-tts` or voice generation fails

Check internet connectivity. Edge TTS is a cloud-based voice service, not an offline synthesizer.

### `ffprobe` not found

Install FFmpeg and add it to PATH. The pipeline can still run, but duration calibration will be less precise.

### Remotion dependencies missing

Re-run:

```powershell
setup_windows.bat
```

or from `my-video`:

```powershell
npm install
```

### MP4 output looks wrong or off-topic

Review the generated files in the relevant `output/runs/<timestamp>_<slug>/` folder and inspect:

- `plan_before_audio.json`
- `final_plan.json`
- generated metadata files

This repo is intentionally built to expose detailed artifacts so debugging is easier than using a black-box pipeline.

## Notes and caveats

- `.env` contains secrets and should not be committed.
- AI-generated technical content should still be reviewed before publishing.
- Optional hosted image generation can incur extra API costs.
- The render phase depends on a valid plan and generated voice assets.
- The system is strongest for structured technical explainers rather than open-ended narrative storytelling.

## Recommended quickstart

If you want the fastest path to a working render:

```powershell
setup_windows.bat
.\.venv\Scripts\python.exe run.py --demo --topic "Two Sum" --skip-images
```

If you want the real AI version:

```powershell
.\.venv\Scripts\python.exe run.py --topic "Two Sum" --skip-images
```

## Summary

Instagram Reel Factory is a production-style technical short-form content pipeline built around a Python orchestration layer and a Remotion render app. It is designed for creators or engineers who want to generate educational vertical videos from a single topic with a consistent quality gate, beat-based narration, and optional social publishing.

The repository is best understood as a content factory rather than a simple script: it converts a topic into a structured explanatory plan, validates it, renders it as a vertical video, and optionally publishes it to social platforms.
