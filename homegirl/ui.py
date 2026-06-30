"""Composable dashboard UI primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pygame

from homegirl.theme import Theme


@dataclass(frozen=True)
class DashboardViewModel:
    """Data required to render the current dashboard frame."""

    greeting: str
    user_name: str
    time_text: str
    date_text: str
    national_day: str | None


class Widget(Protocol):
    """Future widgets can implement this small rendering contract."""

    def draw(self, surface: pygame.Surface, center_x: int, y: int) -> int:
        """Draw the widget and return the next y position."""


class DashboardUI:
    """Render the MVP dashboard while leaving room for future widgets."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._greeting_font: pygame.font.Font
        self._name_font: pygame.font.Font
        self._time_font: pygame.font.Font
        self._date_font: pygame.font.Font
        self._small_font: pygame.font.Font

    def draw(self, surface: pygame.Surface, model: DashboardViewModel, theme: Theme) -> None:
        """Draw all dashboard text centered on the display."""
        self._ensure_fonts(surface)

        lines: list[tuple[str, pygame.font.Font, tuple[int, int, int], int]] = [
            (model.greeting, self._greeting_font, theme.text_secondary, 20),
            (f"Hello, {model.user_name}", self._name_font, theme.text_primary, 26),
            (model.time_text, self._time_font, theme.text_primary, 14),
            (model.date_text, self._date_font, theme.text_secondary, 22),
        ]
        if model.national_day:
            lines.append((f"Happy {model.national_day}!", self._small_font, theme.text_primary, 0))

        rendered = [
            (font.render(text, True, color), spacing)
            for text, font, color, spacing in lines
        ]
        content_height = sum(image.get_height() for image, _ in rendered)
        content_height += sum(spacing for _, spacing in rendered[:-1])
        y = (surface.get_height() - content_height) // 2
        center_x = surface.get_width() // 2

        for index, (image, spacing) in enumerate(rendered):
            rect = image.get_rect(center=(center_x, y + image.get_height() // 2))
            _draw_text_shadow(surface, image, rect)
            y += image.get_height() + spacing
            if index in {1, 3} and index < len(rendered) - 1:
                _draw_rule(surface, center_x, y - spacing // 2, theme.text_accent)

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        """Size fonts from display height once pygame knows the screen size."""
        if self._fonts_ready:
            return

        base = min(surface.get_width(), surface.get_height())
        self._greeting_font = _font(max(28, base // 22))
        self._name_font = _font(max(58, base // 9), bold=True)
        self._time_font = _font(max(48, base // 11), bold=True)
        self._date_font = _font(max(28, base // 23))
        self._small_font = _font(max(24, base // 25), bold=True)
        self._fonts_ready = True


def _draw_text_shadow(surface: pygame.Surface, image: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a soft shadow behind rendered text for contrast."""
    shadow = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 0))
    shadow.blit(image, (0, 0))
    shadow.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(shadow, rect.move(2, 3))
    surface.blit(image, rect)


def _draw_rule(
    surface: pygame.Surface,
    center_x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    """Draw a restrained divider like the reference smart-display layout."""
    rule = pygame.Surface((76, 2), pygame.SRCALPHA)
    pygame.draw.line(rule, (*color, 118), (0, 0), (76, 0), 2)
    surface.blit(rule, rule.get_rect(center=(center_x, y)))


def _font(size: int, *, bold: bool = False) -> pygame.font.Font:
    """Choose a clean system font with broad platform fallback."""
    candidates = ("SF Pro Display", "Helvetica Neue", "Avenir Next", "DejaVu Sans", "Arial")
    return pygame.font.SysFont(candidates, size, bold=bold)
