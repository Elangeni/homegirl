"""Derive a human-readable summary of today's schedule.

This produces a plain, rule-based summary today. The plan is to route this
through an on-device LLM later for more natural phrasing — the string this
returns is the seam that call will replace.
"""

from __future__ import annotations

from datetime import datetime

from homegirl.models.schedule import ScheduleData, ScheduleEvent


def get_schedule_summary(schedule: ScheduleData, now: datetime) -> str | None:
    """Return a short summary of today's remaining schedule, or None if unavailable."""
    if not schedule.is_available:
        return None

    if not schedule.events:
        return "Nothing on your calendar today."

    upcoming = tuple(event for event in schedule.events if _is_upcoming(event, now))
    if not upcoming:
        return "Nothing left on your calendar today."

    next_event = upcoming[0]
    remaining = len(upcoming)

    if remaining == 1:
        return f"1 event left today — {_describe(next_event)}."

    return f"{remaining} events left today. Next: {_describe(next_event)}."


def _is_upcoming(event: ScheduleEvent, now: datetime) -> bool:
    if event.all_day:
        return event.start.date() >= now.date()
    return event.end is None or event.end > now


def _describe(event: ScheduleEvent) -> str:
    if event.all_day:
        return event.title
    return f"{event.title} at {_short_time(event.start)}"


def _short_time(moment: datetime) -> str:
    return moment.strftime("%I:%M %p").lstrip("0")
