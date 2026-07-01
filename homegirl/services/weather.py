"""OpenWeather Current Weather API integration with in-memory caching."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
import threading
from typing import Any

import requests

from homegirl.models.weather import WeatherData


LAT = 37.7749
LON = -122.4194
OPENWEATHER_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_CACHE_SECONDS = 30 * 60

logger = logging.getLogger(__name__)


class WeatherService:
    """Fetch and cache weather without exposing API responses to the UI."""

    def __init__(
        self,
        api_key: str | None,
        timeout_seconds: float,
        refresh_interval_seconds: int = WEATHER_CACHE_SECONDS,
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._refresh_interval = timedelta(seconds=refresh_interval_seconds)
        self._weather = WeatherData(error="Weather unavailable")
        self._is_fetching = False
        self._logged_cached_update: datetime | None = None
        self._reported_missing_key = False
        self._lock = threading.Lock()

    def get_weather(self, now: datetime) -> WeatherData:
        """Return cached weather and start a background refresh when needed."""
        if not self._api_key:
            if not self._reported_missing_key:
                logger.info("OpenWeather API key is missing; weather is unavailable.")
                self._reported_missing_key = True
            return self._weather

        with self._lock:
            weather = self._weather
            should_refresh = self._should_refresh(weather, now) and not self._is_fetching
            if should_refresh:
                self._is_fetching = True

        if should_refresh:
            worker = threading.Thread(
                target=self._refresh_weather,
                args=(now,),
                name="weather-fetch",
                daemon=True,
            )
            worker.start()
        elif weather.is_available and weather.last_updated != self._logged_cached_update:
            logger.info("Using cached weather from %s.", weather.last_updated)
            self._logged_cached_update = weather.last_updated

        return weather

    def _should_refresh(self, weather: WeatherData, now: datetime) -> bool:
        if weather.last_updated is None:
            return True
        return now - weather.last_updated >= self._refresh_interval

    def _refresh_weather(self, now: datetime) -> None:
        try:
            weather = self._fetch_weather(now)
        except requests.RequestException as exc:
            logger.warning("OpenWeather request failed: %s", exc)
            self._keep_cache_or_error("Weather unavailable")
            return
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            logger.warning("OpenWeather response could not be parsed: %s", exc)
            self._keep_cache_or_error("Weather unavailable")
            return

        with self._lock:
            self._weather = weather
            self._logged_cached_update = None
            self._is_fetching = False
        logger.info("Weather updated successfully.")

    def _fetch_weather(self, now: datetime) -> WeatherData:
        response = requests.get(
            OPENWEATHER_CURRENT_URL,
            params={
                "lat": LAT,
                "lon": LON,
                "appid": self._api_key,
                "units": "imperial",
            },
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return self._parse_weather(payload, now)

    def _parse_weather(self, payload: Any, now: datetime) -> WeatherData:
        if not isinstance(payload, dict):
            raise ValueError("weather payload is not an object")

        main = _dict_value(payload, "main")
        wind = _dict_value(payload, "wind")
        weather_items = _list_value(payload, "weather")
        first_condition = _dict_item(weather_items, 0)

        return WeatherData(
            current_temp=_float_value(main, "temp"),
            feels_like=_float_value(main, "feels_like"),
            condition_main=_string_value(first_condition, "main"),
            condition=_string_value(first_condition, "description"),
            high_temp=_float_value(main, "temp_max"),
            low_temp=_float_value(main, "temp_min"),
            humidity=_int_value(main, "humidity"),
            wind_speed=_float_value(wind, "speed"),
            last_updated=now,
        )

    def _keep_cache_or_error(self, error: str) -> None:
        with self._lock:
            if self._weather.is_available:
                logger.info("Using stale cached weather from %s.", self._weather.last_updated)
                self._is_fetching = False
                return

            self._weather = WeatherData(error=error)
            self._is_fetching = False


def _dict_value(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload[key]
    if not isinstance(value, dict):
        raise TypeError(f"{key} is not an object")
    return value


def _list_value(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload[key]
    if not isinstance(value, list):
        raise TypeError(f"{key} is not a list")
    return value


def _dict_item(items: list[Any], index: int) -> dict[str, Any]:
    value = items[index]
    if not isinstance(value, dict):
        raise TypeError(f"item {index} is not an object")
    return value


def _float_value(payload: dict[str, Any], key: str) -> float:
    value = payload[key]
    if not isinstance(value, (int, float)):
        raise TypeError(f"{key} is not a number")
    return float(value)


def _int_value(payload: dict[str, Any], key: str) -> int:
    value = payload[key]
    if not isinstance(value, int):
        raise TypeError(f"{key} is not an integer")
    return value


def _string_value(payload: dict[str, Any], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{key} is not text")
    return value.strip()
