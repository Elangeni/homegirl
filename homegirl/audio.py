"""Sound effect playback through the configured speaker."""

from __future__ import annotations

import logging
from pathlib import Path

import pygame
from pygame._sdl2 import audio as sdl_audio

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Plays short one-shot sound effects through a chosen output device.

    Picks an SDL output device whose name contains ``device_match`` (case
    insensitive) if given, so playback goes through e.g. a USB speaker
    instead of whatever the system happens to default to (a Pi with HDMI
    outputs registered can default to the monitor's speaker instead).
    Falls back to the system default device if no match is found, and
    no-ops quietly if the audio subsystem can't be reached at all.
    """

    def __init__(self, device_match: str | None = None) -> None:
        device_name = self._find_device(device_match) if device_match else None
        try:
            if pygame.mixer.get_init() is not None:
                pygame.mixer.quit()
            pygame.mixer.init(devicename=device_name)
            if device_match and device_name is None:
                logger.warning("No audio device matched %r; using system default.", device_match)
        except pygame.error:
            logger.warning("Audio output unavailable; sounds will be skipped.")

    @staticmethod
    def _find_device(match: str) -> str | None:
        try:
            pygame.mixer.init()
            names = list(sdl_audio.get_audio_device_names(False))
        except pygame.error:
            return None
        finally:
            pygame.mixer.quit()
        for name in names:
            if match.lower() in name.lower():
                return name
        return None

    @property
    def is_available(self) -> bool:
        return pygame.mixer.get_init() is not None

    def play(self, path: Path) -> None:
        """Play a sound file once, fire-and-forget; no-ops on failure."""
        if not self.is_available:
            return
        try:
            pygame.mixer.Sound(str(path)).play()
        except pygame.error:
            logger.warning("Could not play sound: %s", path)
