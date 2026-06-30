"""Disk-backed animated backgrounds."""

from __future__ import annotations

from pathlib import Path

import pygame

from homegirl.greeting import Daypart


class FrameAnimation:
    """Loop through a sequence of PNG frames at a stable cadence."""

    def __init__(self, frames: list[pygame.Surface], seconds_per_frame: float) -> None:
        self._frames = frames
        self._seconds_per_frame = seconds_per_frame
        self._elapsed = 0.0
        self._index = 0

    @property
    def current_frame(self) -> pygame.Surface | None:
        """Return the active frame, or None if no frames were loaded."""
        if not self._frames:
            return None
        return self._frames[self._index]

    def update(self, delta_seconds: float) -> None:
        """Advance the animation without coupling it to clock updates."""
        if len(self._frames) <= 1:
            return

        self._elapsed += delta_seconds
        while self._elapsed >= self._seconds_per_frame:
            self._elapsed -= self._seconds_per_frame
            self._index = (self._index + 1) % len(self._frames)


class BackgroundManager:
    """Load and switch daypart-specific PNG frame animations."""

    def __init__(self, assets_dir: Path, seconds_per_frame: float) -> None:
        self._assets_dir = assets_dir
        self._seconds_per_frame = seconds_per_frame
        self._animations: dict[Daypart, FrameAnimation] = {}
        self._active_daypart: Daypart | None = None

    def set_daypart(self, daypart: Daypart) -> None:
        """Switch to the frame folder matching the current daypart."""
        if self._active_daypart == daypart:
            return
        if daypart not in self._animations:
            self._animations[daypart] = self._load_animation(daypart)
        self._active_daypart = daypart

    def update(self, delta_seconds: float) -> None:
        """Advance the active background animation."""
        animation = self._active_animation
        if animation:
            animation.update(delta_seconds)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the active frame scaled and cropped to fill the display."""
        frame = self._active_animation.current_frame if self._active_animation else None
        if frame is None:
            surface.fill((12, 15, 24))
            return

        scaled = _scale_to_cover(frame, surface.get_size())
        rect = scaled.get_rect(center=surface.get_rect().center)
        surface.blit(scaled, rect)

        # A subtle overlay keeps text readable across bright animation frames.
        veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 92))
        surface.blit(veil, (0, 0))

    @property
    def _active_animation(self) -> FrameAnimation | None:
        if self._active_daypart is None:
            return None
        return self._animations.get(self._active_daypart)

    def _load_animation(self, daypart: Daypart) -> FrameAnimation:
        folder = self._assets_dir / daypart.value
        frames = [
            pygame.image.load(path).convert()
            for path in sorted(folder.glob("*.png"))
            if path.is_file()
        ]
        return FrameAnimation(frames, self._seconds_per_frame)


def _scale_to_cover(surface: pygame.Surface, target_size: tuple[int, int]) -> pygame.Surface:
    """Scale a surface so it covers the target without distortion."""
    target_width, target_height = target_size
    width, height = surface.get_size()
    scale = max(target_width / width, target_height / height)
    scaled_size = (round(width * scale), round(height * scale))
    return pygame.transform.smoothscale(surface, scaled_size)
