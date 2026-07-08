"""Speech-to-text transcription using ElevenLabs Scribe."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

MODEL_ID = "scribe_v1"


class SpeechRecognizer:
    """Wraps the ElevenLabs API to transcribe recorded audio into text.

    Requires an API key; if missing, or the client fails to construct,
    transcription quietly no-ops rather than crashing the app.
    """

    def __init__(self, api_key: str | None) -> None:
        self._client = None
        if not api_key:
            logger.warning("ElevenLabs API key not configured; speech recognition is disabled.")
            return
        try:
            from elevenlabs.client import ElevenLabs

            self._client = ElevenLabs(api_key=api_key)
        except Exception:
            logger.exception("Failed to create ElevenLabs client; speech recognition is disabled.")

    @property
    def is_available(self) -> bool:
        """Return whether an ElevenLabs client was configured successfully."""
        return self._client is not None

    def transcribe(self, audio_wav_bytes: bytes) -> str | None:
        """Transcribe WAV audio bytes to text. Returns None on failure or silence."""
        if not self.is_available:
            return None
        try:
            response = self._client.speech_to_text.convert(
                model_id=MODEL_ID,
                file=("recording.wav", audio_wav_bytes, "audio/wav"),
            )
        except Exception:
            logger.exception("Speech-to-text request failed")
            return None

        text = (getattr(response, "text", None) or "").strip()
        return text or None
