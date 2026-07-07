"""Claude-powered conversational brain for Homegirl."""

from __future__ import annotations

import logging

import anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024

SYSTEM_PROMPT_TEMPLATE = """You are Homegirl, a warm home companion who lives in an ambient \
wall display in {user_name}'s home.

You speak your responses aloud through text-to-speech, so write the way you'd actually \
talk, not the way you'd write: no markdown, no bullet points, no headers, no asterisks. \
Keep replies conversational and reasonably short unless {user_name} clearly wants \
something longer.

Your personality is warm, present, and a little playful — you enjoy the occasional dad \
joke when the moment calls for it, but you don't force it.

One of your regular jobs is leading a compassionate weekly reflection with {user_name}, \
walking through what went well, what was hard, and what they want next week to feel \
like. In that mode, slow down, listen more than you talk, and don't rush to fix things — \
sometimes "that sounds hard" is the whole job."""


class Brain:
    """Wraps the Claude API with Homegirl's persona and a running conversation history."""

    def __init__(self, api_key: str | None, user_name: str) -> None:
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self._system = SYSTEM_PROMPT_TEMPLATE.format(user_name=user_name)
        self._messages: list[dict[str, str]] = []

    @property
    def is_available(self) -> bool:
        """Return whether an API key was configured."""
        return self._client is not None

    def reply(self, user_text: str) -> str | None:
        """Send a user turn and return Homegirl's reply, or None on failure."""
        if not self.is_available:
            return None
        self._messages.append({"role": "user", "content": user_text})
        try:
            response = self._client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=self._system,
                messages=self._messages,
                thinking={"type": "disabled"},
            )
        except Exception:
            logger.exception("Claude API call failed")
            self._messages.pop()
            return None
        reply_text = next((block.text for block in response.content if block.type == "text"), "")
        self._messages.append({"role": "assistant", "content": reply_text})
        return reply_text
