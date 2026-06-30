"""Composable ambient display UI primitives."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from homegirl.theme import Theme


@dataclass(frozen=True)
class AmbientViewModel:
    """Data required to render the current ambient frame."""

    greeting: str
    user_name: str
    time_text: str
    date_text: str
    national_day: str | None


class AmbientUI:
    """Render text that floats over the ambient wallpaper."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._greeting_font: pygame.font.Font
        self._name_font: pygame.font.Font
        self._time_font: pygame.font.Font
        self._date_font: pygame.font.Font
        self._small_font: pygame.font.Font

    def draw(self, surface: pygame.Surface, model: AmbientViewModel, theme: Theme) -> None:
        """Draw all ambient text centered on the display."""
        self._ensure_fonts(surface)

        lines: list[tuple[str, pygame.font.Font, tuple[int, int, int], int, int]] = [
            (model.greeting, self._greeting_font, theme.text_secondary, 230, 30),
            (f"Hello, {model.user_name}", self._name_font, theme.text_primary, 238, 36),
            (model.time_text, self._time_font, theme.text_primary, 236, 30),
            (model.date_text, self._date_font, theme.text_secondary, 220, 28),
        ]
        if model.national_day:
            lines.append((f"Happy {model.national_day}", self._small_font, theme.text_secondary, 205, 0))

        rendered = [
            (_render_text(font, text, color, alpha), spacing)
            for text, font, color, alpha, spacing in lines
        ]
        content_height = sum(image.get_height() for image, _ in rendered)
        content_height += sum(spacing for _, spacing in rendered[:-1])
        y = (surface.get_height() - content_height) // 2
        center_x = surface.get_width() // 2

        for image, spacing in rendered:
            rect = image.get_rect(center=(center_x, y + image.get_height() // 2))
            _draw_text_shadow(surface, image, rect)
            y += image.get_height() + spacing

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        """Size fonts from display height once pygame knows the screen size."""
        if self._fonts_ready:
            return

        base = min(surface.get_width(), surface.get_height())
        self._greeting_font = _font(max(24, base // 30))
        self._name_font = _font(max(54, base // 10), bold=True)
        self._time_font = _font(max(42, base // 13), bold=True)
        self._date_font = _font(max(24, base // 30))
        self._small_font = _font(max(20, base // 36))
        self._fonts_ready = True


def _draw_text_shadow(surface: pygame.Surface, image: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a small text-only shadow for readability over bright wallpaper."""
    shadow = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 0))
    shadow.blit(image, (0, 0))
    shadow.fill((0, 0, 0, 88), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(shadow, rect.move(1, 2))
    surface.blit(image, rect)


def _render_text(
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    alpha: int,
) -> pygame.Surface:
    """Render text with gentle opacity so it belongs to the wallpaper."""
    image = font.render(text, True, color).convert_alpha()
    image.set_alpha(alpha)
    return image


def _font(size: int, *, bold: bool = False) -> pygame.font.Font:
    """Choose a clean system font with broad platform fallback."""
    candidates = ("SF Pro Display", "Helvetica Neue", "Avenir Next", "DejaVu Sans", "Arial")
    return pygame.font.SysFont(candidates, size, bold=bold)
