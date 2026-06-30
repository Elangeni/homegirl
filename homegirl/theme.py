"""Time-of-day visual themes for the ambient display."""

from __future__ import annotations

from dataclasses import dataclass

from homegirl.greeting import Daypart

Color = tuple[int, int, int]


@dataclass(frozen=True)
class BlobSpec:
    """Motion and color settings for one ambient blob."""

    color: Color
    alpha: int
    radius_scale: float
    x_origin: float
    y_origin: float
    x_motion: float
    y_motion: float
    speed: float
    phase: float


@dataclass(frozen=True)
class Theme:
    """A complete daypart palette for background and text treatment."""

    daypart: Daypart
    gradient_top: Color
    gradient_bottom: Color
    vignette: tuple[int, int, int, int]
    text_primary: Color
    text_secondary: Color
    text_accent: Color
    ambient_veil: tuple[int, int, int, int]
    blobs: tuple[BlobSpec, ...]


THEMES: dict[Daypart, Theme] = {
    Daypart.MORNING: Theme(
        daypart=Daypart.MORNING,
        gradient_top=(255, 210, 138),
        gradient_bottom=(248, 104, 138),
        vignette=(54, 38, 34, 72),
        text_primary=(255, 252, 245),
        text_secondary=(247, 238, 226),
        text_accent=(255, 225, 168),
        ambient_veil=(36, 20, 18, 18),
        blobs=(
            BlobSpec((255, 251, 188), 92, 0.46, 0.32, 0.18, 0.10, 0.07, 0.032, 0.0),
            BlobSpec((255, 126, 112), 84, 0.40, 0.82, 0.38, 0.08, 0.09, 0.026, 1.7),
            BlobSpec((255, 126, 174), 70, 0.42, 0.20, 0.76, 0.09, 0.06, 0.021, 3.1),
        ),
    ),
    Daypart.AFTERNOON: Theme(
        daypart=Daypart.AFTERNOON,
        gradient_top=(79, 209, 197),
        gradient_bottom=(31, 138, 188),
        vignette=(26, 48, 72, 70),
        text_primary=(255, 255, 255),
        text_secondary=(235, 247, 250),
        text_accent=(218, 255, 239),
        ambient_veil=(8, 28, 46, 20),
        blobs=(
            BlobSpec((60, 222, 221), 86, 0.47, 0.28, 0.24, 0.10, 0.07, 0.030, 0.4),
            BlobSpec((105, 225, 180), 72, 0.39, 0.76, 0.34, 0.09, 0.09, 0.024, 2.2),
            BlobSpec((34, 113, 188), 64, 0.45, 0.50, 0.78, 0.11, 0.06, 0.019, 4.2),
        ),
    ),
    Daypart.EVENING: Theme(
        daypart=Daypart.EVENING,
        gradient_top=(155, 93, 229),
        gradient_bottom=(120, 35, 165),
        vignette=(48, 24, 35, 88),
        text_primary=(255, 250, 242),
        text_secondary=(244, 226, 216),
        text_accent=(244, 197, 255),
        ambient_veil=(26, 10, 36, 22),
        blobs=(
            BlobSpec((245, 104, 139), 82, 0.44, 0.32, 0.32, 0.09, 0.08, 0.028, 0.3),
            BlobSpec((255, 128, 75), 68, 0.39, 0.82, 0.70, 0.08, 0.06, 0.022, 2.6),
            BlobSpec((91, 45, 174), 72, 0.50, 0.18, 0.76, 0.10, 0.06, 0.018, 4.5),
        ),
    ),
    Daypart.NIGHT: Theme(
        daypart=Daypart.NIGHT,
        gradient_top=(12, 22, 58),
        gradient_bottom=(4, 12, 33),
        vignette=(0, 0, 12, 104),
        text_primary=(246, 249, 255),
        text_secondary=(214, 224, 242),
        text_accent=(166, 211, 255),
        ambient_veil=(0, 0, 16, 28),
        blobs=(
            BlobSpec((30, 58, 168), 72, 0.50, 0.20, 0.30, 0.09, 0.07, 0.022, 0.6),
            BlobSpec((58, 102, 220), 62, 0.42, 0.78, 0.42, 0.08, 0.09, 0.018, 2.4),
            BlobSpec((22, 47, 127), 76, 0.48, 0.52, 0.78, 0.12, 0.06, 0.015, 4.1),
        ),
    ),
}


def get_theme(daypart: Daypart) -> Theme:
    """Return the visual theme for a daypart."""
    return THEMES[daypart]
