"""Claude-powered conversational brain for Homegirl."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator

import anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024

# Splits on the whitespace that follows sentence-ending punctuation, so each
# yielded piece is a complete sentence ready to hand to text-to-speech.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")

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

    def reply_stream(self, user_text: str) -> Iterator[str]:
        """Send a user turn and yield Homegirl's reply one sentence at a time.

        Yields nothing if the brain is unavailable or the request fails.
        Sentence-sized chunks let a caller start synthesizing and speaking
        the start of the reply while Claude is still generating the rest,
        instead of waiting for the full response before saying anything.
        """
        if not self.is_available:
            return
        self._messages.append({"role": "user", "content": user_text})
        full_text = ""
        buffer = ""
        failed = False
        try:
            with self._client.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=self._system,
                messages=self._messages,
                thinking={"type": "disabled"},
            ) as stream:
                for delta in stream.text_stream:
                    full_text += delta
                    buffer += delta
                    *complete, buffer = _SENTENCE_BREAK.split(buffer)
                    yield from complete
            if buffer.strip():
                yield buffer
        except Exception:
            logger.exception("Claude API call failed")
            failed = True
        finally:
            if failed or not full_text:
                self._messages.pop()
            else:
                self._messages.append({"role": "assistant", "content": full_text})
