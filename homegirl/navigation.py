"""Screen state for waking Homegirl into app mode."""

from __future__ import annotations

from enum import Enum


class Screen(str, Enum):
    """Top-level display modes."""

    AMBIENT = "ambient"
    APP = "app"


class WakeController:
    """Switch between ambient and app screens based on activity."""

    def __init__(self, idle_timeout_seconds: float) -> None:
        self._idle_timeout_seconds = idle_timeout_seconds
        self._screen = Screen.AMBIENT
        self._inactive_seconds = 0.0

    @property
    def screen(self) -> Screen:
        return self._screen

    def update(self, delta_seconds: float, had_activity: bool) -> Screen:
        """Advance screen state for the current frame."""
        if had_activity:
            self._screen = Screen.APP
            self._inactive_seconds = 0.0
            return self._screen

        if self._screen == Screen.APP:
            self._inactive_seconds += delta_seconds
            if self._inactive_seconds >= self._idle_timeout_seconds:
                self._screen = Screen.AMBIENT
                self._inactive_seconds = 0.0

        return self._screen
