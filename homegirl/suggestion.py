"""Placeholder proactive suggestion shown as a card on the ambient screen.

There is no suggestion engine yet — this is a stand-in with static copy so the
visual can be reviewed. A future version would replace ``PLACEHOLDER`` with
suggestions generated from real signals (habits, calendar gaps, etc.), and
``confirm()`` would trigger the corresponding action instead of just
dismissing the card.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Suggestion:
    """A single proactive suggestion with two possible responses."""

    body: str
    confirm_label: str = "Sure"
    dismiss_label: str = "Not now"


PLACEHOLDER = Suggestion(
    body="You haven't had sewing time this week — want me to block Saturday afternoon?",
)


class SuggestionState:
    """Tracks whether the placeholder suggestion is still active this session."""

    def __init__(self, suggestion: Suggestion = PLACEHOLDER) -> None:
        self._suggestion = suggestion
        self._dismissed = False

    @property
    def active(self) -> Suggestion | None:
        """Return the suggestion to display, or None once dismissed."""
        return None if self._dismissed else self._suggestion

    def confirm(self) -> None:
        """Handle the affirmative response. No real action exists yet."""
        self._dismissed = True

    def dismiss(self) -> None:
        """Handle the negative response, or hide the card outright."""
        self._dismissed = True
