"""Time-of-day visual themes for the ambient display."""

from __future__ import annotations

from dataclasses import dataclass

from homegirl.greeting import Daypart

Color = tuple[int, int, int]


@dataclass(frozen=True)
class Theme:
    """A daypart palette and static wallpaper selection."""

    daypart: Daypart
    background_image: str
    text_primary: Color
    text_secondary: Color
    text_muted: Color
    time_color: Color


THEMES: dict[Daypart, Theme] = {
    Daypart.MORNING: Theme(
        daypart=Daypart.MORNING,
        background_image="morning.png",
        text_primary=(255, 255, 255),
        text_secondary=(255, 249, 236),
        text_muted=(242, 242, 242),
        time_color=(255, 255, 255),
    ),
    Daypart.AFTERNOON: Theme(
        daypart=Daypart.AFTERNOON,
        background_image="afternoon.png",
        text_primary=(255, 255, 255),
        text_secondary=(248, 253, 255),
        text_muted=(214, 214, 214),
        time_color=(255, 255, 255),
    ),
    Daypart.EVENING: Theme(
        daypart=Daypart.EVENING,
        background_image="evening.png",
        text_primary=(255, 250, 242),
        text_secondary=(255, 243, 236),
        text_muted=(214, 214, 214),
        time_color=(255, 255, 255),
    ),
    Daypart.NIGHT: Theme(
        daypart=Daypart.NIGHT,
        background_image="night.png",
        text_primary=(255, 255, 255),
        text_secondary=(242, 242, 242),
        text_muted=(214, 214, 214),
        time_color=(255, 255, 255),
    ),
}


def get_theme(daypart: Daypart) -> Theme:
    """Return the visual theme for a daypart."""
    return THEMES[daypart]
