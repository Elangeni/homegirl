"""Placeholder weekly reflection prompts.

There's no journaling or voice-capture pipeline yet — that's the excluded
voice-overlay work. This just defines a static prompt sequence so the
screen's visual can be reviewed; a real version would advance through the
prompts as the user answers each one aloud and would vary them over time.
"""

from __future__ import annotations

REFLECTION_PROMPTS: tuple[str, ...] = (
    "What went well this week?",
    "What was hard?",
    "What do you want next week to feel like?",
)
