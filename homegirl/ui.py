"""Ambient floating typography and app-mode screen rendering."""

from __future__ import annotations

import calendar as calendar_module
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pygame

from homegirl import svg_icon, weathericons
from homegirl.animation import AmbientBackground
from homegirl.models.schedule import ScheduleEvent
from homegirl.models.weather import HourlyForecast, WeatherData
from homegirl.schedule_insight import FreeTimeGap, describe_free_time_gap
from homegirl.theme import (
    CELEBRATION_BACKGROUND_IMAGE,
    CELEBRATION_TEXT_COLOR,
    CELEBRATION_WASH_BOTTOM_ALPHA,
    CELEBRATION_WASH_COLOR,
    CELEBRATION_WASH_TOP_ALPHA,
    DARK_BACKGROUND_IMAGE,
    DARK_INK,
    DARK_MUTED,
    DARK_WASH_BOTTOM_ALPHA,
    DARK_WASH_COLOR,
    DARK_WASH_TOP_ALPHA,
    DETAIL_BACKGROUND_IMAGE,
    DETAIL_BLUR_RADIUS,
    DETAIL_WASH_ALPHA,
    DETAIL_WASH_COLOR,
    HOME_BACKGROUND_IMAGE,
    HOME_WASH_BOTTOM_ALPHA,
    HOME_WASH_COLOR,
    HOME_WASH_TOP_ALPHA,
    INK,
    SLATE_MUTED,
    Theme,
)


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

MARGIN_X = 140
PANEL_PAD_TOP = 40
PANEL_PAD_BOTTOM = 80

ALPHA_FULL = 255
ALPHA_STRONG = 217
ALPHA_SECONDARY = 153
ALPHA_MUTED = 102
ALPHA_FAINT = 77
ALPHA_GHOST = 38


@dataclass(frozen=True)
class AmbientViewModel:
    """Data required to render the current ambient frame."""

    greeting: str
    user_name: str
    time_text: str
    date_text: str
    national_day: str | None
    weather: WeatherData


@dataclass(frozen=True)
class AppViewModel:
    """Data required to render the home screen's three summary cards."""

    time_text: str
    date_text: str
    today_text: str
    weather_text: str
    calendar_text: str


@dataclass(frozen=True)
class WeatherViewModel:
    """Data required to render the weather detail screen."""

    time_text: str
    weather: WeatherData
    headline: str | None
    advice: str | None


@dataclass(frozen=True)
class CalendarViewModel:
    """Data required to render the calendar detail screen."""

    time_text: str
    headline: str | None
    free_hint: str | None
    events: tuple[ScheduleEvent, ...]
    free_gap: FreeTimeGap | None


@dataclass(frozen=True)
class ReflectionViewModel:
    """Data required to render the weekly reflection screen."""

    time_text: str
    prompts: tuple[str, ...]


@dataclass(frozen=True)
class FullCalendarViewModel:
    """Data required to render the full month calendar screen."""

    time_text: str
    today: date
    events_by_day: dict[date, tuple[ScheduleEvent, ...]]


@dataclass(frozen=True)
class DayDetailViewModel:
    """Data required to render a single day's agenda screen."""

    month_label: str
    weekday_label: str
    date_label: str
    events: tuple[ScheduleEvent, ...]


class AmbientUI:
    """Render text and the weather pill that float over the ambient wallpaper."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0
        self.home_rect: pygame.Rect | None = None

    @property
    def scale(self) -> float:
        """Return the current display scale factor, for callers like draw_weather_pill."""
        return self._scale

    def draw(self, surface: pygame.Surface, model: AmbientViewModel, theme: Theme) -> None:
        """Draw ambient text with a left-aligned art-frame layout."""
        self._ensure_fonts(surface)

        lines: list[tuple[str, pygame.font.Font, tuple[int, int, int], int, int]] = [
            (model.greeting.upper(), self._label_font, theme.text_color, ALPHA_STRONG, self._spacing(4)),
            (f"Hello, {model.user_name}", self._name_font, theme.text_color, ALPHA_FULL, self._spacing(16)),
        ]

        rendered_head = [
            (_render_text_alpha(font, text, color, alpha), spacing)
            for text, font, color, alpha, spacing in lines
        ]

        time_image = _render_text(self._time_font, model.time_text, theme.time_color)
        date_image = _render_text_alpha(self._date_font, model.date_text, theme.text_color, ALPHA_SECONDARY)
        rendered_time = [(time_image, self._spacing(2)), (date_image, 0)]

        rendered = rendered_head + rendered_time
        if model.national_day:
            national_image = _render_text_alpha(
                self._national_font, f"Happy {model.national_day}", theme.text_color, ALPHA_MUTED
            )
            rendered[-1] = (rendered[-1][0], self._spacing(12))
            rendered.append((national_image, 0))

        content_height = sum(image.get_height() for image, _ in rendered)
        content_height += sum(spacing for _, spacing in rendered[:-1])

        margin_x = self._spacing(MARGIN_X)
        y = max(self._spacing(64), (surface.get_height() - content_height) // 2)

        for image, spacing in rendered:
            surface.blit(image, (margin_x, y))
            y += image.get_height() + spacing

        draw_weather_pill(surface, self, model.weather, theme)
        self._draw_home_button(surface, theme)

    def _draw_home_button(self, surface: pygame.Surface, theme: Theme) -> None:
        size = self._spacing(56)
        margin = self._spacing(24)
        top = self._spacing(40)
        rect = pygame.Rect(margin, top, size, size)

        _draw_glass_panel(surface, rect, size // 2, theme.pill_bg, theme.pill_border)
        icon_rect = rect.inflate(-round(size * 0.44), -round(size * 0.44))
        svg_icon.draw_icon(surface, icon_rect, "house", theme.pill_text)
        self.home_rect = rect

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return

        self._scale = _scale_for(surface)
        self._label_font = _font(round(15 * self._scale), 200)
        self._name_font = _font(round(84 * self._scale), 200)
        self._time_font = _font(round(144 * self._scale), 400)
        self._date_font = _font(round(20 * self._scale), 300)
        self._national_font = _font(round(22 * self._scale), 300)
        self.pill_label_font = _font(round(11 * self._scale), 500)
        self.pill_temp_font = _font(round(16 * self._scale), 600)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


class AppUI:
    """Render the home screen: clock header plus Today / Weather / Calendar cards."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0
        self.today_rect: pygame.Rect | None = None
        self.weather_rect: pygame.Rect | None = None
        self.calendar_rect: pygame.Rect | None = None

    def draw(self, surface: pygame.Surface, model: AppViewModel, background: AmbientBackground) -> None:
        """Draw the frosted home background, header clock, and three summary cards."""
        self._ensure_fonts(surface)

        background.draw_washed(
            surface, HOME_BACKGROUND_IMAGE, HOME_WASH_COLOR, HOME_WASH_TOP_ALPHA, HOME_WASH_BOTTOM_ALPHA
        )

        width, height = surface.get_size()
        pad_top = self._spacing(PANEL_PAD_TOP)
        pad_bottom = self._spacing(PANEL_PAD_BOTTOM)
        margin_x = self._spacing(MARGIN_X)
        gap = self._spacing(48)
        row_height = self._spacing(320)

        time_image = _render_text(self._time_font, model.time_text, INK)
        date_image = _render_text_alpha(self._date_font, model.date_text, INK, ALPHA_SECONDARY)
        header_height = time_image.get_height() + self._spacing(4) + date_image.get_height()

        content_height = header_height + gap + row_height
        available = height - pad_top - pad_bottom
        top = pad_top + max(0, (available - content_height) // 2)

        surface.blit(time_image, time_image.get_rect(midtop=(width // 2, top)).topleft)
        surface.blit(
            date_image,
            date_image.get_rect(midtop=(width // 2, top + time_image.get_height() + self._spacing(4))).topleft,
        )

        row_top = top + header_height + gap
        card_gap = self._spacing(24)
        card_width = (width - margin_x * 2 - card_gap * 2) // 3

        self.today_rect = pygame.Rect(margin_x, row_top, card_width, row_height)
        self.weather_rect = pygame.Rect(self.today_rect.right + card_gap, row_top, card_width, row_height)
        self.calendar_rect = pygame.Rect(self.weather_rect.right + card_gap, row_top, card_width, row_height)

        self._draw_card(surface, self.today_rect, "Today", model.today_text)
        self._draw_card(surface, self.weather_rect, "Weather", model.weather_text)
        self._draw_card(surface, self.calendar_rect, "Calendar", model.calendar_text)

    def _draw_card(self, surface: pygame.Surface, rect: pygame.Rect, title: str, body: str) -> None:
        radius = self._spacing(32)
        _draw_glass_panel(surface, rect, radius, (248, 250, 252, 195), (226, 232, 240, 102), blur_divisor=32)

        pad = self._spacing(32)
        left = rect.left + pad
        top = rect.top + pad
        max_width = rect.width - pad * 2

        title_image = _render_text_alpha(self._title_font, title.upper(), INK, ALPHA_SECONDARY)
        surface.blit(title_image, (left, top))

        body_top = top + title_image.get_height() + self._spacing(16)
        for line in _wrap_text(self._body_font, body, max_width):
            line_image = _render_text(self._body_font, line, INK)
            surface.blit(line_image, (left, body_top))
            body_top += line_image.get_height() + self._spacing(4)

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return
        self._scale = _scale_for(surface)
        self._time_font = _font(round(60 * self._scale), 300)
        self._date_font = _font(round(18 * self._scale), 300)
        self._title_font = _font(round(14 * self._scale), 600)
        self._body_font = _font(round(22 * self._scale), 400)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


class WeatherUI:
    """Render the weather detail screen reached from the home screen."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0
        self.dismiss_rect: pygame.Rect | None = None

    def draw(self, surface: pygame.Surface, model: WeatherViewModel, background: AmbientBackground) -> None:
        """Draw the current reading, situational copy, and hourly strip."""
        self._ensure_fonts(surface)
        _draw_detail_backdrop(surface, background)

        width, height = surface.get_size()
        margin_x = self._spacing(MARGIN_X)
        top = self._spacing(PANEL_PAD_TOP)

        time_image = _render_text(self._time_font, model.time_text, INK)
        surface.blit(time_image, (margin_x, top))
        self.dismiss_rect = _draw_dismiss_button(surface, width - margin_x, top, self._spacing(32))

        if not model.weather.is_available:
            unavailable = _render_text_alpha(self._advice_font, "Weather unavailable", INK, ALPHA_MUTED)
            surface.blit(unavailable, (margin_x, top + self._spacing(160)))
            return

        y = top + self._spacing(90)
        if model.headline:
            max_text_width = round(width * 0.47)
            for line in _wrap_text(self._headline_font, model.headline, max_text_width):
                line_image = _render_text(self._headline_font, line, INK)
                surface.blit(line_image, (margin_x, y))
                y += line_image.get_height() + self._spacing(4)

        y += self._spacing(40)
        temp_image = _render_text(self._temp_font, _format_temp_full(model.weather.current_temp), INK)
        surface.blit(temp_image, (margin_x, y))
        temp_bottom = y + temp_image.get_height()

        detail_x = margin_x + temp_image.get_width() + self._spacing(32)
        detail_y = y + self._spacing(8)
        if model.weather.condition:
            condition_image = _render_text_alpha(
                self._condition_font, model.weather.condition.upper(), INK, ALPHA_MUTED
            )
            surface.blit(condition_image, (detail_x, detail_y))
            detail_y += condition_image.get_height() + self._spacing(4)

        if model.advice:
            advice_image = _render_text_alpha(self._advice_font, model.advice, INK, ALPHA_SECONDARY)
            surface.blit(advice_image, (detail_x, detail_y))

        forecast_bottom = height - self._spacing(PANEL_PAD_BOTTOM)
        forecast_top = max(temp_bottom + self._spacing(64), forecast_bottom - self._spacing(150))
        if model.weather.hourly:
            self._draw_hourly_strip(
                surface,
                model.weather.hourly,
                pygame.Rect(margin_x, forecast_top, width - margin_x * 2, forecast_bottom - forecast_top),
            )

    def _draw_hourly_strip(
        self,
        surface: pygame.Surface,
        hourly: tuple[HourlyForecast, ...],
        rect: pygame.Rect,
    ) -> None:
        line = pygame.Surface((rect.width, 1), pygame.SRCALPHA)
        line.fill((*INK, ALPHA_GHOST))
        surface.blit(line, (rect.left, rect.top))

        slot_top = rect.top + self._spacing(24)
        slot_width = rect.width // len(hourly)
        icon_size = self._spacing(24)

        for index, hour in enumerate(hourly):
            slot_center_x = rect.left + slot_width * index + slot_width // 2

            hour_label = _render_text_alpha(self._hour_font, _short_hour_label(hour.time), INK, ALPHA_SECONDARY)
            surface.blit(hour_label, hour_label.get_rect(midtop=(slot_center_x, slot_top)))

            icon_top = slot_top + hour_label.get_height() + self._spacing(12)
            icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
            icon_rect.center = (slot_center_x, icon_top + icon_size // 2)
            weathericons.draw_icon(surface, icon_rect, hour.condition, False, INK)

            temp_top = icon_rect.bottom + self._spacing(12)
            temp_label = _render_text(self._hour_temp_font, _format_temp(hour.temp), INK)
            surface.blit(temp_label, temp_label.get_rect(midtop=(slot_center_x, temp_top)))

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return
        self._scale = _scale_for(surface)
        self._time_font = _font(round(16 * self._scale), 500)
        self._headline_font = _font(round(32 * self._scale), 500)
        self._temp_font = _font(round(120 * self._scale), 700)
        self._condition_font = _font(round(14 * self._scale), 300)
        self._advice_font = _font(round(16 * self._scale), 300)
        self._hour_font = _font(round(12 * self._scale), 500)
        self._hour_temp_font = _font(round(18 * self._scale), 600)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


class CalendarUI:
    """Render the calendar detail screen: headline, free-time hint, and a timeline."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0
        self.dismiss_rect: pygame.Rect | None = None
        self.full_calendar_rect: pygame.Rect | None = None

    def draw(self, surface: pygame.Surface, model: CalendarViewModel, background: AmbientBackground) -> None:
        """Draw the lead sentence, free-time hint, and today's event timeline."""
        self._ensure_fonts(surface)
        _draw_detail_backdrop(surface, background)

        width, height = surface.get_size()
        margin_x = self._spacing(MARGIN_X)
        top = self._spacing(PANEL_PAD_TOP)

        time_image = _render_text(self._time_font, model.time_text, INK)
        surface.blit(time_image, (margin_x, top))
        self.dismiss_rect = _draw_dismiss_button(surface, width - margin_x, top, self._spacing(32))

        y = top + self._spacing(90)
        if model.headline:
            max_width = width - margin_x * 2
            for line in _wrap_text(self._headline_font, model.headline, max_width):
                line_image = _render_text(self._headline_font, line, INK)
                surface.blit(line_image, (margin_x, y))
                y += line_image.get_height() + self._spacing(4)

        if model.free_hint:
            y += self._spacing(4)
            hint_image = _render_text_alpha(self._hint_font, model.free_hint, INK, ALPHA_SECONDARY)
            surface.blit(hint_image, (margin_x, y))
            y += hint_image.get_height()

        timeline_top = y + self._spacing(48)
        timeline_bottom = height - self._spacing(PANEL_PAD_BOTTOM) - self._spacing(48)
        timeline_rect = pygame.Rect(
            margin_x, timeline_top, width - margin_x * 2, max(0, timeline_bottom - timeline_top)
        )
        self._draw_timeline(surface, model, timeline_rect)

        button_y = height - self._spacing(PANEL_PAD_BOTTOM)
        self._draw_full_calendar_button(surface, width - margin_x, button_y)

    def _draw_timeline(self, surface: pygame.Surface, model: CalendarViewModel, rect: pygame.Rect) -> None:
        if not model.events:
            empty = _render_text_alpha(self._hint_font, "Nothing scheduled today.", INK, ALPHA_MUTED)
            surface.blit(empty, (rect.left, rect.top))
            return

        time_right_x = rect.left + self._spacing(80)
        dot_x = time_right_x + self._spacing(32)
        content_x = dot_x + self._spacing(24)
        row_gap = self._spacing(28)

        items = _build_timeline_items(model.events, model.free_gap)
        dot_ys: list[int] = []
        y = rect.top

        for item in items:
            if isinstance(item, ScheduleEvent):
                title_image = _render_text(self._content_font, item.title, INK)
                dot_y = y + title_image.get_height() // 2
                time_label = _render_text_alpha(self._time_col_font, _short_time(item.start), INK, ALPHA_MUTED)
                surface.blit(time_label, time_label.get_rect(midright=(time_right_x, dot_y)))
                surface.blit(title_image, (content_x, y))
                dot_ys.append(dot_y)
                y += title_image.get_height() + row_gap
            else:
                y += self._draw_free_chip(surface, content_x, y, item) + row_gap

        if len(dot_ys) > 1:
            line_height = dot_ys[-1] - dot_ys[0]
            line = pygame.Surface((max(1, self._spacing(1)), max(1, line_height)), pygame.SRCALPHA)
            line.fill((*INK, 33))
            surface.blit(line, (dot_x, dot_ys[0]))

        for dot_y in dot_ys:
            pygame.draw.circle(surface, INK, (dot_x, dot_y), self._spacing(4))

    def _draw_free_chip(self, surface: pygame.Surface, x: int, y: int, gap: FreeTimeGap) -> int:
        label = describe_free_time_gap(gap)
        text_image = _render_text(self._chip_font, label, SLATE_MUTED)
        pad_x = self._spacing(16)
        pad_y = self._spacing(8)
        icon_size = self._spacing(14)
        gap_size = self._spacing(8)
        width = pad_x * 2 + icon_size + gap_size + text_image.get_width()
        height = pad_y * 2 + max(icon_size, text_image.get_height())
        rect = pygame.Rect(x, y, width, height)

        chip = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(chip, (*SLATE_MUTED, 26), chip.get_rect(), border_radius=self._spacing(12))
        pygame.draw.rect(chip, (226, 232, 240, 102), chip.get_rect(), width=1, border_radius=self._spacing(12))
        surface.blit(chip, rect.topleft)

        icon_rect = pygame.Rect(rect.left + pad_x, rect.centery - icon_size // 2, icon_size, icon_size)
        svg_icon.draw_icon(surface, icon_rect, "leaf", SLATE_MUTED)
        surface.blit(text_image, (icon_rect.right + gap_size, rect.centery - text_image.get_height() // 2))
        return height

    def _draw_full_calendar_button(self, surface: pygame.Surface, right_x: int, y: int) -> None:
        label = _render_text(self._button_font, "FULL CALENDAR", INK)
        pad_x = self._spacing(16)
        pad_y = self._spacing(8)
        chevron_size = self._spacing(12)
        gap = self._spacing(8)
        width = pad_x * 2 + label.get_width() + gap + chevron_size
        height = pad_y * 2 + label.get_height()
        rect = pygame.Rect(right_x - width, y - height // 2, width, height)

        button = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(button, (*INK, 15), button.get_rect(), border_radius=rect.height // 2)
        surface.blit(button, rect.topleft)
        surface.blit(label, (rect.left + pad_x, rect.centery - label.get_height() // 2))

        chevron_rect = pygame.Rect(
            rect.right - pad_x - chevron_size,
            rect.centery - chevron_size // 2,
            chevron_size,
            chevron_size,
        )
        svg_icon.draw_icon(surface, chevron_rect, "chevron-right", INK)
        self.full_calendar_rect = rect

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return
        self._scale = _scale_for(surface)
        self._time_font = _font(round(16 * self._scale), 500)
        self._headline_font = _font(round(32 * self._scale), 500)
        self._hint_font = _font(round(18 * self._scale), 300)
        self._time_col_font = _font(round(14 * self._scale), 400)
        self._content_font = _font(round(20 * self._scale), 500)
        self._chip_font = _font(round(14 * self._scale), 500)
        self._button_font = _font(round(11 * self._scale), 600)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


class CelebrationUI:
    """Render the full-screen celebration takeover for a completed task."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0
        self._confetti: list[tuple[float, float, int, tuple[int, int, int]]] | None = None

    def draw(
        self,
        surface: pygame.Surface,
        headline: str,
        subtext: str,
        date_text: str,
        background: AmbientBackground,
    ) -> None:
        """Draw the warm celebratory backdrop, confetti, and centered message."""
        self._ensure_fonts(surface)
        background.draw_washed(
            surface,
            CELEBRATION_BACKGROUND_IMAGE,
            CELEBRATION_WASH_COLOR,
            CELEBRATION_WASH_TOP_ALPHA,
            CELEBRATION_WASH_BOTTOM_ALPHA,
        )

        width, height = surface.get_size()
        self._draw_glow(surface, (width // 2, height // 2))
        self._draw_confetti(surface, (width, height))

        headline_image = _render_text(self._headline_font, headline, CELEBRATION_TEXT_COLOR)
        subtext_image = _render_text_alpha(self._subtext_font, subtext, CELEBRATION_TEXT_COLOR, 235)
        date_image = _render_text_alpha(self._date_font, date_text.upper(), CELEBRATION_TEXT_COLOR, ALPHA_MUTED)

        gap = self._spacing(12)
        content_height = headline_image.get_height() + subtext_image.get_height() + date_image.get_height() + gap * 2
        y = (height - content_height) // 2

        for image in (headline_image, subtext_image, date_image):
            surface.blit(image, image.get_rect(midtop=(width // 2, y)))
            y += image.get_height() + gap

        footer = _render_text_alpha(self._footer_font, "TAP TO DISMISS", CELEBRATION_TEXT_COLOR, ALPHA_FAINT)
        surface.blit(footer, footer.get_rect(midbottom=(width // 2, height - self._spacing(54))))

    def _draw_glow(self, surface: pygame.Surface, center: tuple[int, int]) -> None:
        glow = pygame.Surface((self._spacing(700), self._spacing(500)), pygame.SRCALPHA)
        glow_rect = glow.get_rect()
        for step in range(6, 0, -1):
            alpha = round(10 * step)
            radius_w = round(glow_rect.width * step / 12)
            radius_h = round(glow_rect.height * step / 12)
            ellipse_rect = pygame.Rect(0, 0, radius_w, radius_h)
            ellipse_rect.center = glow_rect.center
            pygame.draw.ellipse(glow, (255, 244, 224, alpha), ellipse_rect)
        surface.blit(glow, glow.get_rect(center=center))

    def _draw_confetti(self, surface: pygame.Surface, size: tuple[int, int]) -> None:
        if self._confetti is None:
            self._confetti = _generate_confetti()

        for fx, fy, dot_size, color in self._confetti:
            pos = (round(fx * size[0]), round(fy * size[1]))
            scaled_size = max(2, self._spacing(dot_size))
            pygame.draw.circle(surface, color, pos, scaled_size // 2)

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return
        self._scale = _scale_for(surface)
        self._headline_font = _font(round(64 * self._scale), 700)
        self._subtext_font = _font(round(28 * self._scale), 400)
        self._date_font = _font(round(14 * self._scale), 300)
        self._footer_font = _font(round(11 * self._scale), 600)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


class ReflectionUI:
    """Render the weekly reflection check-in screen."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0
        self.dismiss_rect: pygame.Rect | None = None

    def draw(self, surface: pygame.Surface, model: ReflectionViewModel, background: AmbientBackground) -> None:
        """Draw the intro line, active prompt with a listening indicator, and dimmed prompts."""
        self._ensure_fonts(surface)
        _draw_detail_backdrop(surface, background)

        width, height = surface.get_size()
        margin_x = self._spacing(MARGIN_X)
        top = self._spacing(PANEL_PAD_TOP)

        time_image = _render_text(self._time_font, model.time_text, INK)
        surface.blit(time_image, (margin_x, top))
        self.dismiss_rect = _draw_dismiss_button(surface, width - margin_x, top, self._spacing(32))

        content_top = top + self._spacing(80)
        content_bottom = height - self._spacing(PANEL_PAD_BOTTOM)

        y = content_top
        intro_image = _render_text(self._intro_font, "Let's take a few minutes.", INK)
        surface.blit(intro_image, (margin_x, y))
        y += intro_image.get_height() + self._spacing(64)

        if model.prompts:
            active_image = _render_text(self._active_font, model.prompts[0], INK)
            surface.blit(active_image, (margin_x, y))
            y += active_image.get_height() + self._spacing(12)

            glow_center = (margin_x + self._spacing(20), y + self._spacing(20))
            self._draw_pulse(surface, glow_center)
            listening = _render_text(self._listening_font, "Listening...", SLATE_MUTED)
            surface.blit(listening, (margin_x + self._spacing(52), y + self._spacing(13)))
            y += self._spacing(40) + self._spacing(32)

            for prompt, alpha in zip(model.prompts[1:], (ALPHA_FAINT, ALPHA_GHOST)):
                dim_image = _render_text_alpha(self._dim_font, prompt, INK, alpha)
                surface.blit(dim_image, (margin_x, y))
                y += dim_image.get_height() + self._spacing(32)

        self._draw_progress_dots(surface, margin_x, content_bottom - self._spacing(28), len(model.prompts))

    def _draw_pulse(self, surface: pygame.Surface, center: tuple[int, int]) -> None:
        ticks = pygame.time.get_ticks()
        phase = (ticks % 2000) / 2000
        pulse = 0.5 + 0.5 * abs(1 - 2 * phase)

        radius = self._spacing(20)
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        alpha = round(60 + 60 * pulse)
        pygame.draw.circle(glow, (122, 155, 196, alpha), (radius, radius), radius)
        pygame.draw.circle(glow, (122, 155, 196, 220), (radius, radius), round(radius * 0.4))
        surface.blit(glow, (center[0] - radius, center[1] - radius))

    def _draw_progress_dots(self, surface: pygame.Surface, x: int, y: int, count: int) -> None:
        radius = self._spacing(4)
        gap = self._spacing(12)
        for index in range(max(count, 1)):
            color = (74, 111, 165) if index == 0 else (30, 42, 58)
            alpha = ALPHA_STRONG if index == 0 else ALPHA_GHOST
            dot = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*color, alpha), (radius, radius), radius)
            surface.blit(dot, (x + index * (radius * 2 + gap), y))

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return
        self._scale = _scale_for(surface)
        self._time_font = _font(round(16 * self._scale), 500)
        self._intro_font = _font(round(32 * self._scale), 400)
        self._active_font = _font(round(40 * self._scale), 600)
        self._listening_font = _font(round(14 * self._scale), 300)
        self._dim_font = _font(round(28 * self._scale), 300)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


class ListeningUI:
    """Render the full-screen "I'm listening..." state shown while capturing voice input."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0

    def draw(self, surface: pygame.Surface, background: AmbientBackground, caption: str = "I'm listening...") -> None:
        """Draw the wallpaper wash, a breathing glow, and the listening caption, all centered."""
        self._ensure_fonts(surface)
        background.draw_washed(
            surface, HOME_BACKGROUND_IMAGE, HOME_WASH_COLOR, HOME_WASH_TOP_ALPHA, HOME_WASH_BOTTOM_ALPHA
        )

        width, height = surface.get_size()
        glow_size = self._spacing(120)
        gap = self._spacing(24)
        caption_image = _render_text_alpha(self._caption_font, caption, SLATE_MUTED, 230)

        content_height = glow_size + gap + caption_image.get_height()
        top = (height - content_height) // 2

        glow_center = (width // 2, top + glow_size // 2)
        self._draw_glow(surface, glow_center, glow_size // 2)

        caption_top = top + glow_size + gap
        surface.blit(caption_image, caption_image.get_rect(midtop=(width // 2, caption_top)))

    def _draw_glow(self, surface: pygame.Surface, center: tuple[int, int], base_radius: int) -> None:
        ticks = pygame.time.get_ticks()
        breathe = (math.sin(ticks / 1000.0 * math.pi) + 1) / 2
        radius = round(base_radius * (0.92 + 0.16 * breathe))

        glow = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        glow_center = glow.get_rect().center
        for step in range(8, 0, -1):
            alpha = round(6 * step)
            layer_radius = round(radius * (0.5 + 0.5 * step / 8))
            pygame.draw.circle(glow, (*SLATE_MUTED, alpha), glow_center, layer_radius)
        pygame.draw.circle(glow, (*SLATE_MUTED, 110), glow_center, round(radius * 0.55))
        surface.blit(glow, glow.get_rect(center=center))

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return
        self._scale = _scale_for(surface)
        self._caption_font = _font(round(14 * self._scale), 300)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


class FullCalendarUI:
    """Render the full month calendar reached from the calendar detail screen."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0
        self.day_rects: dict[date, pygame.Rect] = {}

    def draw(self, surface: pygame.Surface, model: FullCalendarViewModel, background: AmbientBackground) -> None:
        """Draw the month header, weekday row, and day grid; record each day's tap rect."""
        self._ensure_fonts(surface)
        background.draw_washed(
            surface, DARK_BACKGROUND_IMAGE, DARK_WASH_COLOR, DARK_WASH_TOP_ALPHA, DARK_WASH_BOTTOM_ALPHA
        )

        width, height = surface.get_size()
        margin_x = self._spacing(MARGIN_X)
        top = self._spacing(64)

        time_image = _render_text_alpha(self._time_font, model.time_text, DARK_MUTED, 204)
        surface.blit(time_image, (margin_x, top))

        month_label = model.today.strftime("%B %Y")
        month_image = _render_text(self._month_font, month_label, DARK_INK)
        surface.blit(month_image, (margin_x, top + time_image.get_height() + self._spacing(8)))

        footer_y = height - self._spacing(48) - self._spacing(32)

        weekday_y = top + time_image.get_height() + self._spacing(8) + month_image.get_height() + self._spacing(40)
        col_gap = self._spacing(8)
        col_width = (width - margin_x * 2 - col_gap * 6) / 7

        weekday_row_height = 0
        for index, label in enumerate(("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")):
            text = _render_text_alpha(self._weekday_font, label, DARK_MUTED, ALPHA_SECONDARY)
            x = margin_x + index * (col_width + col_gap) + col_width / 2
            surface.blit(text, text.get_rect(midtop=(round(x), weekday_y)))
            weekday_row_height = max(weekday_row_height, text.get_height())

        grid_top = weekday_y + weekday_row_height + self._spacing(24)

        weeks = calendar_module.Calendar(firstweekday=0).monthdayscalendar(model.today.year, model.today.month)
        row_gap = self._spacing(8)
        available = footer_y - self._spacing(24) - grid_top
        row_height = max(self._spacing(60), (available - row_gap * (len(weeks) - 1)) / len(weeks))

        self.day_rects = {}
        for row_index, week in enumerate(weeks):
            for col_index, day_num in enumerate(week):
                if day_num == 0:
                    continue
                rect = pygame.Rect(
                    round(margin_x + col_index * (col_width + col_gap)),
                    round(grid_top + row_index * (row_height + row_gap)),
                    round(col_width),
                    round(row_height),
                )
                day_date = date(model.today.year, model.today.month, day_num)
                is_today = day_date == model.today
                self.day_rects[day_date] = rect
                self._draw_day_cell(surface, rect, day_num, is_today, model.events_by_day.get(day_date, ()))

        icon_rect = pygame.Rect(margin_x, footer_y, self._spacing(32), self._spacing(32))
        _draw_icon_badge(surface, icon_rect, "x", DARK_INK, (255, 255, 255, 20))
        hint_text = _render_text_alpha(self._hint_font, "Tap anywhere to dismiss", DARK_INK, ALPHA_MUTED)
        surface.blit(
            hint_text,
            (icon_rect.right + self._spacing(12), footer_y + (icon_rect.height - hint_text.get_height()) // 2),
        )

    def _draw_day_cell(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        day_num: int,
        is_today: bool,
        events: tuple[ScheduleEvent, ...],
    ) -> None:
        if is_today:
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel, (248, 250, 252, 46), panel.get_rect(), border_radius=self._spacing(12))
            pygame.draw.rect(panel, (255, 255, 255, 89), panel.get_rect(), width=1, border_radius=self._spacing(12))
            surface.blit(panel, rect.topleft)

        pad = self._spacing(12)
        day_font = self._today_day_font if is_today else self._day_font
        day_text = _render_text_alpha(day_font, str(day_num), DARK_INK, ALPHA_FULL if is_today else 178)
        surface.blit(day_text, (rect.left + pad, rect.top + pad))

        y = rect.top + pad + day_text.get_height() + self._spacing(4)
        max_width = rect.width - pad * 2
        shown = events[:2]
        for event in shown:
            if y > rect.bottom - pad:
                break
            label = event.title if event.all_day else f"{_short_time(event.start)} {event.title}"
            clipped = _clip_text(self._pill_font, label, max_width - self._spacing(16))
            text_image = _render_text_alpha(self._pill_font, clipped, DARK_INK, 230)
            pill_rect = pygame.Rect(rect.left + pad, y, max_width, text_image.get_height() + self._spacing(8))
            pill = pygame.Surface(pill_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(pill, (255, 255, 255, 20), pill.get_rect(), border_radius=self._spacing(6))
            surface.blit(pill, pill_rect.topleft)
            surface.blit(text_image, (pill_rect.left + self._spacing(8), pill_rect.top + self._spacing(4)))
            y += pill_rect.height + self._spacing(4)

        extra = len(events) - len(shown)
        if extra > 0 and y <= rect.bottom - pad:
            more_text = _render_text_alpha(self._more_font, f"+{extra} more", DARK_MUTED, 178)
            surface.blit(more_text, (rect.left + pad, y))

        if is_today:
            today_label = _render_text_alpha(self._today_label_font, "T O D A Y", (255, 255, 255), 128)
            surface.blit(today_label, (rect.left + pad, rect.bottom - pad - today_label.get_height()))

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return
        self._scale = _scale_for(surface)
        self._time_font = _font(round(16 * self._scale), 500)
        self._month_font = _font(round(64 * self._scale), 200)
        self._weekday_font = _font(round(12 * self._scale), 600)
        self._day_font = _font(round(24 * self._scale), 300)
        self._today_day_font = _font(round(24 * self._scale), 600)
        self._pill_font = _font(round(11 * self._scale), 500)
        self._more_font = _font(round(11 * self._scale), 500)
        self._today_label_font = _font(round(8 * self._scale), 500)
        self._hint_font = _font(round(13 * self._scale), 400)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


class DayDetailUI:
    """Render a single day's agenda, reached by tapping a day in the full calendar."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0

    def draw(self, surface: pygame.Surface, model: DayDetailViewModel, background: AmbientBackground) -> None:
        """Draw the breadcrumb, day header, and either the agenda list or an empty state."""
        self._ensure_fonts(surface)
        background.draw_washed(
            surface, DARK_BACKGROUND_IMAGE, DARK_WASH_COLOR, DARK_WASH_TOP_ALPHA, DARK_WASH_BOTTOM_ALPHA
        )

        width, height = surface.get_size()
        margin_x = self._spacing(MARGIN_X)
        top = self._spacing(64)

        chevron_size = self._spacing(18)
        chevron_rect = pygame.Rect(margin_x, top, chevron_size, chevron_size)
        svg_icon.draw_icon(surface, chevron_rect, "chevron-left", DARK_MUTED, alpha=204)
        breadcrumb = _render_text_alpha(self._breadcrumb_font, model.month_label, DARK_MUTED, 204)
        surface.blit(
            breadcrumb,
            (chevron_rect.right + self._spacing(12), top + (chevron_size - breadcrumb.get_height()) // 2),
        )

        content_top = top + chevron_size + self._spacing(64)
        weekday_image = _render_text(self._weekday_font, model.weekday_label, DARK_INK)
        surface.blit(weekday_image, (margin_x, content_top))

        date_y = content_top + weekday_image.get_height() + self._spacing(12)
        date_image = _render_text_alpha(self._date_font, model.date_label, DARK_MUTED, 230)
        surface.blit(date_image, (margin_x, date_y))

        events_top = date_y + date_image.get_height() + self._spacing(48)
        label_image = _render_text_alpha(self._events_label_font, "E V E N T S", DARK_MUTED, ALPHA_SECONDARY)
        surface.blit(label_image, (margin_x, events_top))

        line_y = events_top + label_image.get_height() + self._spacing(16)
        line = pygame.Surface((width - margin_x * 2, 1), pygame.SRCALPHA)
        line.fill((*DARK_MUTED, 51))
        surface.blit(line, (margin_x, line_y))

        list_top = line_y + self._spacing(24)
        if not model.events:
            empty_image = _render_text_alpha(self._empty_font, "Nothing scheduled", DARK_MUTED, ALPHA_MUTED)
            area = pygame.Rect(margin_x, list_top, width - margin_x * 2, self._spacing(240))
            surface.blit(empty_image, empty_image.get_rect(center=area.center))
        else:
            y = list_top
            time_col_width = self._spacing(140)
            for event in model.events:
                time_label = "All day" if event.all_day else _short_time(event.start)
                time_image = _render_text_alpha(self._agenda_time_font, time_label, DARK_MUTED, 178)
                surface.blit(time_image, (margin_x, y))
                title_image = _render_text(self._agenda_title_font, event.title, DARK_INK)
                surface.blit(title_image, (margin_x + time_col_width, y))
                y += max(time_image.get_height(), title_image.get_height()) + self._spacing(20)

        footer_y = height - self._spacing(48) - self._spacing(32)
        icon_rect = pygame.Rect(margin_x, footer_y, self._spacing(32), self._spacing(32))
        _draw_dismiss_hint(surface, icon_rect, DARK_INK)
        hint_text = _render_text_alpha(self._hint_font, "Tap anywhere to dismiss", DARK_INK, ALPHA_MUTED)
        surface.blit(
            hint_text,
            (icon_rect.right + self._spacing(12), footer_y + (icon_rect.height - hint_text.get_height()) // 2),
        )

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return
        self._scale = _scale_for(surface)
        self._breadcrumb_font = _font(round(16 * self._scale), 500)
        self._weekday_font = _font(round(80 * self._scale), 200)
        self._date_font = _font(round(40 * self._scale), 300)
        self._events_label_font = _font(round(12 * self._scale), 600)
        self._empty_font = _font(round(24 * self._scale), 300)
        self._agenda_time_font = _font(round(18 * self._scale), 400)
        self._agenda_title_font = _font(round(20 * self._scale), 500)
        self._hint_font = _font(round(13 * self._scale), 400)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


def draw_weather_pill(surface: pygame.Surface, ui: AmbientUI, weather: WeatherData, theme: Theme) -> None:
    """Draw the frosted weather pill in the corner of the ambient screen."""
    if not weather.is_available:
        return

    label = (weather.condition or "").upper()
    temp = _format_temp(weather.current_temp)
    label_image = _render_text_alpha(ui.pill_label_font, label, theme.pill_text, theme.pill_label_alpha)
    temp_image = _render_text_alpha(ui.pill_temp_font, temp, theme.pill_text, round(theme.pill_label_alpha * 0.8))

    pad_x = round(16 * ui.scale)
    pad_y = round(12 * ui.scale)
    icon_size = round(32 * ui.scale)
    gap = round(12 * ui.scale)
    text_width = max(label_image.get_width(), temp_image.get_width())
    text_height = label_image.get_height() + round(2 * ui.scale) + temp_image.get_height()

    width = pad_x * 2 + icon_size + gap + text_width
    height = pad_y * 2 + max(icon_size, text_height)
    right_margin = round(24 * ui.scale)
    top_margin = round(40 * ui.scale)
    rect = pygame.Rect(surface.get_width() - right_margin - width, top_margin, width, height)

    _draw_glass_panel(surface, rect, rect.height // 2, theme.pill_bg, theme.pill_border)

    icon_rect = pygame.Rect(rect.left + pad_x, rect.centery - icon_size // 2, icon_size, icon_size)
    weathericons.draw_icon(surface, icon_rect, weather.condition, theme.is_dark, theme.pill_text)

    text_x = icon_rect.right + gap
    text_y = rect.centery - text_height // 2
    surface.blit(label_image, (text_x, text_y))
    surface.blit(temp_image, (text_x, text_y + label_image.get_height() + round(2 * ui.scale)))


def _draw_detail_backdrop(surface: pygame.Surface, background: AmbientBackground) -> None:
    background.draw_washed(
        surface,
        DETAIL_BACKGROUND_IMAGE,
        DETAIL_WASH_COLOR,
        DETAIL_WASH_ALPHA,
        DETAIL_WASH_ALPHA,
        blur_radius=DETAIL_BLUR_RADIUS,
    )


def _draw_dismiss_button(surface: pygame.Surface, right_x: int, top_y: int, size: int) -> pygame.Rect:
    rect = pygame.Rect(right_x - size, top_y, size, size)
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*INK, 15), panel.get_rect(), border_radius=rect.width // 2)
    surface.blit(panel, rect.topleft)

    circle_size = round(size * 0.44)
    circle_rect = pygame.Rect(0, 0, circle_size, circle_size)
    circle_rect.center = rect.center
    pygame.draw.circle(surface, INK, circle_rect.center, circle_size // 2, width=max(1, round(size * 0.06)))
    icon_rect = circle_rect.inflate(-round(circle_size * 0.64), -round(circle_size * 0.64))
    svg_icon.draw_icon(surface, icon_rect, "x", INK)
    return rect


def _draw_dismiss_hint(surface: pygame.Surface, rect: pygame.Rect, ink_color: tuple[int, int, int]) -> None:
    """Draw a non-interactive bordered dismiss glyph, used where any tap dismisses the screen."""
    pygame.draw.circle(surface, ink_color, rect.center, rect.width // 2, width=max(1, round(rect.width * 0.06)))
    icon_rect = rect.inflate(-round(rect.width * 0.64), -round(rect.width * 0.64))
    svg_icon.draw_icon(surface, icon_rect, "x", ink_color)


def _draw_icon_badge(
    surface: pygame.Surface,
    rect: pygame.Rect,
    icon_name: str,
    ink_color: tuple[int, int, int],
    bg_rgba: tuple[int, int, int, int],
) -> None:
    """Draw a filled rounded badge containing a small centered icon."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, bg_rgba, panel.get_rect(), border_radius=rect.width // 2)
    surface.blit(panel, rect.topleft)
    icon_rect = rect.inflate(-round(rect.width * 0.56), -round(rect.width * 0.56))
    svg_icon.draw_icon(surface, icon_rect, icon_name, ink_color)


def _clip_text(font: pygame.font.Font, text: str, max_width: int) -> str:
    """Shorten text with a trailing ellipsis so it fits within max_width."""
    if font.size(text)[0] <= max_width:
        return text

    clipped = text
    while clipped and font.size(clipped + "…")[0] > max_width:
        clipped = clipped[:-1]
    return f"{clipped}…" if clipped else "…"


def _build_timeline_items(
    events: tuple[ScheduleEvent, ...],
    gap: FreeTimeGap | None,
) -> list[ScheduleEvent | FreeTimeGap]:
    items: list[ScheduleEvent | FreeTimeGap] = list(events)
    if gap is None:
        return items

    insert_at = len(items)
    for index, event in enumerate(items):
        if gap.start < event.start:
            insert_at = index
            break
    items.insert(insert_at, gap)
    return items


def _generate_confetti() -> list[tuple[float, float, int, tuple[int, int, int]]]:
    import random

    colors = [(212, 112, 58), (217, 164, 65), (122, 139, 111), (255, 255, 255)]
    rng = random.Random(7)
    dots: list[tuple[float, float, int, tuple[int, int, int]]] = []
    for _ in range(26):
        fx = rng.uniform(0.05, 0.95)
        fy = rng.uniform(0.05, 0.9)
        if 0.3 < fx < 0.7 and 0.25 < fy < 0.75:
            continue
        size = rng.choice((4, 5, 6, 8))
        dots.append((fx, fy, size, rng.choice(colors)))
    return dots


def _draw_glass_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    radius: int,
    tint_rgba: tuple[int, int, int, int],
    border_rgba: tuple[int, int, int, int] | None,
    blur_divisor: int = 20,
) -> None:
    """Sample the region behind rect, soften it, and lay a tinted rounded panel over it."""
    bounded = rect.clip(surface.get_rect())
    if bounded.width <= 0 or bounded.height <= 0:
        return

    crop = surface.subsurface(bounded).copy()
    width, height = crop.get_size()
    small_size = (max(1, width // blur_divisor), max(1, height // blur_divisor))
    blurred = pygame.transform.smoothscale(pygame.transform.smoothscale(crop, small_size), (width, height))

    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    blurred = blurred.convert_alpha()
    blurred.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(blurred, bounded.topleft)

    tint = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(tint, tint_rgba, tint.get_rect(), border_radius=radius)
    surface.blit(tint, bounded.topleft)

    if border_rgba is not None:
        border = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(border, border_rgba, border.get_rect(), width=1, border_radius=radius)
        surface.blit(border, bounded.topleft)


def _render_text(font: pygame.font.Font, text: str, color: tuple[int, int, int]) -> pygame.Surface:
    """Render crisp text at full opacity."""
    return font.render(text, True, color)


def _render_text_alpha(
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    alpha: int,
) -> pygame.Surface:
    """Render text and apply a uniform opacity, blending correctly over any backdrop."""
    image = font.render(text, True, color)
    if alpha < 255:
        image = image.convert_alpha()
        image.set_alpha(alpha)
    return image


def _font(size: int, weight: int = 400) -> pygame.font.Font:
    return pygame.font.Font(FONT_DIR / FONTS[weight], max(1, size))


def _scale_for(surface: pygame.Surface) -> float:
    return max(0.82, min(surface.get_height() / 720, surface.get_width() / 1280))


def _format_temp(value: float | None) -> str:
    if value is None:
        return ""
    return f"{round(value)}°"


def _format_temp_full(value: float | None) -> str:
    if value is None:
        return ""
    return f"{round(value)}°F"


def _short_hour_label(moment: datetime) -> str:
    return moment.strftime("%I %p").lstrip("0")


def _short_time(moment: datetime) -> str:
    return moment.strftime("%I:%M %p").lstrip("0")


def _wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    """Greedily wrap text onto lines no wider than max_width."""
    words = text.split(" ")
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    return lines
