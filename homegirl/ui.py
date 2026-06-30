"""Composable dashboard UI primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pygame


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

    def draw(self, surface: pygame.Surface, model: DashboardViewModel) -> None:
        """Draw all dashboard text centered on the display."""
        self._ensure_fonts(surface)

        lines: list[tuple[str, pygame.font.Font, tuple[int, int, int], int]] = [
            (model.greeting, self._greeting_font, (238, 239, 232), 22),
            (f"Hello, {model.user_name}", self._name_font, (255, 255, 250), 34),
            (model.time_text, self._time_font, (255, 255, 250), 18),
            (model.date_text, self._date_font, (232, 234, 229), 24),
        ]
        if model.national_day:
            lines.append((f"Happy {model.national_day}!", self._small_font, (245, 221, 171), 0))

        rendered = [
            (font.render(text, True, color), spacing)
            for text, font, color, spacing in lines
        ]
        content_height = sum(image.get_height() + spacing for image, spacing in rendered)
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

        height = surface.get_height()
        self._greeting_font = pygame.font.SysFont("arial", max(38, height // 16))
        self._name_font = pygame.font.SysFont("arial", max(64, height // 10), bold=True)
        self._time_font = pygame.font.SysFont("arial", max(54, height // 12), bold=True)
        self._date_font = pygame.font.SysFont("arial", max(30, height // 22))
        self._small_font = pygame.font.SysFont("arial", max(24, height // 30))
        self._fonts_ready = True


def _draw_text_shadow(surface: pygame.Surface, image: pygame.Surface, rect: pygame.Rect) -> None:
    """Draw a soft shadow behind rendered text for contrast."""
    shadow = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 0))
    shadow.blit(image, (0, 0))
    shadow.fill((0, 0, 0, 130), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(shadow, rect.move(3, 4))
    surface.blit(image, rect)
