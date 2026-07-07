"""Static wallpaper and frosted-panel backdrop rendering."""

from __future__ import annotations

from pathlib import Path

import pygame

from homegirl.theme import Theme

BlurCacheKey = tuple[str, tuple[int, int], int]
WashCacheKey = tuple[str, tuple[int, int], tuple[int, int, int], int, int, int]


class AmbientBackground:
    """Load, scale, and cache static wallpaper photos for full-screen backdrops."""

    # quality_scale is accepted (and set via Settings.animation_quality_scale)
    # for forward compatibility with quality tiering, but static wallpapers
    # don't have a quality knob to apply it to yet.
    def __init__(self, quality_scale: float = 0.5) -> None:  # pylint: disable=unused-argument
        self._assets_dir = Path(__file__).resolve().parent.parent / "assets" / "backgrounds"
        self._source_cache: dict[str, pygame.Surface] = {}
        self._scaled_cache: dict[tuple[str, tuple[int, int]], pygame.Surface] = {}
        self._blurred_cache: dict[BlurCacheKey, pygame.Surface] = {}
        self._wash_cache: dict[WashCacheKey, pygame.Surface] = {}
        self._gradient_cache: dict[tuple[tuple[int, int, int], int, int, tuple[int, int]], pygame.Surface] = {}

    def update(self, delta_seconds: float) -> None:
        """Keep the existing app loop contract; static wallpapers do not animate."""

    def draw(self, surface: pygame.Surface, theme: Theme) -> None:
        """Draw the ambient wallpaper with its wash gradient for a daypart theme."""
        self.draw_washed(
            surface,
            theme.background_image,
            theme.wash_color,
            theme.wash_top_alpha,
            theme.wash_bottom_alpha,
        )

    def draw_washed(
        self,
        surface: pygame.Surface,
        filename: str,
        wash_color: tuple[int, int, int],
        top_alpha: int,
        bottom_alpha: int,
        blur_radius: int = 0,
    ) -> None:
        """Draw a wallpaper photo, optionally frosted, under a vertical color wash."""
        size = surface.get_size()
        composited = self._composited(filename, size, wash_color, top_alpha, bottom_alpha, blur_radius)
        surface.blit(composited, (0, 0))

    def _composited(
        self,
        filename: str,
        size: tuple[int, int],
        wash_color: tuple[int, int, int],
        top_alpha: int,
        bottom_alpha: int,
        blur_radius: int,
    ) -> pygame.Surface:
        key: WashCacheKey = (filename, size, wash_color, top_alpha, bottom_alpha, blur_radius)
        cached = self._wash_cache.get(key)
        if cached is not None:
            return cached

        base = self._scale_to_cover(self._load(filename), size, filename)
        if blur_radius > 0:
            base = self._blurred(base, filename, size, blur_radius)

        result = base.copy()
        result.blit(self._gradient(wash_color, top_alpha, bottom_alpha, size), (0, 0))
        self._wash_cache[key] = result
        return result

    def _blurred(
        self,
        image: pygame.Surface,
        filename: str,
        size: tuple[int, int],
        blur_radius: int,
    ) -> pygame.Surface:
        key: BlurCacheKey = (filename, size, blur_radius)
        cached = self._blurred_cache.get(key)
        if cached is not None:
            return cached

        width, height = size
        small_size = (max(1, width // blur_radius), max(1, height // blur_radius))
        small = pygame.transform.smoothscale(image, small_size)
        blurred = pygame.transform.smoothscale(small, size)
        self._blurred_cache[key] = blurred
        return blurred

    def _gradient(
        self,
        color: tuple[int, int, int],
        top_alpha: int,
        bottom_alpha: int,
        size: tuple[int, int],
    ) -> pygame.Surface:
        key = (color, top_alpha, bottom_alpha, size)
        cached = self._gradient_cache.get(key)
        if cached is not None:
            return cached

        height = max(1, size[1])
        column = pygame.Surface((1, height), pygame.SRCALPHA)
        for y in range(height):
            progress = y / max(1, height - 1)
            alpha = round(top_alpha + (bottom_alpha - top_alpha) * progress)
            column.set_at((0, y), (*color, alpha))

        gradient = pygame.transform.scale(column, size)
        self._gradient_cache[key] = gradient
        return gradient

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
        scaled = pygame.transform.smoothscale(image, scaled_size)

        crop_x = (scaled_size[0] - target_width) // 2
        crop_y = (scaled_size[1] - target_height) // 2
        wallpaper = pygame.Surface(target_size)
        wallpaper.blit(scaled, (0, 0), pygame.Rect(crop_x, crop_y, target_width, target_height))

        self._scaled_cache[(cache_key, target_size)] = wallpaper
        return wallpaper
