# Browser entry point for pygbag. web/build.sh copies this next to the
# swoopin package and builds the page into build/web/.
# pygbag only fetches packages it sees imported here, hence `import pygame`.
# numpy is left out (a big download); build.sh pre-renders its blips instead.
import asyncio
import platform

import pygame  # noqa: F401

from swoopin import tuning


def screen_width():
    """Phones and tablets: widen the 960x540 view to the screen's shape (up
    to 1280x540), so a 20:9 phone is filled edge to edge instead of
    letterboxed. Desktop browsers keep 960. Set before the game modules load,
    since they read the width on import."""
    try:
        win = platform.window
        if not win.matchMedia("(pointer: coarse)").matches:
            return 960
        a, b = win.screen.width, win.screen.height
        aspect = max(a, b) / max(1, min(a, b))
    except Exception:
        return 960
    return max(960, min(1280, round(540 * aspect / 2) * 2))


tuning.SCREEN_W = screen_width()

from swoopin.main import run  # noqa: E402

asyncio.run(run())
