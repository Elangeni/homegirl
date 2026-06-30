"""Ambient floating typography."""

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
        """Draw ambient text with a left-aligned art-frame layout."""
        self._ensure_fonts(surface)

        lines: list[tuple[str, pygame.font.Font, tuple[int, int, int], int, int]] = [
            (model.greeting, self._greeting_font, theme.text_secondary, 196, self._spacing(42)),
            (f"Hello, {model.user_name}", self._name_font, theme.text_primary, 244, self._spacing(62)),
            (model.time_text, self._time_font, theme.time_color, 230, self._spacing(52)),
            (model.date_text, self._date_font, theme.text_secondary, 218, self._spacing(28)),
        ]
        if model.national_day:
            lines.append((f"Happy {model.national_day}", self._small_font, theme.text_muted, 140, 0))

        rendered = [
            (_render_text(font, text, color, alpha), spacing)
            for text, font, color, alpha, spacing in lines
        ]
        content_height = sum(image.get_height() for image, _ in rendered)
        content_height += sum(spacing for _, spacing in rendered[:-1])
        margin_x = max(116, round(surface.get_width() * 0.109))
        margin_y = max(64, round(surface.get_height() * 0.11))
        y = max(margin_y, (surface.get_height() - content_height) // 2)

        for image, spacing in rendered:
            rect = image.get_rect(topleft=(margin_x, y))
            surface.blit(image, rect)
            y += image.get_height() + spacing

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        """Size fonts from display height once pygame knows the screen size."""
        if self._fonts_ready:
            return

        scale = max(0.82, min(surface.get_height() / 720, surface.get_width() / 1280))
        self._greeting_font = _font(round(29 * scale))
        self._name_font = _font(round(77 * scale), bold=True)
        self._time_font = _font(round(72 * scale))
        self._date_font = _font(round(34 * scale))
        self._small_font = _font(round(24 * scale))
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)

    @property
    def _scale(self) -> float:
        if not self._fonts_ready:
            return 1.0
        return self._name_font.get_height() / 98


def _render_text(
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    alpha: int,
) -> pygame.Surface:
    """Render text with gentle opacity so it belongs to the wallpaper."""
    image = font.render(text, True, color)
    image.set_alpha(alpha)
    return image


def _font(size: int, *, bold: bool = False) -> pygame.font.Font:
    """Choose a clean system font with broad platform fallback."""
    candidates = ("Inter", "SF Pro Display", "Manrope", "IBM Plex Sans", "Noto Sans", "Helvetica Neue", "Arial")
    return pygame.font.SysFont(candidates, size, bold=bold)
