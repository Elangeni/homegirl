"""Typed weather snapshot for Homegirl features."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WeatherData:
    """Weather values the UI and future features can safely consume."""

    current_temp: float | None = None
    feels_like: float | None = None
    condition_main: str | None = None
    condition: str | None = None
    high_temp: float | None = None
    low_temp: float | None = None
    rain_chance: float | None = None
    humidity: int | None = None
    wind_speed: float | None = None
    last_updated: datetime | None = None
    error: str | None = None

    @property
    def is_available(self) -> bool:
        """Return whether the snapshot contains displayable weather."""
        return self.current_temp is not None
