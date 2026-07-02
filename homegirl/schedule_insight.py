"""Derive a human-readable summary of today's schedule.

This produces a plain, rule-based summary today. The plan is to route this
through an on-device LLM later for more natural phrasing — the string this
returns is the seam that call will replace.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homegirl.models.schedule import ScheduleData, ScheduleEvent

DEFAULT_EVENT_DURATION_MINUTES = 60
FREE_GAP_THRESHOLD_MINUTES = 60
DAY_END_HOUR = 21


@dataclass(frozen=True)
class FreeTimeGap:
    """A stretch of open time between two events, or now and the next event."""

    start: datetime
    end: datetime

    @property
    def duration_minutes(self) -> int:
        return round((self.end - self.start).total_seconds() / 60)


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


def get_schedule_headline(schedule: ScheduleData, now: datetime) -> str | None:
    """Return a one-line "you have N things today" sentence naming what's next."""
    if not schedule.is_available:
        return None

    if not schedule.events:
        return "Nothing on your calendar today."

    upcoming = tuple(event for event in schedule.events if _is_upcoming(event, now))
    if not upcoming:
        return "Nothing left on your calendar today."

    count = len(upcoming)
    noun = "thing" if count == 1 else "things"
    named = ", ".join(_describe(event) for event in upcoming[:2])
    return f"You have {count} {noun} today — {named}."


def timed_events_today(schedule: ScheduleData) -> tuple[ScheduleEvent, ...]:
    """Return today's non-all-day events in chronological order for the timeline."""
    return tuple(sorted((e for e in schedule.events if not e.all_day), key=lambda e: e.start))


def get_free_time_gap(schedule: ScheduleData, now: datetime) -> FreeTimeGap | None:
    """Return the largest open gap between today's remaining timed events."""
    events = timed_events_today(schedule)
    if not events:
        return None

    day_end = now.replace(hour=DAY_END_HOUR, minute=0, second=0, microsecond=0)
    boundaries = [max(now, events[0].start)]
    for event in events:
        boundaries.append(event.start)
        boundaries.append(event.end or event.start + timedelta(minutes=DEFAULT_EVENT_DURATION_MINUTES))
    boundaries.append(day_end)
    boundaries = sorted(set(b for b in boundaries if now <= b <= day_end))

    best: FreeTimeGap | None = None
    for start, end in zip(boundaries, boundaries[1:]):
        if _overlaps_event(start, end, events):
            continue
        gap = FreeTimeGap(start=start, end=end)
        if gap.duration_minutes < FREE_GAP_THRESHOLD_MINUTES:
            continue
        if best is None or gap.duration_minutes > best.duration_minutes:
            best = gap

    return best


def _overlaps_event(start: datetime, end: datetime, events: tuple[ScheduleEvent, ...]) -> bool:
    for event in events:
        event_end = event.end or event.start + timedelta(minutes=DEFAULT_EVENT_DURATION_MINUTES)
        if start < event_end and event.start < end:
            return True
    return False


def describe_free_time_gap(gap: FreeTimeGap) -> str:
    """Return a short chip label like "2.5 hrs free" or "45 min free"."""
    if gap.duration_minutes < 60:
        return f"{gap.duration_minutes} min free"

    hours = gap.duration_minutes / 60
    text = f"{hours:.1f}".rstrip("0").rstrip(".")
    return f"{text} hrs free"


def get_free_time_hint(schedule: ScheduleData, now: datetime) -> str | None:
    """Return a short suggestion naming the day's best open window, if any."""
    gap = get_free_time_gap(schedule, now)
    if gap is None:
        return None

    return (
        f"You're free from {_terse_hour(gap.start)} to {_terse_hour(gap.end)} "
        "if you wanted that walk."
    )


def _terse_hour(moment: datetime) -> str:
    if moment.minute == 0:
        return moment.strftime("%I %p").lstrip("0").replace(" AM", "").replace(" PM", "")
    return moment.strftime("%I:%M").lstrip("0")


def group_events_by_day(schedule: ScheduleData) -> dict[date, tuple[ScheduleEvent, ...]]:
    """Group a month's events by calendar day, each day's events sorted by start time."""
    grouped: dict[date, list[ScheduleEvent]] = {}
    for event in sorted(schedule.events, key=lambda e: e.start):
        grouped.setdefault(event.start.date(), []).append(event)
    return {day: tuple(events) for day, events in grouped.items()}
