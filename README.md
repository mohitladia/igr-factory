# Instagram Reel Factory — Complete Starter Codebase

A universal, JSON-driven technical Reel generator. Enter a topic once; the pipeline creates a Hinglish storyboard, beat-level narration, Edge TTS word timings, optional AI-generated supporting images, animated Remotion scenes, and a vertical MP4.

## What is included

- **AI story + beat generator** using an OpenAI-compatible chat-completions endpoint (configured for the FreeLLM local gateway by default).
- **Demo mode** so the pipeline can be tested without an LLM API key.
- **Edge TTS** audio generated per visual beat, with word-boundary metadata when available.
- **Optional hosted image generation** through Replicate FLUX Schnell. This is disabled by default and may incur API charges.
- **Universal Remotion renderer** with reusable visual behaviors: cinematic title, architecture nodes/connections, animated data flow, concept visuals, comparison, metric callout, and summary.
- **One-command Windows orchestration** plus setup scripts.

This is a runnable starter implementation, not a claim that every AI-generated script is automatically fact-checked or that every possible topic has perfect visuals. Preview each Reel before publishing.

## Requirements

- Windows 10/11
- Python 3.12 recommended
- Node.js and npm (the previously used Node 26 installation should be detected by the setup script)
- Internet access for Edge TTS and optional hosted image generation
- FFmpeg/ffprobe on PATH recommended for precise audio-duration probing
- FreeLLM/OpenAI-compatible API key for AI-generated scripts (not needed in `--demo` mode)

## 1. Install

1. Extract this ZIP to a folder such as `C:\Instagram-Reel-Factory-Complete`.
2. Open that folder in File Explorer.
3. Double-click `setup_windows.bat`.
4. Wait for Python packages and Remotion npm dependencies to install.
5. Open the `.env` file created by setup and set your LLM key:

```dotenv
OPENAI_BASE_URL=http://127.0.0.1:31415/v1
FREELLM_API_KEY=your_key_here
OPENAI_MODEL=auto
```

Do not paste your API key into chat or commit `.env` to Git.

## 2. Generate a Reel with AI

Open PowerShell in the project folder and run:

```powershell
.\.venv\Scripts\python.exe run.py --topic "Apache Kafka" 
```

Or double-click `run_reel.bat` and pass the topic after it:

```powershell
.\run_reel.bat --topic "How Redis works"
```

The output is written to:

```text
output\final\<timestamp>_<topic>.mp4
```

The full run artifacts and plans are stored under:

```text
output\runs\<run-id>\
```

## 3. Test the pipeline without an LLM key

The demo still uses Edge TTS, so it needs internet access, but it does not call the LLM:

```powershell
.\.venv\Scripts\python.exe run.py --demo --topic "Apache Kafka" --skip-images
```

The demo plan is deterministic. It is intended to verify narration, timeline generation, Remotion rendering, and the MP4 output path—not to demonstrate the quality of AI-authored content.

## 4. Optional AI-generated supporting images

The renderer creates technical diagrams and motion graphics itself. AI-generated images are only supporting cutaways/background art; important labels and architecture connections remain Remotion-rendered for accuracy.

To enable optional images:

1. Obtain a Replicate API token.
2. Put it in `.env`:

```dotenv
REPLICATE_API_TOKEN=your_replicate_token
ENABLE_AI_IMAGES=true
MAX_AI_IMAGES_PER_REEL=4
REPLICATE_MODEL=black-forest-labs/flux-schnell
```

3. Run the normal command again.

Image generation is a hosted, metered service and can incur charges. Leave `ENABLE_AI_IMAGES=false` to use only deterministic Remotion visuals. Failure to generate an optional image does not stop rendering.

Model details: https://replicate.com/black-forest-labs/flux-schnell/api

## 5. Useful options

```powershell
# AI plan, voice and assets; stop before Remotion export
.\.venv\Scripts\python.exe run.py --topic "Kafka partitions" --plan-only

# Skip optional paid image generation
.\.venv\Scripts\python.exe run.py --topic "Spring Boot internals" --skip-images

# Demo content without LLM
.\.venv\Scripts\python.exe run.py --demo --topic "Apache Kafka" --skip-images

# Set target duration in seconds (actual duration follows spoken audio)
.\.venv\Scripts\python.exe run.py --topic "Redis caching" --duration 70
```

## 6. Preview the composition manually

```powershell
cd my-video
npm run dev
```

Open the Remotion Studio URL printed in the terminal. The Python pipeline writes the current plan to `my-video/src/data/plan.json` and audio/images to `my-video/public`.

## Instagram publishing and comment-to-DM

Set `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, and a public `PUBLIC_VIDEO_URL` in `.env` before using `--publish-instagram`. Instagram must be able to fetch the MP4 over HTTPS. Catbox uploads are disabled by default; set `ALLOW_PUBLIC_CATBOX_UPLOADS=true` only if you accept public third-party hosting. Prefer your own hosting URL.

For optional PDF delivery, set `CHEATSHEET_DEFAULT_URL` to a public URL you control, or explicitly opt in to Catbox uploads. Run with `--publish-instagram --auto-dm`; this scans comments on the Reel published in that run once. To keep watching for new comments, start this after publishing and keep it running:

```powershell
.\.venv\Scripts\python.exe tools\watch_instagram_comments.py --media-id "YOUR_INSTAGRAM_MEDIA_ID" --keyword "KAFKA" --cheatsheet-url "https://your-domain/notes.pdf"
```

The watcher remembers processed comment IDs under `output/state/instagram_dm`. Keep that folder intact to avoid reprocessing comments. The Instagram API account and permissions must support comment private replies.

## 7. TypeScript check

```powershell
cd my-video
npx.cmd tsc --noEmit
```

## How the timing works

- The script is split into independent visual beats.
- Edge TTS creates one audio file per beat.
- The pipeline records word-boundary start/end timestamps when Edge TTS provides them.
- Each beat's frame duration is calculated from the actual audio duration plus a small visual tail.
- Remotion sequences the beat, its captions, and its audio together.

The configured target duration is a generation target, not a forced time-stretch. The actual MP4 duration follows the narration generated by the LLM and TTS voice.

## Troubleshooting

### `No LLM key found`
Edit `.env` and set `FREELLM_API_KEY` or `OPENAI_API_KEY`. If you only want to test the renderer, use `--demo`.

### FreeLLM connection refused
Make sure the local FreeLLM gateway is running at the `OPENAI_BASE_URL` address in `.env`. If your gateway uses another port, update it there.

### `edge-tts` or audio generation fails
Check internet connectivity and retry. The voice service is online; this project does not synthesize speech offline.

### `ffprobe` not found
Install FFmpeg and add its `bin` directory to PATH. The renderer can still run, but duration probing is less precise if ffprobe is unavailable.

### Remotion says dependencies are missing
Run `setup_windows.bat` again, or from `my-video` run `npm install`.

### MP4 looks repetitive
The renderer is data-driven and has several beat types, but visual quality depends on the AI plan. Inspect `output/runs/<run-id>/final_plan.json`. Improve the beat descriptions, node/connection data, and narration before changing React components. The renderer intentionally does not ask an image model to draw exact text or technical labels.

## Important implementation notes

- Never hardcode API keys in Python or TypeScript.
- Keep `.env` private.
- Do not delete the run folder until the video has been checked.
- AI-generated technical content should be reviewed for accuracy before publishing.
- The old static image slideshow is not used as the primary renderer.


## Universal topic engine update (v2)

This update adds automatic topic-family classification and topic-specific teaching formats:
- DSA / algorithm walkthroughs (Two Sum is included as a dedicated demo)
- Distributed messaging / event streaming (Kafka, RabbitMQ, SQS)
- Caching (Redis, cache concepts)
- Backend frameworks (Spring Boot, Hibernate/JPA)
- Programming/runtime concepts (Java, JVM, concurrency)
- System design / architecture trade-offs
- A general technical explainer fallback for other topics

### Important topic-safety behavior
- The exact requested topic is passed into the AI prompt as a hard constraint.
- If the model changes the returned topic, validation stops the pipeline.
- Placeholder and production-instruction text is rejected.
- `visual_action` is treated as an internal direction, not viewer-facing copy; the Remotion renderer no longer prints it as text.
- Demo mode is topic-aware. For example, `Two Sum` produces a DSA walkthrough rather than a Kafka sample.

### Test the topic-aware demo
From the extracted project folder in CMD:

```cmd
setup_windows.bat
run_reel.bat --demo --topic "Two Sum" --skip-images
```

For a real AI-generated plan (requires your local `.env` configuration):

```cmd
run_reel.bat --topic "Two Sum" --skip-images
```

Try other topics:

```cmd
run_reel.bat --demo --topic "Apache Kafka" --skip-images
run_reel.bat --demo --topic "Redis caching" --skip-images
run_reel.bat --demo --topic "Spring Boot dependency injection" --skip-images
```

Note: demo mode is a deterministic pipeline smoke-test, not the full AI content quality benchmark. The DSA Two Sum demo has a dedicated walkthrough; other demo topics use a generic topic-safe sample structure. For production-quality topic-specific content, use the configured LLM mode.

### Verification status
The verification notes below refer to earlier snapshots and may not match the current code. For a local check, run `python -m unittest discover -s tests -v` and `npx.cmd tsc --noEmit` from `my-video`. A real MP4 render, Instagram publish, YouTube upload, and comment-DM require local dependencies and credentials; review generated videos before publishing.


## v3: topic-drift bug fix

This version fixes a critical bug found in the generated Two Sum plan:
- The previous generator silently overwrote the AI's returned `topic` with the user's topic before validation. That hid topic drift. It now preserves the AI-returned topic so validation can reject mismatches.
- Two Sum plans are checked across narration, titles, visual instructions, nodes and steps. Kafka-specific terms cause a hard failure before audio/rendering.
- Two Sum must include HashMap, complement, target and O(n) teaching concepts.
- The user topic is printed in the run log along with detected family and teaching format.
- Prompt newline escaping is corrected so the model receives readable separate instructions.
- A regression test injects Kafka narration into a Two Sum plan and verifies that it is rejected.

### Run the new code (important: use this extracted v3 folder)
```cmd
setup_windows.bat
run_reel.bat --demo --topic "Two Sum" --skip-images
```

For the real AI path:
```cmd
run_reel.bat --topic "Two Sum" --skip-images
```

The run must show `family=dsa` and `format=algorithm_walkthrough`. If the model returns Kafka content, the pipeline now stops with a relevance error instead of rendering the wrong video. Demo mode creates the deterministic Two Sum teaching plan.

The test counts above describe an earlier snapshot; use the current verification commands in the section above for this checkout.
