"""Sound effect playback through the configured speaker."""

from __future__ import annotations

import io
import logging
from collections.abc import Iterable
from pathlib import Path

import pygame
from pygame._sdl2 import audio as sdl_audio

logger = logging.getLogger(__name__)

# Reserved so pygame's automatic channel allocation (used by one-shot sounds
# like chimes and the greeting) never steals the channel `play_stream` uses.
_VOICE_CHANNEL_INDEX = 0


class AudioPlayer:
    """Plays short one-shot sound effects through a chosen output device.

    Picks an SDL output device whose name contains ``device_match`` (case
    insensitive) if given, so playback goes through e.g. a USB speaker
    instead of whatever the system happens to default to (a Pi with HDMI
    outputs registered can default to the monitor's speaker instead).
    Falls back to the system default device if no match is found, and
    no-ops quietly if the audio subsystem can't be reached at all.
    """

    _WARMUP_SECONDS = 0.2

    def __init__(self, device_match: str | None = None) -> None:
        device_name = self._find_device(device_match) if device_match else None
        try:
            if pygame.mixer.get_init() is not None:
                pygame.mixer.quit()
            pygame.mixer.init(devicename=device_name)
            pygame.mixer.set_reserved(_VOICE_CHANNEL_INDEX + 1)
            if device_match and device_name is None:
                logger.warning("No audio device matched %r; using system default.", device_match)
            self.warm_up()
        except pygame.error:
            logger.warning("Audio output unavailable; sounds will be skipped.")

    def warm_up(self) -> None:
        """Play a moment of silence so the next real sound isn't clipped.

        Some USB audio devices drop the opening fraction of a second of
        sound played after a period of quiet, while the underlying
        ALSA/PipeWire stream wakes back up. This runs once automatically
        when the mixer opens, but callers should call it again right before
        playing anything that was queued up behind a network call (a TTS
        greeting or conversation reply) — the wait for that call is often
        long enough for the device to go back to sleep, silently undoing the
        original warm-up.
        """
        frequency, _, channels = pygame.mixer.get_init()
        frame_count = int(frequency * self._WARMUP_SECONDS)
        silence = bytes(frame_count * channels * 2)
        pygame.mixer.Sound(buffer=silence).play()
        pygame.time.wait(round(self._WARMUP_SECONDS * 1000))

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
        """Return whether the mixer initialized successfully."""
        return pygame.mixer.get_init() is not None

    def play(self, path: Path) -> None:
        """Play a sound file once, fire-and-forget; no-ops on failure."""
        if not self.is_available:
            return
        try:
            pygame.mixer.Sound(str(path)).play()
        except pygame.error:
            logger.warning("Could not play sound: %s", path)

    def play_stream(self, chunks: Iterable[bytes]) -> None:
        """Play a sequence of complete audio buffers back-to-back, gaplessly.

        Each item in ``chunks`` must be a whole, independently decodable
        audio file's bytes (e.g. one synthesized sentence), not a raw partial
        byte stream — pygame's mixer can't resume mid-file. Queuing each one
        on a dedicated channel as it becomes available lets playback of an
        earlier sentence overlap with synthesis of the next, rather than
        waiting for an entire reply to be synthesized before any of it is
        heard. Iterates ``chunks`` lazily, so a generator that synthesizes
        on demand drives the pipelining.
        """
        if not self.is_available:
            return
        channel = pygame.mixer.Channel(_VOICE_CHANNEL_INDEX)
        started = False
        try:
            for chunk in chunks:
                sound = pygame.mixer.Sound(file=io.BytesIO(chunk))
                if started:
                    channel.queue(sound)
                else:
                    channel.play(sound)
                    started = True
        except pygame.error:
            logger.warning("Could not play streamed audio.")
