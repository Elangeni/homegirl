"""Derive human-readable weather summaries from forecast data."""

from __future__ import annotations

from homegirl.greeting import Daypart
from homegirl.models.weather import HourlyForecast, WeatherData

RAIN_CHANCE_THRESHOLD = 50


def get_headline(weather: WeatherData) -> str | None:
    """Return a one-line summary of what's changing in the next few hours."""
    if not weather.is_available or not weather.hourly:
        return None

    if _is_rain_likely(weather.hourly[0]):
        return "Rain for now — clearer skies later today."

    rainy_hour = next((hour for hour in weather.hourly if _is_rain_likely(hour)), None)
    if rainy_hour is None:
        return "Clear skies for the rest of the day."

    return f"Rain moves in around {_short_hour(rainy_hour)} — clear skies until then."


def get_advice(weather: WeatherData, daypart: Daypart) -> str | None:
    """Return a short, situational tip for the current conditions."""
    if not weather.is_available:
        return None

    if weather.hourly and _is_rain_likely(weather.hourly[0]):
        return "Grab an umbrella before you head out."

    if daypart == Daypart.MORNING:
        return "Good time for a morning walk."
    if daypart == Daypart.AFTERNOON:
        return "Good time to get outside."
    if daypart == Daypart.EVENING:
        return "Nice evening for a walk."
    return "Bundle up if you're heading out."


def _is_rain_likely(hour: HourlyForecast) -> bool:
    return hour.chance_of_rain is not None and hour.chance_of_rain >= RAIN_CHANCE_THRESHOLD


def _short_hour(hour: HourlyForecast) -> str:
    return hour.time.strftime("%I %p").lstrip("0")
