"""Entry point for the Homegirl wall display."""

import logging

from dotenv import load_dotenv

from homegirl.app import HomegirlApp
from homegirl.settings import Settings


def main() -> None:
    """Start the fullscreen ambient display."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    load_dotenv()
    app = HomegirlApp(Settings.from_environment())
    try:
        app.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
