"""Text-to-speech synthesis using Piper (offline, on-device)."""

from __future__ import annotations

import logging
import wave
from pathlib import Path

logger = logging.getLogger(__name__)


class SpeechSynthesizer:
    """Wraps a local Piper voice model to synthesize text into a WAV file.

    Loading the model happens once at construction. If the model file isn't
    present (e.g. not downloaded yet) or Piper fails to load it, synthesis
    quietly no-ops rather than crashing the app.
    """

    def __init__(self, voice_model_path: Path) -> None:
        self._voice = None
        if not voice_model_path.exists():
            logger.warning("Piper voice model not found at %s; speech is disabled.", voice_model_path)
            return
        try:
            import piper
            from piper import PiperVoice

            espeak_data_dir = Path(piper.__file__).parent / "espeak-ng-data"
            self._voice = PiperVoice.load(str(voice_model_path), espeak_data_dir=str(espeak_data_dir))
        except Exception:
            logger.exception("Failed to load Piper voice; speech is disabled.")

    @property
    def is_available(self) -> bool:
        return self._voice is not None

    def synthesize_to_file(self, text: str, out_path: Path) -> bool:
        """Synthesize text to a WAV file. Returns False (and logs) on failure."""
        if not self.is_available:
            return False
        try:
            with wave.open(str(out_path), "wb") as wav_file:
                self._voice.synthesize_wav(text, wav_file)
            return True
        except Exception:
            logger.exception("Speech synthesis failed for text: %r", text)
            return False
