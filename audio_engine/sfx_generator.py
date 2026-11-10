from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100


def _write_stereo_wav(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    stereo = np.column_stack([pcm, pcm]).ravel()
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(stereo.tobytes())


def generate_whoosh(path: Path) -> None:
    """Soft cinematic transition whoosh (180ms)."""
    duration = 0.18
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 1, len(t))
    # Simple moving-average lowpass filter + pitch sweep sine
    kernel = np.ones(32) / 32.0
    filtered = np.convolve(noise, kernel, mode="same")
    freq = np.linspace(180.0, 65.0, len(t))
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    env = np.sin(np.pi * (t / duration)) ** 1.8
    audio = (0.35 * filtered + 0.45 * tone) * env * 0.45
    _write_stereo_wav(path, audio)


def generate_pop(path: Path) -> None:
    """Crisp warm UI pop for badges & callouts (95ms)."""
    duration = 0.095
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(420.0, 860.0, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    env = np.exp(-t * 38.0) * np.minimum(1.0, t / 0.004)
    audio = (np.sin(phase) + 0.3 * np.sin(2 * phase)) * env * 0.5
    _write_stereo_wav(path, audio)


def generate_stamp(path: Path) -> None:
    """Deep percussive impact thud for red problem stamps (150ms)."""
    duration = 0.15
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(150.0, 42.0, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    env = np.exp(-t * 24.0) * np.minimum(1.0, t / 0.002)
    click = np.exp(-t * 180.0) * np.sin(2 * np.pi * 1200.0 * t) * 0.3
    audio = (np.sin(phase) * env + click) * 0.55
    _write_stereo_wav(path, audio)


def generate_chime(path: Path) -> None:
    """Subtle warm golden chord for Cheat Sheet outro card (360ms)."""
    duration = 0.36
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    env = np.exp(-t * 9.5) * np.minimum(1.0, t / 0.008)
    chord = (
        0.55 * np.sin(2 * np.pi * 587.33 * t)  # D5
        + 0.35 * np.sin(2 * np.pi * 880.0 * t)  # A5
        + 0.25 * np.sin(2 * np.pi * 1174.66 * t)  # D6
    )
    audio = chord * env * 0.45
    _write_stereo_wav(path, audio)


def ensure_sfx_assets(root: Path) -> dict[str, Path]:
    audio_dir = root / "my-video" / "public" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "whoosh": audio_dir / "sfx_whoosh.wav",
        "pop": audio_dir / "sfx_pop.wav",
        "stamp": audio_dir / "sfx_stamp.wav",
        "chime": audio_dir / "sfx_chime.wav",
    }
    generate_whoosh(files["whoosh"])
    generate_pop(files["pop"])
    generate_stamp(files["stamp"])
    generate_chime(files["chime"])
    return files


if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parent.parent
    out = ensure_sfx_assets(root_dir)
    for k, v in out.items():
        print(f"[sfx] Generated {k}: {v} ({v.stat().st_size} bytes)")
