"""National Day fetching with once-per-day in-memory caching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import threading
from typing import Any

import requests


@dataclass
class NationalDayState:
    """Snapshot consumed by the UI layer."""

    name: str | None = None
    fetched_for: date | None = None
    is_fetching: bool = False


class NationalDayClient:
    """Fetch and cache the current National Day without blocking rendering."""

    def __init__(self, api_url: str, timeout_seconds: float) -> None:
        self._api_url = api_url
        self._timeout_seconds = timeout_seconds
        self._state = NationalDayState()
        self._lock = threading.Lock()

    def get_state(self, today: date) -> NationalDayState:
        """Return cached state and start a background refresh when needed."""
        with self._lock:
            state = NationalDayState(
                name=self._state.name,
                fetched_for=self._state.fetched_for,
                is_fetching=self._state.is_fetching,
            )
            should_fetch = state.fetched_for != today and not state.is_fetching
            if should_fetch:
                self._state.is_fetching = True

        if should_fetch:
            worker = threading.Thread(
                target=self._fetch_for_day,
                args=(today,),
                name="national-day-fetch",
                daemon=True,
            )
            worker.start()

        return state

    def _fetch_for_day(self, today: date) -> None:
        name: str | None = None
        try:
            response = requests.get(self._api_url, timeout=self._timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            name = self._extract_name(payload)
        except requests.RequestException:
            name = None
        except ValueError:
            name = None
        finally:
            with self._lock:
                self._state = NationalDayState(
                    name=name,
                    fetched_for=today,
                    is_fetching=False,
                )

    def _extract_name(self, payload: Any) -> str | None:
        """Extract a holiday name from common National Day API shapes."""
        names = self._collect_names(payload)
        for name in names:
            if name.lower().startswith("national "):
                return name
        return names[0] if names else None

    def _collect_names(self, payload: Any) -> list[str]:
        """Collect possible holiday names from common JSON response shapes."""
        if isinstance(payload, str):
            value = payload.strip()
            return [value] if value else []

        if isinstance(payload, dict):
            for key in ("national_day", "name", "title", "day", "holiday"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return [value.strip()]

            names: list[str] = []
            for key in ("data", "today", "holidays", "events", "results"):
                nested = payload.get(key)
                names.extend(self._collect_names(nested))
            return names

        if isinstance(payload, list):
            names: list[str] = []
            for item in payload:
                names.extend(self._collect_names(item))
            return names

        return []
