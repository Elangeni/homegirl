"""Weather glyphs from Erik Flowers' Weather Icons font (SIL OFL 1.1 / MIT)."""

from __future__ import annotations

from pathlib import Path

import pygame

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "weathericons-regular-webfont.ttf"

# Codepoints from weather-icons.css — see erikflowers/weather-icons.
_CLEAR_DAY = ""
_CLEAR_NIGHT = ""
_PARTLY_DAY = ""
_PARTLY_NIGHT = ""
_CLOUDY = ""
_FOG_DAY = ""
_FOG_NIGHT = ""
_RAIN_DAY = ""
_RAIN_NIGHT = ""
_SNOW_DAY = ""
_SNOW_NIGHT = ""
_THUNDER_DAY = ""
_THUNDER_NIGHT = ""

# The glyphs don't fill their em-square, so render noticeably larger than
# the target box and let the centered blit crop to it.
_SIZE_FACTOR = 0.9

_font_cache: dict[int, pygame.font.Font] = {}
_render_cache: dict[tuple[str, int, tuple[int, int, int]], pygame.Surface] = {}


def _category(condition: str | None) -> str:
    text = (condition or "").lower()
    if "thunder" in text or "storm" in text:
        return "thunder"
    if "snow" in text or "sleet" in text or "ice" in text:
        return "snow"
    if "rain" in text or "drizzle" in text or "shower" in text:
        return "rain"
    if "fog" in text or "mist" in text or "haze" in text:
        return "fog"
    if "partly" in text or "partial" in text:
        return "partly-cloudy"
    if "cloud" in text or "overcast" in text:
        return "cloud"
    return "clear"


def glyph_for(condition: str | None, is_night: bool) -> str:
    """Return the weather-icons font glyph for a condition string."""
    category = _category(condition)
    if category == "clear":
        return _CLEAR_NIGHT if is_night else _CLEAR_DAY
    if category == "partly-cloudy":
        return _PARTLY_NIGHT if is_night else _PARTLY_DAY
    if category == "cloud":
        return _CLOUDY
    if category == "fog":
        return _FOG_NIGHT if is_night else _FOG_DAY
    if category == "rain":
        return _RAIN_NIGHT if is_night else _RAIN_DAY
    if category == "snow":
        return _SNOW_NIGHT if is_night else _SNOW_DAY
    if category == "thunder":
        return _THUNDER_NIGHT if is_night else _THUNDER_DAY
    return _CLEAR_DAY


def _font(size: int) -> pygame.font.Font:
    cached = _font_cache.get(size)
    if cached is None:
        cached = pygame.font.Font(FONT_PATH, size)
        _font_cache[size] = cached
    return cached


def draw_icon(
    surface: pygame.Surface,
    rect: pygame.Rect,
    condition: str | None,
    is_night: bool,
    color: tuple[int, int, int],
) -> None:
    """Draw the weather glyph for a condition, centered in rect."""
    glyph = glyph_for(condition, is_night)
    size = max(1, round(rect.height * _SIZE_FACTOR))

    key = (glyph, size, color)
    cached = _render_cache.get(key)
    if cached is None:
        cached = _font(size).render(glyph, True, color)
        _render_cache[key] = cached

    surface.blit(cached, cached.get_rect(center=rect.center))
