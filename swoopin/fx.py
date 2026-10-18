"""Comic-book hit text, particles, physics props, screen shake."""

import math
import random

import pygame

from . import art
from . import palette as P
from . import tuning as T

_fonts = {}


def font(size, bold=True, italic=True):
    key = (size, bold, italic)
    if key not in _fonts:
        try:
            f = pygame.font.SysFont("liberationsans,dejavusans,notosans,arial", size, bold=bold, italic=italic)
        except Exception:
            f = pygame.font.Font(None, size)
        _fonts[key] = f
    return _fonts[key]


def outlined_text(text, size, fill, outline, shadow=None, thick=3, italic=True):
    f = font(size, italic=italic)
    base = f.render(text, True, fill)
    w, h = base.get_size()
    pad = thick + 5
    s = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    if shadow:
        sh = f.render(text, True, shadow)
        for dx in range(-thick, thick + 1):
            for dy in range(-thick, thick + 1):
                if dx * dx + dy * dy <= thick * thick:
                    s.blit(sh, (pad + dx + 4, pad + dy + 4))
    ol = f.render(text, True, outline)
    for dx in range(-thick, thick + 1):
        for dy in range(-thick, thick + 1):
            if dx * dx + dy * dy <= thick * thick:
                s.blit(ol, (pad + dx, pad + dy))
    s.blit(base, (pad, pad))
    return s


STYLES = {
    # burst fill, text fill, text outline
    "hit": (P.BONE, P.WATTLE, P.WARATAH),
    "big": (P.WARATAH, P.WATTLE, P.CHARCOAL),
    "ko": (P.WATTLE, P.BONE, P.WARATAH),
    "bad": (P.CHARCOAL, P.WARATAH, P.BONE),
    "good": (P.EUCALYPT, P.BONE, P.DEEP_GUM),
    "plain": (None, P.WATTLE, P.CHARCOAL),
}


class ComicText:
    def __init__(self, text, pos, style="hit", size=30, life=T.COMIC_TEXT_TIME, drift=-30):
        self.pos = [pos[0], pos[1]]
        self.t = 0.0
        self.life = life
        self.drift = drift
        self.style = style
        self.tilt = random.uniform(-14, 14)
        self.wobble_phase = random.uniform(0, math.tau)
        burst_col, fill, outline = STYLES[style]
        txt = outlined_text(text, size, fill, outline, P.COMIC_SHADOW, thick=3)
        tw, th = txt.get_size()
        if burst_col is None:
            self.surf = txt
        else:
            bw, bh = int(tw * 1.25) + 20, int(th * 1.6) + 16
            s = pygame.Surface((bw, bh), pygame.SRCALPHA)
            cx, cy = bw / 2, bh / 2
            pts = []
            n = 16
            for i in range(n * 2):
                a = i * math.pi / n + random.uniform(-0.08, 0.08)
                r = 1.0 if i % 2 == 0 else random.uniform(0.62, 0.78)
                pts.append((cx + math.cos(a) * (bw / 2 - 2) * r, cy + math.sin(a) * (bh / 2 - 2) * r))
            pygame.draw.polygon(s, burst_col, pts)
            pygame.draw.polygon(s, P.CHARCOAL, pts, 3)
            s.blit(txt, (cx - tw / 2, cy - th / 2))
            self.surf = s

    @property
    def alive(self):
        return self.t < self.life

    def update(self, dt):
        self.t += dt
        self.pos[1] += self.drift * dt

    def draw(self, dst, cam):
        k = self.t / self.life
        if k < 0.12:
            scale = 1.5 - (k / 0.12) * 0.5
        else:
            scale = 1.0 + 0.04 * math.sin(self.t * 30)
        angle = self.tilt + 6 * math.sin(self.t * 18 + self.wobble_phase) * (1 - k)
        img = pygame.transform.rotozoom(self.surf, angle, scale)
        if k > 0.65:
            img.set_alpha(int(255 * (1 - (k - 0.65) / 0.35)))
        x = self.pos[0] - cam[0]
        y = self.pos[1] - cam[1]
        dst.blit(img, (x - img.get_width() / 2, y - img.get_height() / 2))


class Particle:
    """Feathers, leaves, fur: drift and flutter, no collision."""

    def __init__(self, kind, pos, vel, life=1.2):
        self.kind = kind
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.t = 0.0
        self.life = life
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-400, 400)
        self.surf, self.anchor = art.draw_prop(kind)

    @property
    def alive(self):
        return self.t < self.life

    def update(self, dt):
        self.t += dt
        self.vel[0] *= 1 - 2.5 * dt
        self.vel[1] = self.vel[1] * (1 - 2.5 * dt) + 160 * dt
        self.pos[0] += (self.vel[0] + math.sin(self.t * 9 + self.angle) * 30) * dt
        self.pos[1] += self.vel[1] * dt
        self.angle += self.spin * dt

    def draw(self, dst, cam):
        a = 255 if self.t < self.life * 0.7 else int(255 * (1 - (self.t - self.life * 0.7) / (self.life * 0.3)))
        art.blit_actor(dst, self.surf, self.anchor, (self.pos[0] - cam[0], self.pos[1] - cam[1]), 1, self.angle,
                       max(0, a))


class Prop:
    """Dropped items: gravity, bounce on the footpath, then fade."""

    def __init__(self, kind, pos, vel, life=3.5, spin=None, target=None, on_arrive=None):
        self.kind = kind
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.t = 0.0
        self.life = life
        self.angle = 0.0
        self.spin = random.uniform(-500, 500) if spin is None else spin
        self.wheel_spin = 0.0
        self.target = target  # fly in an arc to this point (hat -> nest)
        self.on_arrive = on_arrive
        self.start = tuple(pos)
        self.surf, self.anchor = art.draw_prop(kind)

    @property
    def alive(self):
        return self.t < self.life

    def update(self, dt):
        self.t += dt
        if self.target:
            k = min(1.0, self.t / 0.9)
            sx, sy = self.start
            tx, ty = self.target
            self.pos[0] = sx + (tx - sx) * k
            self.pos[1] = sy + (ty - sy) * k - math.sin(k * math.pi) * 120
            self.angle += self.spin * dt
            if k >= 1.0:
                if self.on_arrive:
                    self.on_arrive()
                self.life = 0
            return
        self.vel[1] += T.GRAVITY * 0.8 * dt
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.angle += self.spin * dt
        if self.pos[1] >= T.GROUND_Y + 6:
            self.pos[1] = T.GROUND_Y + 6
            if abs(self.vel[1]) > 80:
                self.vel[1] *= -0.4
                self.vel[0] *= 0.6
                self.spin *= 0.5
            else:
                self.vel[1] = 0
                self.vel[0] *= 1 - 6 * dt
                self.spin *= 1 - 6 * dt
        if self.kind == "wheel":
            self.wheel_spin += 12 * dt * max(0.0, 1 - self.t / self.life)
            self.surf, self.anchor = art.draw_prop("wheel", self.wheel_spin)

    def draw(self, dst, cam):
        fade = 0.6
        a = 255 if self.t < self.life - fade else int(255 * max(0.0, (self.life - self.t) / fade))
        art.blit_actor(dst, self.surf, self.anchor, (self.pos[0] - cam[0], self.pos[1] - cam[1]), 1, self.angle, a)


class Splat:
    """Broken egg on the footpath."""

    def __init__(self, pos, life=6.0):
        self.pos = pos
        self.t = 0.0
        self.life = life

    @property
    def alive(self):
        return self.t < self.life

    def update(self, dt):
        self.t += dt

    def draw(self, dst, cam):
        x, y = self.pos[0] - cam[0], self.pos[1] - cam[1]
        pygame.draw.ellipse(dst, P.BONE, (x - 12, y - 3, 24, 7))
        pygame.draw.circle(dst, P.YOLK, (round(x), round(y)), 4)
        for dx in (-9, 8):
            pygame.draw.polygon(dst, P.EGG, [(x + dx, y - 2), (x + dx + 5, y - 7), (x + dx + 6, y)])


class Shake:
    def __init__(self):
        self.mag = 0.0

    def add(self, amount):
        self.mag = max(self.mag, amount)

    def update(self, dt):
        self.mag = max(0.0, self.mag - dt * 30)

    def offset(self):
        if self.mag <= 0:
            return 0, 0
        return random.uniform(-self.mag, self.mag), random.uniform(-self.mag, self.mag)


class FX:
    def __init__(self):
        self.texts = []
        self.parts = []
        self.props = []
        self.splats = []
        self.shake = Shake()
        self.hitpause = 0

    MAX_BURSTS = 2

    def text(self, word, pos, style="hit", size=30, **kw):
        pos = [pos[0], pos[1]]
        if style != "plain":
            # keep big bursts readable: cap how many are up, and nudge apart
            bursts = [t for t in self.texts if t.style != "plain"]
            if len(bursts) >= self.MAX_BURSTS:
                self.texts.remove(bursts[0])
            for t in bursts[-self.MAX_BURSTS + 1:]:
                if abs(t.pos[0] - pos[0]) < 120 and abs(t.pos[1] - pos[1]) < 40:
                    pos[1] = t.pos[1] - 44
        self.texts.append(ComicText(word, pos, style, size, **kw))

    def burst(self, kind, pos, n=8, speed=180, life=1.2):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.3, 1.0) * speed
            self.parts.append(Particle(kind, pos, (math.cos(a) * v, math.sin(a) * v - 60), life))

    def prop(self, kind, pos, vel, **kw):
        self.props.append(Prop(kind, pos, vel, **kw))

    def splat(self, pos):
        self.splats.append(Splat(pos))

    def big_hit(self):
        self.shake.add(T.SHAKE_BIG)
        self.hitpause = max(self.hitpause, T.HITPAUSE_BIG)

    def update(self, dt):
        self.shake.update(dt)
        for group in (self.texts, self.parts, self.props, self.splats):
            for o in group:
                o.update(dt)
            group[:] = [o for o in group if o.alive]

    def draw_ground(self, dst, cam):
        for o in self.splats:
            o.draw(dst, cam)
        for o in self.props:
            o.draw(dst, cam)

    def draw_air(self, dst, cam):
        for o in self.parts:
            o.draw(dst, cam)
        for o in self.texts:
            o.draw(dst, cam)

    def clear(self):
        self.texts.clear()
        self.parts.clear()
