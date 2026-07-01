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


@dataclass(frozen=True)
class AppViewModel:
    """Data required to render the unlocked app frame."""

    time_text: str
    labels: tuple[str, str, str, str]


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
            lines.append((f"Happy {model.national_day}", self._date_font, theme.text_muted, 0))

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


class AppUI:
    """Render the first unlocked app screen."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0

    def draw(self, surface: pygame.Surface, model: AppViewModel) -> None:
        """Draw a simple status bar and 2-by-2 app grid."""
        self._ensure_fonts(surface)

        surface.fill((242, 240, 234))
        width, height = surface.get_size()
        margin = self._spacing(36)
        status_height = self._spacing(78)
        line_color = (43, 43, 39)
        text_color = (34, 34, 30)

        time_image = _render_text(self._time_font, model.time_text, text_color)
        time_rect = time_image.get_rect(
            midleft=(margin, status_height // 2),
        )
        surface.blit(time_image, time_rect)

        pygame.draw.line(
            surface,
            line_color,
            (0, status_height),
            (width, status_height),
            max(1, self._spacing(2)),
        )

        grid_top = status_height + self._spacing(34)
        grid_rect = pygame.Rect(
            margin,
            grid_top,
            width - (margin * 2),
            height - grid_top - margin,
        )
        gap = self._spacing(18)
        cell_width = (grid_rect.width - gap) // 2
        cell_height = (grid_rect.height - gap) // 2

        for index, label in enumerate(model.labels):
            column = index % 2
            row = index // 2
            rect = pygame.Rect(
                grid_rect.left + column * (cell_width + gap),
                grid_rect.top + row * (cell_height + gap),
                cell_width,
                cell_height,
            )
            self._draw_tile(surface, rect, label)

    def _draw_tile(self, surface: pygame.Surface, rect: pygame.Rect, label: str) -> None:
        fill_color = (255, 255, 251)
        border_color = (52, 52, 46)
        text_color = (33, 33, 29)

        pygame.draw.rect(surface, fill_color, rect, border_radius=self._spacing(8))
        pygame.draw.rect(
            surface,
            border_color,
            rect,
            width=max(1, self._spacing(2)),
            border_radius=self._spacing(8),
        )

        label_image = _render_text(self._tile_font, label, text_color)
        label_rect = label_image.get_rect(center=rect.center)
        surface.blit(label_image, label_rect)

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return

        self._scale = max(
            0.82,
            min(surface.get_height() / 720, surface.get_width() / 1280),
        )
        self._time_font = _font(round(30 * self._scale), 500)
        self._tile_font = _font(round(56 * self._scale), 600)
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
