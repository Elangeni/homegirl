"""Ambient floating typography."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pygame

from homegirl.models.weather import HourlyForecast, WeatherData
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
    weather: WeatherData


@dataclass(frozen=True)
class AppViewModel:
    """Data required to render the unlocked app frame."""

    time_text: str
    labels: tuple[str, str, str, str]
    weather: WeatherData
    schedule_summary: str | None = None


@dataclass(frozen=True)
class WeatherViewModel:
    """Data required to render the weather detail screen."""

    time_text: str
    weather: WeatherData
    headline: str | None
    advice: str | None


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

        self._draw_weather(surface, model.weather, theme)

    def _draw_weather(
        self,
        surface: pygame.Surface,
        weather: WeatherData,
        theme: Theme,
    ) -> None:
        if not weather.is_available:
            return

        text = _format_temp(weather.current_temp)
        image = _render_text(self._small_font, text, theme.text_secondary)
        margin_x = max(32, round(surface.get_width() * 0.044))
        margin_y = max(28, round(surface.get_height() * 0.056))
        rect = image.get_rect(topright=(surface.get_width() - margin_x, margin_y))
        surface.blit(image, rect)

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
        self.weather_tile_rect: pygame.Rect | None = None

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
            if index == 0:
                self.weather_tile_rect = rect
                self._draw_weather_tile(surface, rect, model.weather)
            elif index == 1:
                self._draw_schedule_tile(surface, rect, model.schedule_summary)
            elif index == 2:
                self._draw_coming_soon_tile(surface, rect)
            else:
                self._draw_tile(surface, rect, label)

    def _draw_weather_tile(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        weather: WeatherData,
    ) -> None:
        self._draw_tile_frame(surface, rect)

        title_color = (68, 68, 60)
        text_color = (33, 33, 29)
        muted_color = (88, 88, 78)
        left = rect.left + self._spacing(28)
        top = rect.top + self._spacing(24)

        title = _render_text(self._card_title_font, "Weather", title_color)
        surface.blit(title, title.get_rect(topleft=(left, top)))

        if not weather.is_available:
            unavailable = _render_text(self._card_body_font, "Unavailable", muted_color)
            surface.blit(
                unavailable,
                unavailable.get_rect(topleft=(left, top + self._spacing(58))),
            )
            return

        temp = _render_text(self._weather_temp_font, _format_temp(weather.current_temp), text_color)
        surface.blit(temp, temp.get_rect(topleft=(left, top + self._spacing(46))))

        if weather.condition:
            condition = _render_text(
                self._card_body_font,
                weather.condition.title(),
                muted_color,
            )
            surface.blit(condition, condition.get_rect(topleft=(left, top + self._spacing(116))))

        if weather.high_temp is not None and weather.low_temp is not None:
            high_low = _render_text(
                self._card_detail_font,
                f"High {_format_temp(weather.high_temp)}  Low {_format_temp(weather.low_temp)}",
                muted_color,
            )
            surface.blit(high_low, high_low.get_rect(topleft=(left, top + self._spacing(158))))

    def _draw_schedule_tile(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        summary: str | None,
    ) -> None:
        self._draw_tile_frame(surface, rect)

        title_color = (68, 68, 60)
        body_color = (33, 33, 29)
        muted_color = (88, 88, 78)
        left = rect.left + self._spacing(28)
        top = rect.top + self._spacing(24)
        max_width = rect.width - self._spacing(56)

        title = _render_text(self._card_title_font, "Schedule", title_color)
        surface.blit(title, title.get_rect(topleft=(left, top)))

        text = summary or "Unavailable"
        color = body_color if summary else muted_color
        body_top = top + self._spacing(58)
        for line in _wrap_text(self._card_body_font, text, max_width):
            line_image = _render_text(self._card_body_font, line, color)
            surface.blit(line_image, line_image.get_rect(topleft=(left, body_top)))
            body_top += line_image.get_height() + self._spacing(4)

    def _draw_coming_soon_tile(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_tile_frame(surface, rect)

        title_color = (68, 68, 60)
        muted_color = (88, 88, 78)
        left = rect.left + self._spacing(28)
        top = rect.top + self._spacing(24)

        title = _render_text(self._card_title_font, "Mail", title_color)
        surface.blit(title, title.get_rect(topleft=(left, top)))

        body = _render_text(self._card_body_font, "Coming soon", muted_color)
        surface.blit(body, body.get_rect(topleft=(left, top + self._spacing(58))))

    def _draw_tile(self, surface: pygame.Surface, rect: pygame.Rect, label: str) -> None:
        self._draw_tile_frame(surface, rect)
        text_color = (33, 33, 29)

        label_image = _render_text(self._tile_font, label, text_color)
        label_rect = label_image.get_rect(center=rect.center)
        surface.blit(label_image, label_rect)

    def _draw_tile_frame(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        fill_color = (255, 255, 251)
        border_color = (52, 52, 46)

        pygame.draw.rect(surface, fill_color, rect, border_radius=self._spacing(8))
        pygame.draw.rect(
            surface,
            border_color,
            rect,
            width=max(1, self._spacing(2)),
            border_radius=self._spacing(8),
        )

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return

        self._scale = max(
            0.82,
            min(surface.get_height() / 720, surface.get_width() / 1280),
        )
        self._time_font = _font(round(30 * self._scale), 500)
        self._tile_font = _font(round(56 * self._scale), 600)
        self._card_title_font = _font(round(26 * self._scale), 600)
        self._weather_temp_font = _font(round(58 * self._scale), 600)
        self._card_body_font = _font(round(30 * self._scale), 400)
        self._card_detail_font = _font(round(24 * self._scale), 400)
        self._fonts_ready = True

    def _spacing(self, value: int) -> int:
        return round(value * self._scale)


class WeatherUI:
    """Render the weather detail screen reached from the app grid."""

    def __init__(self) -> None:
        self._fonts_ready = False
        self._scale = 1.0
        self.dismiss_rect: pygame.Rect | None = None

    def draw(self, surface: pygame.Surface, model: WeatherViewModel) -> None:
        """Draw the current reading, situational copy, and hourly strip."""
        self._ensure_fonts(surface)

        surface.fill((242, 240, 234))
        width, _ = surface.get_size()
        margin_x = self._spacing(140)
        margin_top = self._spacing(40)
        text_color = (34, 34, 30)
        muted_color = (88, 88, 78)

        time_image = _render_text(self._time_font, model.time_text, text_color)
        surface.blit(time_image, time_image.get_rect(topleft=(margin_x, margin_top)))

        dismiss_size = self._spacing(32)
        self.dismiss_rect = pygame.Rect(
            width - margin_x - dismiss_size,
            margin_top,
            dismiss_size,
            dismiss_size,
        )
        pygame.draw.circle(
            surface,
            (30, 42, 58, 20),
            self.dismiss_rect.center,
            dismiss_size // 2,
            width=max(1, self._spacing(2)),
        )
        _draw_x_mark(surface, self.dismiss_rect, text_color, self._spacing(4))

        if not model.weather.is_available:
            unavailable = _render_text(self._advice_font, "Weather unavailable", muted_color)
            surface.blit(unavailable, unavailable.get_rect(topleft=(margin_x, margin_top + self._spacing(120))))
            return

        y = margin_top + self._spacing(80)
        if model.headline:
            max_text_width = round(width * 0.55)
            for line in _wrap_text(self._headline_font, model.headline, max_text_width):
                line_image = _render_text(self._headline_font, line, text_color)
                surface.blit(line_image, line_image.get_rect(topleft=(margin_x, y)))
                y += line_image.get_height() + self._spacing(4)

        y += self._spacing(40)
        temp_image = _render_text(
            self._temp_font,
            _format_temp_full(model.weather.current_temp),
            text_color,
        )
        temp_rect = temp_image.get_rect(topleft=(margin_x, y))
        surface.blit(temp_image, temp_rect)

        detail_x = temp_rect.right + self._spacing(32)
        detail_y = temp_rect.top + self._spacing(8)
        if model.weather.condition:
            condition_image = _render_text(
                self._condition_font,
                model.weather.condition.upper(),
                muted_color,
            )
            surface.blit(condition_image, condition_image.get_rect(topleft=(detail_x, detail_y)))
            detail_y += condition_image.get_height() + self._spacing(4)

        if model.advice:
            advice_image = _render_text(self._advice_font, model.advice, muted_color)
            surface.blit(advice_image, advice_image.get_rect(topleft=(detail_x, detail_y)))

        forecast_top = temp_rect.bottom + self._spacing(64)
        forecast_bottom = surface.get_height() - self._spacing(80)
        if model.weather.hourly:
            self._draw_hourly_strip(
                surface,
                model.weather.hourly,
                pygame.Rect(margin_x, forecast_top, width - margin_x * 2, forecast_bottom - forecast_top),
                text_color,
                muted_color,
            )

    def _draw_hourly_strip(
        self,
        surface: pygame.Surface,
        hourly: tuple[HourlyForecast, ...],
        rect: pygame.Rect,
        text_color: tuple[int, int, int],
        muted_color: tuple[int, int, int],
    ) -> None:
        line_color = (43, 43, 39)
        pygame.draw.line(
            surface,
            line_color,
            (rect.left, rect.top),
            (rect.right, rect.top),
            max(1, self._spacing(1)),
        )

        slot_top = rect.top + self._spacing(24)
        slot_width = rect.width // len(hourly)
        icon_size = self._spacing(24)

        for index, hour in enumerate(hourly):
            slot_center_x = rect.left + slot_width * index + slot_width // 2

            hour_label = _render_text(self._hour_font, _short_hour_label(hour.time), muted_color)
            surface.blit(hour_label, hour_label.get_rect(midtop=(slot_center_x, slot_top)))

            icon_top = slot_top + hour_label.get_height() + self._spacing(12)
            icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
            icon_rect.center = (slot_center_x, icon_top + icon_size // 2)
            _draw_condition_icon(surface, icon_rect, hour.condition, muted_color)

            temp_top = icon_rect.bottom + self._spacing(12)
            temp_label = _render_text(self._hour_temp_font, _format_temp(hour.temp), text_color)
            surface.blit(temp_label, temp_label.get_rect(midtop=(slot_center_x, temp_top)))

    def _ensure_fonts(self, surface: pygame.Surface) -> None:
        if self._fonts_ready:
            return

        self._scale = max(
            0.82,
            min(surface.get_height() / 720, surface.get_width() / 1280),
        )
        self._time_font = _font(round(20 * self._scale), 500)
        self._headline_font = _font(round(34 * self._scale), 500)
        self._temp_font = _font(round(120 * self._scale), 700)
        self._condition_font = _font(round(15 * self._scale), 300)
        self._advice_font = _font(round(18 * self._scale), 300)
        self._hour_font = _font(round(14 * self._scale), 500)
        self._hour_temp_font = _font(round(20 * self._scale), 600)
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


def _draw_x_mark(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    """Draw a small dismiss glyph centered in rect."""
    inset = round(rect.width * 0.3)
    pygame.draw.line(
        surface,
        color,
        (rect.left + inset, rect.top + inset),
        (rect.right - inset, rect.bottom - inset),
        max(1, thickness),
    )
    pygame.draw.line(
        surface,
        color,
        (rect.right - inset, rect.top + inset),
        (rect.left + inset, rect.bottom - inset),
        max(1, thickness),
    )


def _condition_category(condition: str | None) -> str:
    """Classify condition text into a coarse icon category."""
    text = (condition or "").lower()
    if "thunder" in text or "storm" in text:
        return "thunder"
    if "snow" in text or "sleet" in text or "ice" in text:
        return "snow"
    if "rain" in text or "drizzle" in text or "shower" in text:
        return "rain"
    if "cloud" in text or "overcast" in text or "fog" in text or "mist" in text:
        return "cloud"
    return "clear"


def _draw_condition_icon(
    surface: pygame.Surface,
    rect: pygame.Rect,
    condition: str | None,
    color: tuple[int, int, int],
) -> None:
    """Draw a simple placeholder glyph for the hourly forecast condition."""
    category = _condition_category(condition)
    width = max(1, round(rect.width * 0.08))

    if category == "clear":
        radius = round(rect.width * 0.32)
        pygame.draw.circle(surface, color, rect.center, radius, width=width)
        return

    cloud_rect = pygame.Rect(0, 0, round(rect.width * 0.8), round(rect.height * 0.5))
    cloud_rect.center = (rect.centerx, rect.centery - round(rect.height * 0.05))
    pygame.draw.ellipse(surface, color, cloud_rect, width=width)

    if category == "cloud" or category == "snow":
        return

    if category == "rain":
        for offset in (-0.2, 0.0, 0.2):
            x = rect.centerx + round(offset * rect.width)
            top = cloud_rect.bottom + round(rect.height * 0.05)
            bottom = top + round(rect.height * 0.22)
            pygame.draw.line(surface, color, (x, top), (x - round(rect.width * 0.08), bottom), width)
        return

    if category == "thunder":
        bolt_top = (rect.centerx + round(rect.width * 0.08), cloud_rect.bottom)
        bolt_mid = (rect.centerx - round(rect.width * 0.08), rect.centery + round(rect.height * 0.18))
        bolt_bottom = (rect.centerx + round(rect.width * 0.02), rect.bottom)
        pygame.draw.lines(surface, color, False, [bolt_top, bolt_mid, bolt_bottom], width)
