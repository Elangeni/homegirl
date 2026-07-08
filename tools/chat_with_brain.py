"""Interactive CLI to chat with Homegirl's brain and hear her speak the replies.

A keyboard-only way to exercise the brain without tapping the ambient screen
and talking out loud:

    python tools/chat_with_brain.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# pylint: disable=wrong-import-position
from dotenv import load_dotenv

from homegirl.audio import AudioPlayer
from homegirl.brain import Brain
from homegirl.settings import Settings
from homegirl.speech import SpeechSynthesizer

# pylint: enable=wrong-import-position


def main() -> None:
    """Run a text-in, spoken-reply chat loop against the Claude-powered brain."""
    load_dotenv()
    settings = Settings.from_environment()
    brain = Brain(settings.anthropic_api_key, settings.user_name)
    if not brain.is_available:
        print("No ANTHROPIC_API_KEY configured; check your .env file.")
        return

    audio = AudioPlayer(settings.speaker_device_match)
    speech = SpeechSynthesizer(settings.elevenlabs_api_key, settings.elevenlabs_voice_id)

    print("Chatting with Homegirl. Type 'quit' to exit.")
    while True:
        try:
            user_text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_text or user_text.lower() in {"quit", "exit"}:
            break

        reply = brain.reply(user_text)
        if reply is None:
            print("(homegirl didn't respond - check the API key/network)")
            continue

        print(f"homegirl> {reply}")
        if speech.synthesize_to_file(reply, settings.greeting_cache_path):
            audio.play(settings.greeting_cache_path)


if __name__ == "__main__":
    main()
