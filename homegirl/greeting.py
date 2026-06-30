"""Greeting and daypart helpers."""

from __future__ import annotations

from datetime import datetime
from enum import Enum


class Daypart(str, Enum):
    """Named time blocks that drive copy and background selection."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


def get_daypart(moment: datetime) -> Daypart:
    """Return the daypart for a local datetime."""
    hour = moment.hour
    if 5 <= hour < 12:
        return Daypart.MORNING
    if 12 <= hour < 17:
        return Daypart.AFTERNOON
    if 17 <= hour < 21:
        return Daypart.EVENING
    return Daypart.NIGHT


def get_greeting(moment: datetime) -> str:
    """Return the human-readable greeting for a local datetime."""
    return {
        Daypart.MORNING: "Good Morning",
        Daypart.AFTERNOON: "Good Afternoon",
        Daypart.EVENING: "Good Evening",
        Daypart.NIGHT: "Good Night",
    }[get_daypart(moment)]
