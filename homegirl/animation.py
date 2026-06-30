"""Procedural ambient lava-lamp background."""

from __future__ import annotations

import math

import pygame

from homegirl.theme import BlobSpec, Theme


class AmbientBackground:
    """Draw a calm generated background with slow translucent blobs.

    The animation is intentionally procedural now: no PNG sequence is required
    for the product shell, and all motion is deterministic so it loops softly
    without sudden jumps.
    """

    def __init__(self, quality_scale: float = 0.5) -> None:
        self._time = 0.0
        self._quality_scale = quality_scale
        self._gradient_cache: dict[tuple[tuple[int, int], tuple[int, int, int], tuple[int, int, int]], pygame.Surface] = {}

    def update(self, delta_seconds: float) -> None:
        """Advance animation time independently from clock updates."""
        self._time = (self._time + delta_seconds) % 3600.0

    def draw(self, surface: pygame.Surface, theme: Theme) -> None:
        """Render the active ambient theme onto the display surface."""
        surface.blit(self._gradient(surface.get_size(), theme), (0, 0))

        size = surface.get_size()
        blob_layer = pygame.Surface(size, pygame.SRCALPHA)
        for blob in theme.blobs:
            self._draw_blob(blob_layer, blob)

        # Smoothscale creates a gentle blur/glow feeling without an expensive
        # per-pixel blur pass, which keeps this Raspberry Pi friendly.
        small_size = (
            max(8, round(size[0] * self._quality_scale)),
            max(8, round(size[1] * self._quality_scale)),
        )
        soft = pygame.transform.smoothscale(blob_layer, small_size)
        soft = pygame.transform.smoothscale(soft, size)
        surface.blit(soft, (0, 0))

        self._draw_vignette(surface, theme)
        self._draw_center_readability_panel(surface, theme)

    def _draw_blob(self, layer: pygame.Surface, blob: BlobSpec) -> None:
        width, height = layer.get_size()
        orbit = self._time * blob.speed * math.tau
        cx = width * (blob.x_origin + blob.x_motion * math.sin(orbit + blob.phase))
        cy = height * (blob.y_origin + blob.y_motion * math.cos(orbit * 0.83 + blob.phase))
        radius = min(width, height) * blob.radius_scale
        radius *= 1.0 + 0.08 * math.sin(orbit * 0.71 + blob.phase)

        # Draw several offset glows per blob so the shape feels organic while
        # still using cheap circles instead of a costly pixel shader.
        offsets = ((0.0, 0.0, 1.0), (0.34, -0.18, 0.72), (-0.28, 0.24, 0.66))
        for ox, oy, scale in offsets:
            self._draw_glow_circle(
                layer,
                blob,
                cx + radius * ox,
                cy + radius * oy,
                radius * scale,
                0.78 if scale < 1 else 1.0,
            )

    def _draw_glow_circle(
        self,
        layer: pygame.Surface,
        blob: BlobSpec,
        cx: float,
        cy: float,
        radius: float,
        alpha_scale: float,
    ) -> None:
        for step in range(16, 0, -1):
            fraction = step / 16
            alpha = round(blob.alpha * alpha_scale * (1 - fraction) ** 1.65)
            current_radius = round(radius * fraction)
            if alpha <= 0 or current_radius <= 0:
                continue
            pygame.draw.circle(
                layer,
                (*blob.color, alpha),
                (round(cx), round(cy)),
                current_radius,
            )

    def _gradient(self, size: tuple[int, int], theme: Theme) -> pygame.Surface:
        key = (size, theme.gradient_top, theme.gradient_bottom)
        cached = self._gradient_cache.get(key)
        if cached is not None:
            return cached

        width, height = size
        gradient = pygame.Surface(size)
        for y in range(height):
            t = y / max(1, height - 1)
            color = _mix(theme.gradient_top, theme.gradient_bottom, t)
            pygame.draw.line(gradient, color, (0, y), (width, y))

        self._gradient_cache[key] = gradient
        return gradient

    def _draw_vignette(self, surface: pygame.Surface, theme: Theme) -> None:
        width, height = surface.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        edge = round(max(width, height) * 0.08)
        pygame.draw.rect(overlay, (*theme.vignette[:3], theme.vignette[3]), (0, 0, width, edge))
        pygame.draw.rect(overlay, (*theme.vignette[:3], theme.vignette[3]), (0, height - edge, width, edge))
        pygame.draw.rect(overlay, (*theme.vignette[:3], theme.vignette[3]), (0, 0, edge, height))
        pygame.draw.rect(overlay, (*theme.vignette[:3], theme.vignette[3]), (width - edge, 0, edge, height))
        surface.blit(overlay, (0, 0))

    def _draw_center_readability_panel(self, surface: pygame.Surface, theme: Theme) -> None:
        width, height = surface.get_size()
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, round(width * 0.62), round(height * 0.64))
        rect.center = (width // 2, height // 2)

        for inset in range(0, 44, 4):
            current = rect.inflate(inset * 2, inset * 2)
            alpha = max(0, theme.panel_alpha - inset)
            pygame.draw.ellipse(panel, (0, 0, 0, alpha), current)

        surface.blit(panel, (0, 0))


def _mix(start: tuple[int, int, int], end: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    """Blend two RGB colors."""
    return tuple(round(start[index] * (1 - amount) + end[index] * amount) for index in range(3))
