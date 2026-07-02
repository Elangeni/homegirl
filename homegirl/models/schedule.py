"""Typed schedule snapshot for Homegirl features."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ScheduleEvent:
    """One calendar event for today."""

    title: str
    start: datetime
    end: datetime | None = None
    all_day: bool = False


@dataclass(frozen=True)
class ScheduleData:
    """Today's calendar events the UI and future features can safely consume."""

    events: tuple[ScheduleEvent, ...] = ()
    last_updated: datetime | None = None
    error: str | None = None

    @property
    def is_available(self) -> bool:
        """Return whether this snapshot reflects a successful fetch."""
        return self.error is None and self.last_updated is not None
