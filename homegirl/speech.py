"""Text-to-speech synthesis using ElevenLabs."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_ID = "eleven_flash_v2_5"
OUTPUT_FORMAT = "wav_44100"


class SpeechSynthesizer:
    """Wraps the ElevenLabs API to synthesize text into a WAV file.

    Requires both an API key and a voice ID; if either is missing, or the
    client fails to construct, synthesis quietly no-ops rather than
    crashing the app.
    """

    def __init__(self, api_key: str | None, voice_id: str | None) -> None:
        self._voice_id = voice_id
        self._client = None
        if not api_key or not voice_id:
            logger.warning("ElevenLabs API key or voice ID not configured; speech is disabled.")
            return
        try:
            from elevenlabs.client import ElevenLabs

            self._client = ElevenLabs(api_key=api_key)
        except Exception:
            logger.exception("Failed to create ElevenLabs client; speech is disabled.")

    @property
    def is_available(self) -> bool:
        """Return whether an ElevenLabs client was configured successfully."""
        return self._client is not None

    def synthesize_to_file(self, text: str, out_path: Path) -> bool:
        """Synthesize text to a WAV file. Returns False (and logs) on failure."""
        if not self.is_available:
            return False
        try:
            chunks = self._client.text_to_speech.convert(
                self._voice_id,
                text=text,
                model_id=MODEL_ID,
                output_format=OUTPUT_FORMAT,
            )
            out_path.write_bytes(b"".join(chunks))
            return True
        except Exception:
            logger.exception("Speech synthesis failed for text: %r", text)
            return False
