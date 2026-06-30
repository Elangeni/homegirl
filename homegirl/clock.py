"""Clock formatting utilities."""

from __future__ import annotations

from datetime import datetime


def now_local() -> datetime:
    """Return the local system time."""
    return datetime.now().astimezone()


def format_time(moment: datetime) -> str:
    """Format time for a glanceable wall display."""
    return moment.strftime("%I:%M %p").lstrip("0")


def format_date(moment: datetime) -> str:
    """Format the full date shown below the clock."""
    return moment.strftime("%A, %B %-d, %Y")
