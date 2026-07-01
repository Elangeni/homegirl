"""Visual transitions between top-level screens."""

from __future__ import annotations

from homegirl.navigation import Screen


class ScreenTransition:
    """Track a smooth transition from one screen to another."""

    def __init__(self, initial_screen: Screen, duration_seconds: float) -> None:
        self._duration_seconds = max(0.001, duration_seconds)
        self._source_screen: Screen | None = None
        self._target_screen = initial_screen
        self._elapsed_seconds = duration_seconds

    @property
    def is_active(self) -> bool:
        return self._source_screen is not None

    @property
    def source_screen(self) -> Screen:
        return self._source_screen or self._target_screen

    @property
    def target_screen(self) -> Screen:
        return self._target_screen

    @property
    def progress(self) -> float:
        raw_progress = min(1.0, self._elapsed_seconds / self._duration_seconds)
        return _ease_in_out(raw_progress)

    @property
    def target_alpha(self) -> int:
        return round(255 * self.progress)

    def update(self, target_screen: Screen, delta_seconds: float) -> None:
        """Advance the transition toward the requested screen."""
        if target_screen != self._target_screen:
            self._source_screen = self._target_screen
            self._target_screen = target_screen
            self._elapsed_seconds = 0.0
            return

        if self._source_screen is None:
            return

        self._elapsed_seconds += delta_seconds
        if self._elapsed_seconds >= self._duration_seconds:
            self._source_screen = None
            self._elapsed_seconds = self._duration_seconds


def _ease_in_out(progress: float) -> float:
    """Smoothstep easing for opacity transitions."""
    return progress * progress * (3.0 - (2.0 * progress))
