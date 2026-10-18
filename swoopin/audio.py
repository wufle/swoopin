"""Procedurally synthesised sound effects. Silent if no audio device."""

import random

import pygame

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

RATE = 22050


def _env(n, attack=0.005, release=0.3):
    t = np.linspace(0, 1, n, endpoint=False)
    a = max(1, int(attack * RATE))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e *= np.exp(-t * (1 / max(release, 1e-3)))
    return e


def _glide(f0, f1, dur, wave="sine"):
    n = int(dur * RATE)
    f = np.geomspace(f0, f1, n)
    ph = np.cumsum(f) / RATE * 2 * np.pi
    if wave == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if wave == "square":
        return np.sign(np.sin(ph))
    return np.sin(ph)


def _noise(dur):
    return np.random.uniform(-1, 1, int(dur * RATE))


def _lowpass(x, k):
    out = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        out[i] = acc
    return out


def _to_sound(x, vol=0.5):
    x = np.clip(x * vol, -1, 1)
    data = (x * 32767).astype(np.int16)
    return pygame.mixer.Sound(buffer=data.tobytes())


def _carol():
    """Magpie carol: warbling, flute-like glides with a harmonic."""
    notes = [(900, 1300, 0.16), (1300, 1050, 0.12), (1500, 1700, 0.1), (1700, 1200, 0.18),
             (800, 1100, 0.14), (1100, 1600, 0.2), (1600, 1400, 0.22)]
    parts = []
    for f0, f1, d in notes:
        n = int(d * RATE)
        vib = 1 + 0.02 * np.sin(np.linspace(0, d * 2 * np.pi * 28, n))
        f = np.geomspace(f0, f1, n) * vib
        ph = np.cumsum(f) / RATE * 2 * np.pi
        tone = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3.01 * ph)
        parts.append(tone * _env(n, 0.02, d * 1.6))
        parts.append(np.zeros(int(0.025 * RATE)))
    return np.concatenate(parts)


def build():
    s = {}
    s["flap"] = _lowpass(_noise(0.09), 0.25) * _env(int(0.09 * RATE), 0.002, 0.03) * 1.4
    s["swoop"] = (_lowpass(_noise(0.35), 0.12) * 1.5 + 0.2 * _glide(500, 180, 0.35)) * _env(int(0.35 * RATE), 0.08, 0.2)
    hit_n = int(0.22 * RATE)
    s["bang"] = (_glide(180, 50, 0.22) * 0.9 + _lowpass(_noise(0.22), 0.4) * 0.6) * _env(hit_n, 0.001, 0.08)
    claw = np.concatenate([_noise(0.04) * _env(int(0.04 * RATE), 0.001, 0.015), np.zeros(int(0.02 * RATE))] * 3)
    s["claw"] = claw
    s["peck"] = _glide(1400, 900, 0.05) * _env(int(0.05 * RATE), 0.001, 0.02)
    s["eye"] = np.concatenate([s["bang"], _glide(1800, 2600, 0.15) * _env(int(0.15 * RATE), 0.005, 0.1) * 0.5])
    s["ko"] = np.concatenate([_glide(f, f, 0.12) * _env(int(0.12 * RATE), 0.002, 0.08) for f in (1568, 1175, 784)])
    s["waah"] = _glide(700, 380, 0.5, "saw") * _env(int(0.5 * RATE), 0.03, 0.35) * 0.35
    s["crack"] = _lowpass(_noise(0.12), 0.7) * _env(int(0.12 * RATE), 0.001, 0.03) * 1.2
    s["caw"] = _glide(520, 380, 0.25, "saw") * _env(int(0.25 * RATE), 0.01, 0.12) * 0.4
    meow = np.concatenate([_glide(600, 900, 0.12, "saw"), _glide(900, 450, 0.25, "saw")]) * 0.3
    s["meow"] = meow * _env(len(meow), 0.02, 0.25)
    chit = _glide(3200, 2600, 0.035) * _env(int(0.035 * RATE), 0.001, 0.012)
    s["chatter"] = np.concatenate([chit, np.zeros(int(0.03 * RATE))] * 5) * 0.5
    s["thud"] = _glide(120, 40, 0.18) * _env(int(0.18 * RATE), 0.001, 0.06)
    s["hurt"] = _glide(1200, 500, 0.18, "square") * _env(int(0.18 * RATE), 0.001, 0.08) * 0.25
    s["egg"] = _glide(800, 1600, 0.25) * _env(int(0.25 * RATE), 0.01, 0.15) * 0.6
    s["carol"] = _carol()
    s["tick"] = _glide(1000, 1000, 0.03) * _env(int(0.03 * RATE), 0.001, 0.01) * 0.4
    return s


class Audio:
    def __init__(self, enabled=True):
        self.sounds = {}
        self.ok = False
        if not enabled or np is None:
            return
        try:
            pygame.mixer.pre_init(RATE, -16, 1, 512)
            pygame.mixer.init(RATE, -16, 1, 512)
            pygame.mixer.set_num_channels(24)
            self.sounds = {k: _to_sound(v, 0.45) for k, v in build().items()}
            self.ok = True
        except Exception:
            self.sounds = {}

    def play(self, name, vol=1.0):
        snd = self.sounds.get(name)
        if snd is None:
            return
        ch = snd.play()
        if ch:
            ch.set_volume(vol * random.uniform(0.85, 1.0))
