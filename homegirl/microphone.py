"""Microphone capture with simple silence-based end-of-speech detection.

There's no wake word yet — a tap starts a recording, and this decides when
to stop it: once speech has been heard, stop after a beat of quiet; if
nothing is ever said, give up after a shorter timeout instead of waiting
for the full max duration.
"""

from __future__ import annotations

import io
import logging
import wave

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SECONDS = 0.1
MAX_RECORD_SECONDS = 12.0
PRE_SPEECH_TIMEOUT_SECONDS = 5.0
SILENCE_HANG_SECONDS = 1.2
MIN_SPEECH_SECONDS = 0.3

# Tuned against int16 samples from a typical USB mic at a normal speaking
# volume and distance; quiet room noise should sit well below this.
SILENCE_RMS_THRESHOLD = 400.0


class Microphone:
    """Records a single utterance from an input device, stopping on silence.

    Quietly no-ops (returns None) if sounddevice/numpy aren't installed or no
    input device can be reached, rather than crashing the app.
    """

    def __init__(self, device_match: str | None = None) -> None:
        self._sd = None
        self._np = None
        self._device_index: int | None = None
        try:
            import numpy as np
            import sounddevice as sd
        except Exception:
            logger.exception("sounddevice/numpy not available; microphone input is disabled.")
            return

        self._sd = sd
        self._np = np
        if device_match:
            self._device_index = self._find_device(device_match)
            if self._device_index is None:
                logger.warning("No input device matched %r; using system default.", device_match)

    @property
    def is_available(self) -> bool:
        """Return whether the capture libraries loaded (not a guarantee a device works)."""
        return self._sd is not None

    def _find_device(self, match: str) -> int | None:
        try:
            devices = self._sd.query_devices()
        except Exception:
            logger.warning("Could not query audio input devices.")
            return None
        for index, info in enumerate(devices):
            if info.get("max_input_channels", 0) > 0 and match.lower() in info.get("name", "").lower():
                return index
        return None

    def record_utterance(self) -> bytes | None:
        """Record until a beat of silence follows speech, and return WAV bytes.

        Returns None if capture is unavailable, or if nothing was said before
        the pre-speech timeout elapsed.
        """
        if not self.is_available:
            return None

        block_frames = int(SAMPLE_RATE * BLOCK_SECONDS)
        pre_speech_blocks = max(1, round(PRE_SPEECH_TIMEOUT_SECONDS / BLOCK_SECONDS))
        silence_hang_blocks = max(1, round(SILENCE_HANG_SECONDS / BLOCK_SECONDS))
        min_speech_blocks = max(1, round(MIN_SPEECH_SECONDS / BLOCK_SECONDS))
        max_blocks = max(1, round(MAX_RECORD_SECONDS / BLOCK_SECONDS))

        blocks = []
        speech_blocks = 0
        silence_blocks = 0

        try:
            with self._sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                device=self._device_index,
                blocksize=block_frames,
            ) as stream:
                for _ in range(max_blocks):
                    block, _overflowed = stream.read(block_frames)
                    blocks.append(block.copy())

                    rms = float(self._np.sqrt(self._np.mean(block.astype(self._np.float64) ** 2)))
                    if rms >= SILENCE_RMS_THRESHOLD:
                        speech_blocks += 1
                        silence_blocks = 0
                    else:
                        silence_blocks += 1

                    if speech_blocks == 0 and len(blocks) >= pre_speech_blocks:
                        break
                    if speech_blocks >= min_speech_blocks and silence_blocks >= silence_hang_blocks:
                        break
        except Exception:
            logger.exception("Microphone recording failed.")
            return None

        if speech_blocks < min_speech_blocks:
            return None

        audio = self._np.concatenate(blocks, axis=0)
        return _to_wav_bytes(audio, SAMPLE_RATE)


def _to_wav_bytes(audio, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())
    return buffer.getvalue()
