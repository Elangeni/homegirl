"""Screen state for waking Homegirl into app mode."""

from __future__ import annotations

from enum import Enum


class Screen(str, Enum):
    """Top-level display modes."""

    AMBIENT = "ambient"
    APP = "app"
    WEATHER = "weather"
    CALENDAR = "calendar"
    CELEBRATION = "celebration"
    REFLECTION = "reflection"


_RETURN_SCREEN: dict[Screen, Screen] = {
    Screen.WEATHER: Screen.APP,
    Screen.CALENDAR: Screen.APP,
    Screen.CELEBRATION: Screen.AMBIENT,
    Screen.REFLECTION: Screen.AMBIENT,
}


class WakeController:
    """Switch between ambient, app, and detail screens based on activity."""

    def __init__(self, idle_timeout_seconds: float) -> None:
        self._idle_timeout_seconds = idle_timeout_seconds
        self._screen = Screen.AMBIENT
        self._inactive_seconds = 0.0

    @property
    def screen(self) -> Screen:
        return self._screen

    def show(self, screen: Screen) -> None:
        """Navigate directly to a screen."""
        self._screen = screen
        self._inactive_seconds = 0.0

    def show_weather(self) -> None:
        """Navigate to the weather detail screen."""
        self.show(Screen.WEATHER)

    def show_calendar(self) -> None:
        """Navigate to the calendar detail screen."""
        self.show(Screen.CALENDAR)

    def show_celebration(self) -> None:
        """Navigate to the celebration takeover screen."""
        self.show(Screen.CELEBRATION)

    def show_reflection(self) -> None:
        """Navigate to the weekly reflection screen."""
        self.show(Screen.REFLECTION)

    def show_app(self) -> None:
        """Return to the app grid screen."""
        self.show(Screen.APP)

    def dismiss(self) -> None:
        """Return from the current detail screen to where it was reached from."""
        self.show(_RETURN_SCREEN.get(self._screen, Screen.AMBIENT))

    def update(self, delta_seconds: float, had_activity: bool) -> Screen:
        """Advance the idle timer for the current frame.

        Navigating between screens (including waking from ambient) happens
        explicitly via ``show()``/``dismiss()`` in the input handlers, so this
        only has to track the idle timeout back to ambient.
        """
        if had_activity:
            self._inactive_seconds = 0.0
            return self._screen

        if self._screen != Screen.AMBIENT:
            self._inactive_seconds += delta_seconds
            if self._inactive_seconds >= self._idle_timeout_seconds:
                self._screen = Screen.AMBIENT
                self._inactive_seconds = 0.0

        return self._screen
