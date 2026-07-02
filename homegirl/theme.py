"""Time-of-day visual themes for the ambient display."""

from __future__ import annotations

from dataclasses import dataclass

from homegirl.greeting import Daypart

Color = tuple[int, int, int]

DATE_ALPHA = 153
"""~60% opacity, used for date lines and secondary copy across themes."""

MUTED_ALPHA = 102
"""~40% opacity, used for the national-day line and other tertiary copy."""


@dataclass(frozen=True)
class Theme:
    """A daypart palette, wallpaper, and pill styling for the ambient display."""

    daypart: Daypart
    background_image: str
    is_dark: bool
    text_color: Color
    time_color: Color
    wash_color: Color
    wash_top_alpha: int
    wash_bottom_alpha: int
    pill_bg: tuple[int, int, int, int]
    pill_border: tuple[int, int, int, int]
    pill_text: Color
    pill_label_alpha: int


THEMES: dict[Daypart, Theme] = {
    Daypart.MORNING: Theme(
        daypart=Daypart.MORNING,
        background_image="morning.png",
        is_dark=False,
        text_color=(30, 42, 58),
        time_color=(107, 127, 160),
        wash_color=(248, 250, 252),
        wash_top_alpha=200,
        wash_bottom_alpha=140,
        pill_bg=(255, 255, 255, 140),
        pill_border=(255, 255, 255, 204),
        pill_text=(26, 37, 53),
        pill_label_alpha=242,
    ),
    Daypart.AFTERNOON: Theme(
        daypart=Daypart.AFTERNOON,
        background_image="afternoon.png",
        is_dark=False,
        text_color=(26, 37, 53),
        time_color=(122, 139, 111),
        wash_color=(248, 250, 252),
        wash_top_alpha=160,
        wash_bottom_alpha=110,
        pill_bg=(255, 255, 255, 140),
        pill_border=(255, 255, 255, 255),
        pill_text=(26, 37, 53),
        pill_label_alpha=230,
    ),
    Daypart.EVENING: Theme(
        daypart=Daypart.EVENING,
        background_image="evening.png",
        is_dark=False,
        text_color=(42, 18, 8),
        time_color=(74, 138, 114),
        wash_color=(248, 232, 216),
        wash_top_alpha=180,
        wash_bottom_alpha=120,
        pill_bg=(255, 245, 229, 153),
        pill_border=(255, 255, 255, 204),
        pill_text=(42, 18, 8),
        pill_label_alpha=255,
    ),
    Daypart.NIGHT: Theme(
        daypart=Daypart.NIGHT,
        background_image="night.png",
        is_dark=True,
        text_color=(230, 232, 255),
        time_color=(122, 155, 196),
        wash_color=(11, 16, 32),
        wash_top_alpha=204,
        wash_bottom_alpha=90,
        pill_bg=(140, 158, 191, 64),
        pill_border=(255, 255, 255, 90),
        pill_text=(228, 234, 245),
        pill_label_alpha=217,
    ),
}

INK: Color = (30, 42, 58)
"""Fixed ink color used on frosted content screens, independent of daypart."""

HOME_BACKGROUND_IMAGE = "home.png"
HOME_WASH_COLOR: Color = (248, 250, 252)
HOME_WASH_TOP_ALPHA = 190
HOME_WASH_BOTTOM_ALPHA = 130

DETAIL_BACKGROUND_IMAGE = "morning.png"
DETAIL_WASH_COLOR: Color = (248, 250, 252)
DETAIL_WASH_ALPHA = 235
DETAIL_BLUR_RADIUS = 48

CELEBRATION_BACKGROUND_IMAGE = "evening.png"
CELEBRATION_WASH_COLOR: Color = (248, 232, 216)
CELEBRATION_WASH_TOP_ALPHA = 210
CELEBRATION_WASH_BOTTOM_ALPHA = 130
CELEBRATION_TEXT_COLOR: Color = (42, 18, 8)


def get_theme(daypart: Daypart) -> Theme:
    """Return the visual theme for a daypart."""
    return THEMES[daypart]
