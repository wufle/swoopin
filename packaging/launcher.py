"""Entry point for the packaged game (PyInstaller can't run `python -m`)."""

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from swoopin.main import main  # noqa: E402

if __name__ == "__main__":
    main()
