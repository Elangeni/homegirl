"""Static ambient wallpaper renderer."""

from __future__ import annotations

from pathlib import Path

import pygame

from homegirl.theme import Theme


class AmbientBackground:
    """Draw the static wallpaper for the active time-of-day theme."""

    def __init__(self, quality_scale: float = 0.5) -> None:
        self._assets_dir = Path(__file__).resolve().parent.parent / "assets" / "backgrounds"
        self._source_cache: dict[str, pygame.Surface] = {}
        self._scaled_cache: dict[tuple[str, tuple[int, int]], pygame.Surface] = {}

    def update(self, delta_seconds: float) -> None:
        """Keep the existing app loop contract; static wallpapers do not animate."""

    def draw(self, surface: pygame.Surface, theme: Theme) -> None:
        """Draw the theme wallpaper scaled and cropped to fill the screen."""
        image = self._load(theme.background_image)
        wallpaper = self._scale_to_cover(image, surface.get_size(), theme.background_image)
        rect = wallpaper.get_rect(center=surface.get_rect().center)
        surface.blit(wallpaper, rect)

    def _load(self, filename: str) -> pygame.Surface:
        cached = self._source_cache.get(filename)
        if cached is not None:
            return cached

        path = self._assets_dir / filename
        image = pygame.image.load(path)
        try:
            image = image.convert()
        except pygame.error:
            pass

        self._source_cache[filename] = image
        return image

    def _scale_to_cover(
        self,
        image: pygame.Surface,
        target_size: tuple[int, int],
        cache_key: str,
    ) -> pygame.Surface:
        cached = self._scaled_cache.get((cache_key, target_size))
        if cached is not None:
            return cached

        target_width, target_height = target_size
        width, height = image.get_size()
        scale = max(target_width / width, target_height / height)
        scaled_size = (round(width * scale), round(height * scale))
        wallpaper = pygame.transform.smoothscale(image, scaled_size)
        self._scaled_cache[(cache_key, target_size)] = wallpaper
        return wallpaper
