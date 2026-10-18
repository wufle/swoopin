"""Sound: real recordings from swoopin/sounds/ plus a few synthesised blips.

Recordings are CC0 / CC BY-SA, credited in swoopin/sounds/CREDITS.md. Files
named like scream0.ogg, scream1.ogg are variants of "scream"; one is picked
at random each time. Silent if there is no audio device.
"""

import random
import re
from pathlib import Path

import pygame

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

RATE = 44100
SOUND_DIR = Path(__file__).parent / "sounds"

# game event -> recording name, where they differ
ALIASES = {
    "swoop": "swoosh",
    "eye": "thump",
    "waah": "scream",
}
VOLUME = {
    "carol": 0.55, "chortle": 0.6, "caw": 0.55, "caaaw": 0.5, "chatter": 0.6, "meow": 0.6, "hiss": 0.6,
    "mum": 0.85, "scream": 0.5, "oi": 0.9, "grumble": 0.7, "yell": 0.7, "shotgun": 0.75, "pump": 0.6,
    "bang": 0.8, "thump": 0.85, "swoosh": 0.6, "flap": 0.35, "crack": 0.8, "thud": 0.7,
}


# --------------------------------------------------------------------------
# synthesised blips (no recording needed)
# --------------------------------------------------------------------------

def _n(dur):
    return int(dur * RATE)


def _env(n, attack=0.005, release=0.3):
    t = np.linspace(0, 1, n, endpoint=False)
    a = max(1, int(attack * RATE))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e *= np.exp(-t * (1 / max(release, 1e-3)))
    return e


def _glide(f0, f1, dur, wave="sine"):
    n = _n(dur)
    ph = np.cumsum(np.geomspace(f0, f1, n)) / RATE * 2 * np.pi
    if wave == "square":
        return np.sign(np.sin(ph))
    return np.sin(ph)


def _noise(dur):
    return np.random.uniform(-1, 1, _n(dur))


def synth():
    s = {}
    s["claw"] = np.concatenate([_noise(0.04) * _env(_n(0.04), 0.001, 0.015), np.zeros(_n(0.02))] * 3) * 0.6
    s["peck"] = _glide(1400, 900, 0.05) * _env(_n(0.05), 0.001, 0.02)
    s["ko"] = np.concatenate([_glide(f, f, 0.12) * _env(_n(0.12), 0.002, 0.08) for f in (1568, 1175, 784)]) * 0.6
    s["egg"] = _glide(800, 1600, 0.25) * _env(_n(0.25), 0.01, 0.15) * 0.6
    s["hurt"] = _glide(1200, 500, 0.18, "square") * _env(_n(0.18), 0.001, 0.08) * 0.25
    return s


class Audio:
    def __init__(self, enabled=True):
        self.sounds = {}  # name -> [Sound, ...]
        self.ok = False
        self.last = {}
        if not enabled:
            return
        try:
            pygame.mixer.pre_init(RATE, -16, 1, 512)
            pygame.mixer.init(RATE, -16, 1, 512)
            pygame.mixer.set_num_channels(32)
        except Exception:
            return
        self.ok = True
        if np is not None:
            for name, x in synth().items():
                data = (np.clip(x * 0.45, -1, 1) * 32767).astype(np.int16)
                self.sounds[name] = [pygame.mixer.Sound(buffer=data.tobytes())]
        for path in sorted(SOUND_DIR.glob("*.ogg")):
            name = re.sub(r"\d+$", "", path.stem)
            try:
                self.sounds.setdefault(name, []).append(pygame.mixer.Sound(path))
            except pygame.error:
                pass

    def play(self, name, vol=1.0, min_gap=0.0):
        key = ALIASES.get(name, name)
        variants = self.sounds.get(key)
        if not variants:
            return
        now = pygame.time.get_ticks() / 1000
        if min_gap and now - self.last.get(key, -99) < min_gap:
            return
        self.last[key] = now
        ch = random.choice(variants).play()
        if ch:
            ch.set_volume(min(1.0, vol * VOLUME.get(key, 1.0) * random.uniform(0.85, 1.0)))
