"""Text-to-speech synthesis using ElevenLabs."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_ID = "eleven_flash_v2_5"
# wav/pcm at 44.1kHz require an ElevenLabs Pro subscription; mp3 works on
# the free tier and pygame's SDL_mixer decodes it natively either way.
OUTPUT_FORMAT = "mp3_44100_128"

# ElevenLabs' default stability (0.5) trends monotone/robotic; lower values
# give more natural emotional range. style adds a little expressive
# exaggeration on top. speed is 1.0 = normal pace.
VOICE_STABILITY = 0.35
VOICE_STYLE = 0.15
VOICE_SPEED = 1.0


class SpeechSynthesizer:
    """Wraps the ElevenLabs API to synthesize text into an audio file.

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
            from elevenlabs.types import VoiceSettings

            client = ElevenLabs(api_key=api_key)
            voice_settings = VoiceSettings(
                stability=VOICE_STABILITY,
                style=VOICE_STYLE,
                speed=VOICE_SPEED,
            )
        except Exception:
            logger.exception("Failed to create ElevenLabs client; speech is disabled.")
            return
        self._client = client
        self._voice_settings = voice_settings

    @property
    def is_available(self) -> bool:
        """Return whether an ElevenLabs client was configured successfully."""
        return self._client is not None

    def synthesize(self, text: str) -> bytes | None:
        """Synthesize text to audio bytes. Returns None on failure."""
        if not self.is_available:
            return None
        try:
            chunks = self._client.text_to_speech.convert(
                self._voice_id,
                text=text,
                model_id=MODEL_ID,
                output_format=OUTPUT_FORMAT,
                voice_settings=self._voice_settings,
            )
            return b"".join(chunks)
        except Exception:
            logger.exception("Speech synthesis failed for text: %r", text)
            return None

    def synthesize_to_file(self, text: str, out_path: Path) -> bool:
        """Synthesize text to an audio file. Returns False (and logs) on failure."""
        audio_bytes = self.synthesize(text)
        if audio_bytes is None:
            return False
        out_path.write_bytes(audio_bytes)
        return True
