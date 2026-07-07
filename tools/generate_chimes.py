"""Generates the daypart-transition chime WAV files in assets/sounds/.

Pure stdlib (wave + math), no audio-editing dependency needed. Re-run this
and commit the output if you want to tweak a chime's notes/duration/feel:

    python tools/generate_chimes.py
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44100
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"

# Each chime is a short list of (frequency_hz, start_offset_s, duration_s)
# notes, mixed together. Pitch/feel loosely follows the existing per-daypart
# visual theme (theme.py): morning bright, afternoon neutral, evening warm
# and settling, night soft and low.
CHIMES: dict[str, list[tuple[float, float, float]]] = {
    "daypart_morning.wav": [(523.25, 0.0, 0.16), (659.25, 0.1, 0.30)],
    "daypart_afternoon.wav": [(587.33, 0.0, 0.16), (698.46, 0.1, 0.30)],
    "daypart_evening.wav": [(587.33, 0.0, 0.16), (440.00, 0.12, 0.34)],
    "daypart_night.wav": [(349.23, 0.0, 0.42)],
}

FADE_SECONDS = 0.02
AMPLITUDE = 0.3


def _tone_samples(freq: float, duration: float) -> list[float]:
    n = int(SAMPLE_RATE * duration)
    fade = int(SAMPLE_RATE * FADE_SECONDS)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        value = math.sin(2 * math.pi * freq * t)
        if i < fade:
            value *= i / fade
        elif i > n - fade:
            value *= (n - i) / fade
        samples.append(value * AMPLITUDE)
    return samples


def _write_chime(notes: list[tuple[float, float, float]], path: Path) -> None:
    total_duration = max(start + duration for _, start, duration in notes)
    n_samples = int(SAMPLE_RATE * total_duration) + 1
    mix = [0.0] * n_samples
    for freq, start, duration in notes:
        offset = int(SAMPLE_RATE * start)
        for i, sample in enumerate(_tone_samples(freq, duration)):
            if offset + i < n_samples:
                mix[offset + i] += sample

    peak = max(1.0, max(abs(sample) for sample in mix))
    frames = b"".join(
        struct.pack("<h", int(max(-1.0, min(1.0, sample / peak)) * 32767)) for sample in mix
    )
    # pylint can't resolve wave.open()'s mode-based overload, so it infers
    # Wave_read here instead of Wave_write; this is genuinely a Wave_write.
    # pylint: disable=no-member
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(frames)
    # pylint: enable=no-member


def main() -> None:
    """Write all configured chime WAV files to assets/sounds/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, notes in CHIMES.items():
        out_path = OUTPUT_DIR / filename
        _write_chime(notes, out_path)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
