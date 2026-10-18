# Browser entry point for pygbag. web/build.sh copies this next to the
# swoopin package and builds the page into build/web/.
# pygbag only fetches packages it sees imported here, hence `import pygame`.
# numpy is left out (a big download); build.sh pre-renders its blips instead.
import asyncio

import pygame  # noqa: F401

from swoopin.main import run

asyncio.run(run())
