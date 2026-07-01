"""Ambient floating typography."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygame

from homegirl.theme import Theme


FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONTS = {
    100: "ElmsSans-Thin.ttf",
    200: "ElmsSans-ExtraLight.ttf",
    300: "ElmsSans-Light.ttf",
    400: "ElmsSans-Regular.ttf",
    500: "ElmsSans-Medium.ttf",
    600: "ElmsSans-SemiBold.ttf",
    700: "ElmsSans-Bold.ttf",
    800: "ElmsSans-ExtraBold.ttf",
    900: "ElmsSans-Black.ttf",
}


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
        self._scale = 1.0

    def draw(self, surface: pygame.Surface, model: AmbientViewModel, theme: Theme) -> None:
        """Draw ambient text with a left-aligned art-frame layout."""
        self._ensure_fonts(surface)

        lines: list[tuple[str, pygame.font.Font, tuple[int, int, int], int]] = [
            (model.greeting, self._greeting_font, theme.text_secondary, self._spacing(42)),
            (f"Hello, {model.user_name}", self._name_font, theme.text_primary, self._spacing(62)),
            (model.time_text, self._time_font, theme.time_color, self._spacing(52)),
            (model.date_text, self._date_font, theme.text_secondary, self._spacing(28)),
        ]

        if model.national_day:
            lines.append((f"Happy {model.national_day}", self._small_font, theme.text_muted, 0))

        rendered = [
            (_render_text(font, text, color), spacing)
            for text, font, color, spacing in lines
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
        if self._fonts_ready:
            return

        self._scale = max(
            0.82,
            min(surface.get_height() / 720, surface.get_width() / 1280),
        )

        self._greeting_font = _font(round(29 * self._scale), 200)
        self._name_font = _font(round(77 * self._scale), 700)
        self._time_font = _font(round(72 * self._scale), 400)
        self._date_font = _font(round(34 * self._scale), 400)
        self._small_font = _font(round(24 * self._scale), 300)

        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


def _render_text(
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
) -> pygame.Surface:
    """Render crisp ambient text."""
    return font.render(text, True, color)


def _font(size: int, weight: int = 400) -> pygame.font.Font:
    return pygame.font.Font(FONT_DIR / FONTS[weight], size)