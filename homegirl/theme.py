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
        text_primary=(255, 249, 242),      # Warm ivory
        text_secondary=(236, 220, 198),    # Soft champagne
        text_muted=(201, 179, 154),         # Warm taupe
        time_color=(255, 249, 242),
    ),
    Daypart.AFTERNOON: Theme(
        daypart=Daypart.AFTERNOON,
        background_image="afternoon.png",
        text_primary=(255, 255, 255),      # Bright white
        text_secondary=(214, 242, 255),    # Sky blue
        text_muted=(171, 209, 230),         # Muted aqua
        time_color=(255, 255, 255),
    ),
    Daypart.EVENING: Theme(
        daypart=Daypart.EVENING,
        background_image="evening.png",
        text_primary=(255, 250, 242),      # Warm white
        text_secondary=(255, 223, 215),    # Peach blush
        text_muted=(226, 183, 183),         # Dusty rose
        time_color=(255, 250, 242),
    ),
    Daypart.NIGHT: Theme(
        daypart=Daypart.NIGHT,
        background_image="night.png",
        text_primary=(255, 255, 255),      # Cool white
        text_secondary=(210, 223, 255),    # Moonlight blue
        text_muted=(162, 180, 225),         # Periwinkle
        time_color=(255, 255, 255),
    ),
}


def get_theme(daypart: Daypart) -> Theme:
    """Return the visual theme for a daypart."""
    return THEMES[daypart]
