"""Procedurally synthesised sound: effects plus a small formant voice synth.

Voices (kids yelling for mum, ravens, angry dads) are a buzzy glottal source
pushed through time-varying vowel resonators. The magpie carol is additive
flute-like partials with fast glides and a second, answering voice.
Silent if there is no audio device.
"""

import random

import pygame

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

RATE = 22050


# --------------------------------------------------------------------------
# building blocks
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


def _adsr(n, a=0.02, r=0.1):
    e = np.ones(n)
    na, nr = min(n, _n(a)), min(n, _n(r))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[n - nr:] *= np.linspace(1, 0, nr)
    return e


def _glide(f0, f1, dur, wave="sine"):
    n = _n(dur)
    f = np.geomspace(f0, f1, n)
    ph = np.cumsum(f) / RATE * 2 * np.pi
    if wave == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if wave == "square":
        return np.sign(np.sin(ph))
    return np.sin(ph)


def _noise(dur):
    return np.random.uniform(-1, 1, _n(dur))


def _lowpass(x, k):
    out = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        out[i] = acc
    return out


def _curve(points, n):
    """Piecewise-linear curve through (time_fraction, value) points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return np.interp(np.linspace(0, 1, n), xs, ys)


def _resonate(x, freq, bw):
    """Two-pole resonator with per-sample centre frequency."""
    r = np.exp(-np.pi * bw / RATE)
    a1 = -2 * r * np.cos(2 * np.pi * np.asarray(freq) / RATE)
    a2 = r * r
    g = 1 - r
    a1 = np.broadcast_to(a1, x.shape)
    y = np.empty_like(x)
    y1 = y2 = 0.0
    for i in range(len(x)):
        v = g * x[i] - a1[i] * y1 - a2 * y2
        y[i] = v
        y2, y1 = y1, v
    return y


def _norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def _echo(x, delay=0.09, fb=0.3, taps=3):
    d = _n(delay)
    out = np.concatenate([x, np.zeros(d * taps)])
    for k in range(1, taps + 1):
        out[d * k:d * k + len(x)] += x * (fb ** k)
    return out


def voice(dur, f0, formants, breath=0.08, jitter=0.02, rough=0.0, nasal=None, amp=None):
    """Formant voice.

    f0: list of (t, Hz) pitch points. formants: list of (points, bandwidth, gain)
    where points is a list of (t, Hz). nasal: optional (t, 0..1) points mixing in
    a closed-mouth hum (for 'm'). amp: optional (t, gain) amplitude points.
    """
    n = _n(dur)
    pitch = _curve(f0, n)
    pitch *= 1 + jitter * _lowpass(np.random.uniform(-1, 1, n), 0.02) * 6
    pitch *= 1 + 0.025 * np.sin(np.linspace(0, dur * 2 * np.pi * 5.5, n))  # vibrato
    ph = np.cumsum(pitch) / RATE
    src = 2 * (ph % 1) - 1  # buzzy saw source
    if rough:  # subharmonic growl for harsh calls
        src += rough * np.sign(np.sin(np.pi * ph * 2)) * 0.5
    src += breath * np.random.uniform(-1, 1, n)
    out = np.zeros(n)
    for pts, bw, gain in formants:
        out += gain * _resonate(src, _curve(pts, n), bw)
    if nasal:
        mix = _curve(nasal, n)
        hum = _resonate(src, np.full(n, 280.0), 90) * 1.4
        out = out * (1 - mix) + hum * mix
    e = _adsr(n, 0.02, min(0.12, dur * 0.3))
    if amp:
        e *= _curve(amp, n)
    return out * e


# --------------------------------------------------------------------------
# voices
# --------------------------------------------------------------------------

def _mum():
    """A kid hollering 'MUUUUUM!'"""
    dur = random.uniform(0.85, 1.05)
    base = random.uniform(430, 520)
    f0 = [(0, base * 0.9), (0.15, base * 1.15), (0.6, base * 1.28), (0.85, base * 1.1), (1, base * 0.85)]
    # m -> uh (ʌ) -> m
    nasal = [(0, 1), (0.1, 1), (0.18, 0), (0.8, 0), (0.9, 1), (1, 1)]
    f1 = [(0, 500), (0.18, 900), (0.8, 900), (1, 500)]
    f2 = [(0, 1300), (0.18, 1650), (0.8, 1600), (1, 1300)]
    f3 = [(0, 3000), (1, 3300)]
    v = voice(dur, f0, [(f1, 140, 1.0), (f2, 180, 0.6), (f3, 300, 0.25)], breath=0.12, jitter=0.03,
              nasal=nasal, amp=[(0, 0.6), (0.2, 1), (0.85, 1), (1, 0.5)])
    return _echo(_norm(v))


def _waah():
    """Crying wail: 'WAAAAAH-ah-ah'."""
    dur = 1.0
    base = random.uniform(480, 560)
    f0 = [(0, base * 1.1), (0.2, base * 1.3), (0.7, base * 1.05), (1, base * 0.75)]
    f1 = [(0, 400), (0.15, 1000), (1, 950)]
    f2 = [(0, 900), (0.15, 1650), (1, 1550)]
    sob = [(0, 0.3), (0.12, 1)] + [(0.6 + k * 0.1, 1 if k % 2 == 0 else 0.35) for k in range(5)]
    v = voice(dur, f0, [(f1, 150, 1.0), (f2, 200, 0.55), ([(0, 3200), (1, 3200)], 300, 0.2)],
              breath=0.15, jitter=0.04, amp=sob)
    return _norm(v)


def _scream():
    """Short startled 'AAH!'"""
    dur = 0.45
    base = random.uniform(650, 800)
    f0 = [(0, base), (0.3, base * 1.2), (1, base * 0.9)]
    v = voice(dur, f0, [([(0, 1050), (1, 1000)], 160, 1.0), ([(0, 1700), (1, 1600)], 200, 0.6)],
              breath=0.25, jitter=0.05)
    return _norm(v)


def _raven(syllables=3):
    """Australian raven: drawn-out, wailing 'aaah-aaah-aaaaaah' with a gargle."""
    parts = []
    for k in range(syllables):
        last = k == syllables - 1
        dur = 0.55 if last else 0.3
        f0 = [(0, 330), (0.2, 360), (0.7, 320), (1, 230 if last else 300)]
        f1 = [(0, 650), (0.15, 850), (1, 780)]
        f2 = [(0, 1150), (0.15, 1350), (1, 1250)]
        amp = [(0, 0.5), (0.1, 1), (0.6, 0.9), (1, 0.4 if last else 0.8)]
        v = voice(dur, f0, [(f1, 120, 1.0), (f2, 160, 0.7), ([(0, 2500), (1, 2400)], 260, 0.35)],
                  breath=0.25, jitter=0.06, rough=0.7, amp=amp)
        parts.append(v)
        parts.append(np.zeros(_n(0.07)))
    return _echo(_norm(np.concatenate(parts)), 0.12, 0.25)


def _oi():
    """Angry dad: 'OI!'"""
    dur = 0.42
    f0 = [(0, 150), (0.3, 175), (1, 120)]
    f1 = [(0, 600), (0.45, 560), (0.7, 320), (1, 300)]
    f2 = [(0, 900), (0.45, 950), (0.7, 2000), (1, 2200)]
    v = voice(dur, f0, [(f1, 110, 1.0), (f2, 150, 0.7), ([(0, 2600), (1, 2900)], 250, 0.3)],
              breath=0.15, jitter=0.04, rough=0.4, amp=[(0, 0.7), (0.15, 1), (1, 0.8)])
    return _norm(v)


def _yeah_nah():
    """Dad grumbles, low and short (when he storms off)."""
    v = voice(0.5, [(0, 130), (1, 105)], [([(0, 500), (0.5, 700), (1, 400)], 110, 1.0),
                                          ([(0, 1000), (0.5, 1200), (1, 900)], 150, 0.6)],
              breath=0.2, jitter=0.05, rough=0.5, amp=[(0, 0.6), (0.3, 1), (0.6, 0.4), (0.75, 1), (1, 0.3)])
    return _norm(v) * 0.8


def _carol():
    """Magpie carol: two birds trading rich, fluting, gliding phrases."""
    def phrase(notes, scale=1.0):
        out = []
        for f0, f1, d in notes:
            n = _n(d)
            # fast glide with a little overshoot, plus a throaty 30 Hz warble
            k = np.linspace(0, 1, n)
            f = f0 + (f1 - f0) * (1 - (1 - k) ** 3) * (1 + 0.06 * np.sin(k * np.pi))
            f = f * scale * (1 + 0.025 * np.sin(np.arange(n) / RATE * 2 * np.pi * 31))
            ph = np.cumsum(f) / RATE * 2 * np.pi
            tone = np.sin(ph) + 0.45 * np.sin(2 * ph + 0.3) + 0.2 * np.sin(3 * ph) + 0.08 * np.sin(4 * ph)
            tone += 0.04 * np.random.uniform(-1, 1, n)
            out.append(tone * _adsr(n, 0.015, d * 0.5))
            out.append(np.zeros(_n(random.uniform(0.01, 0.04))))
        return np.concatenate(out)

    a = phrase([(780, 1180, 0.13), (1180, 940, 0.09), (1400, 1720, 0.08), (1720, 1150, 0.16),
                (700, 1050, 0.1), (1050, 1550, 0.18), (1550, 1320, 0.2)])
    b = phrase([(620, 880, 0.12), (880, 700, 0.08), (1050, 1300, 0.1), (1300, 980, 0.15),
                (560, 820, 0.14), (820, 1250, 0.22)], 1.0)
    out = np.zeros(len(a) + _n(0.35) + len(b))
    out[:len(a)] += a
    out[_n(0.55):_n(0.55) + len(b)] += b * 0.8
    return _echo(_norm(out), 0.11, 0.3)


def _chortle():
    """Short pleased magpie warble (big hits / combos)."""
    notes = [(900, 1300, 0.07), (1300, 1050, 0.06), (1200, 1600, 0.09)]
    out = []
    for f0, f1, d in notes:
        n = _n(d)
        f = np.geomspace(f0, f1, n) * (1 + 0.03 * np.sin(np.arange(n) / RATE * 2 * np.pi * 34))
        ph = np.cumsum(f) / RATE * 2 * np.pi
        out.append((np.sin(ph) + 0.4 * np.sin(2 * ph)) * _adsr(n, 0.01, d * 0.5))
    return _norm(np.concatenate(out)) * 0.7


def _clack():
    """Magpie beak snap: two sharp clicks."""
    click = _resonate(np.concatenate([np.random.uniform(-1, 1, 40), np.zeros(_n(0.04))]), 2600, 400)
    return _norm(np.concatenate([click, np.zeros(_n(0.05)), click]))


def _shotgun():
    n = _n(0.9)
    boom = _glide(90, 35, 0.9) * _env(n, 0.001, 0.12) * 1.2
    crack = _lowpass(_noise(0.9), 0.6) * _env(n, 0.0005, 0.05) * 1.5
    tail = _lowpass(_noise(0.9), 0.08) * _env(n, 0.01, 0.35) * 0.8
    return _echo(_norm(boom + crack + tail), 0.18, 0.35)


def _pump():
    """Shotgun pump: chk-chk."""
    def chk():
        return _resonate(np.random.uniform(-1, 1, _n(0.03)), 1400, 500) * _env(_n(0.03), 0.001, 0.01)
    return _norm(np.concatenate([chk(), np.zeros(_n(0.08)), chk()])) * 0.6


def _chatter():
    chit = _glide(3200, 2600, 0.035) * _env(_n(0.035), 0.001, 0.012)
    return np.concatenate([chit, np.zeros(_n(0.03))] * 5) * 0.5


def build():
    s = {}
    s["flap"] = _lowpass(_noise(0.09), 0.25) * _env(_n(0.09), 0.002, 0.03) * 1.4
    whoosh = (_lowpass(_noise(0.35), 0.12) * 1.5 + 0.2 * _glide(500, 180, 0.35)) * _env(_n(0.35), 0.08, 0.2)
    clack = _clack()
    whoosh[:len(clack)] += clack * 0.4
    s["swoop"] = whoosh
    s["bang"] = (_glide(180, 50, 0.22) * 0.9 + _lowpass(_noise(0.22), 0.4) * 0.6) * _env(_n(0.22), 0.001, 0.08)
    s["claw"] = np.concatenate([_noise(0.04) * _env(_n(0.04), 0.001, 0.015), np.zeros(_n(0.02))] * 3)
    s["peck"] = _glide(1400, 900, 0.05) * _env(_n(0.05), 0.001, 0.02)
    s["eye"] = np.concatenate([s["bang"], _glide(1800, 2600, 0.15) * _env(_n(0.15), 0.005, 0.1) * 0.5])
    s["ko"] = np.concatenate([_glide(f, f, 0.12) * _env(_n(0.12), 0.002, 0.08) for f in (1568, 1175, 784)])
    s["crack"] = _lowpass(_noise(0.12), 0.7) * _env(_n(0.12), 0.001, 0.03) * 1.2
    meow = np.concatenate([_glide(600, 900, 0.12, "saw"), _glide(900, 450, 0.25, "saw")]) * 0.3
    s["meow"] = meow * _env(len(meow), 0.02, 0.25)
    s["chatter"] = _chatter()
    s["thud"] = _glide(120, 40, 0.18) * _env(_n(0.18), 0.001, 0.06)
    s["hurt"] = _glide(1200, 500, 0.18, "square") * _env(_n(0.18), 0.001, 0.08) * 0.25
    s["egg"] = _glide(800, 1600, 0.25) * _env(_n(0.25), 0.01, 0.15) * 0.6
    s["carol"] = _carol()
    s["chortle"] = _chortle()
    s["caw"] = _raven(1)
    s["caaaw"] = _raven(3)
    s["oi"] = _oi()
    s["grumble"] = _yeah_nah()
    s["shotgun"] = _shotgun()
    s["pump"] = _pump()
    # a few takes of each kid voice so it doesn't get samey
    for i in range(3):
        s[f"mum{i}"] = _mum()
        s[f"waah{i}"] = _waah()
        s[f"scream{i}"] = _scream()
    return s


VARIANTS = {"mum": 3, "waah": 3, "scream": 3}
VOLUME = {"carol": 0.7, "mum": 0.75, "waah": 0.6, "scream": 0.55, "caw": 0.6, "caaaw": 0.6, "oi": 0.8,
          "shotgun": 0.9, "grumble": 0.6}


class Audio:
    def __init__(self, enabled=True):
        self.sounds = {}
        self.ok = False
        self.last = {}
        if not enabled or np is None:
            return
        try:
            pygame.mixer.pre_init(RATE, -16, 1, 512)
            pygame.mixer.init(RATE, -16, 1, 512)
            pygame.mixer.set_num_channels(32)
            self.sounds = {k: self._sound(v) for k, v in build().items()}
            self.ok = True
        except Exception:
            self.sounds = {}

    @staticmethod
    def _sound(x):
        x = np.clip(x * 0.45, -1, 1)
        return pygame.mixer.Sound(buffer=(x * 32767).astype(np.int16).tobytes())

    def play(self, name, vol=1.0, min_gap=0.0):
        if name in VARIANTS:
            key = f"{name}{random.randrange(VARIANTS[name])}"
        else:
            key = name
        snd = self.sounds.get(key)
        if snd is None:
            return
        now = pygame.time.get_ticks() / 1000
        if min_gap and now - self.last.get(name, -99) < min_gap:
            return
        self.last[name] = now
        ch = snd.play()
        if ch:
            ch.set_volume(vol * VOLUME.get(name, 1.0) * random.uniform(0.85, 1.0))
