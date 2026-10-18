"""Parallax background, the gum tree, the nest and the territory ring."""

import math
import random

import pygame

from . import art
from . import palette as P
from . import tuning as T

W, H = T.SCREEN_W, T.SCREEN_H
GY = T.GROUND_Y
NX, NY = T.NEST_X, T.NEST_Y


def _lerp_col(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


class Level:
    FAR = 0.25
    MID = 0.55

    def __init__(self):
        rnd = random.Random(7)
        self.sky = self._sky()
        self.far = self._far(rnd)
        self.mid = self._mid(rnd)
        self.world = self._world(rnd)
        self.canopy = self._canopy(rnd)
        self.ring = self._ring()
        self.trophy_hats = 0

    # -- static layers ----------------------------------------------------

    def _sky(self):
        s = pygame.Surface((W, H))
        for y in range(H):
            k = min(1.0, y / (GY - 40))
            pygame.draw.line(s, _lerp_col(P.SKY_TOP, P.SKY_HORIZON, k ** 1.4), (0, y), (W, y))
        # hot, hazy sun
        sun = pygame.Surface((160, 160), pygame.SRCALPHA)
        for r, a in ((78, 30), (58, 60), (40, 255)):
            pygame.draw.circle(sun, (*P.BONE, a), (80, 80), r)
        s.blit(sun, (W - 210, 30))
        return s

    def _far(self, rnd):
        w = W + int((T.WORLD_W - W) * self.FAR) + 4
        s = pygame.Surface((w, H), pygame.SRCALPHA)
        pts = [(0, H)]
        x = 0
        while x < w + 40:
            pts.append((x, 330 + rnd.randint(-30, 20) + 25 * math.sin(x / 140)))
            x += rnd.randint(30, 70)
        pts.append((w, H))
        pygame.draw.polygon(s, P.RANGE_FAR, pts)
        pts = [(0, H)]
        x = 0
        while x < w + 40:
            pts.append((x, 380 + rnd.randint(-14, 10) + 18 * math.sin(x / 90 + 2)))
            x += rnd.randint(25, 60)
        pts.append((w, H))
        pygame.draw.polygon(s, P.RANGE_NEAR, pts)
        return s

    def _mid(self, rnd):
        w = W + int((T.WORLD_W - W) * self.MID) + 4
        s = pygame.Surface((w, H), pygame.SRCALPHA)
        base = 420
        # distant gums
        for _ in range(14):
            x = rnd.randint(0, w)
            h = rnd.randint(60, 120)
            pygame.draw.line(s, P.BARK_SHADE, (x, base), (x + rnd.randint(-6, 6), base - h), 5)
            for _ in range(5):
                pygame.draw.circle(s, P.EUCALYPT, (x + rnd.randint(-28, 28), base - h + rnd.randint(-18, 14)),
                                   rnd.randint(14, 24))
        # houses with red iron roofs
        for hx in (90, 470, 820):
            pygame.draw.rect(s, P.CONCRETE, (hx, base - 46, 120, 46))
            pygame.draw.rect(s, P.CONCRETE_SHADE, (hx, base - 46, 120, 46), 2)
            pygame.draw.polygon(s, P.RED_EARTH, [(hx - 12, base - 46), (hx + 60, base - 82), (hx + 132, base - 46)])
            for k in range(0, 140, 8):
                pygame.draw.line(s, P.WARATAH, (hx - 10 + k, base - 47), (hx + 60, base - 81), 1)
            pygame.draw.rect(s, P.SKY_TOP, (hx + 18, base - 34, 22, 16))
            pygame.draw.rect(s, P.FENCE_SHADE, (hx + 74, base - 36, 18, 36))
        # Hills Hoist
        hx, hy = 330, base
        pygame.draw.line(s, P.GREY, (hx, hy), (hx, hy - 70), 4)
        for k in range(4):
            a = k * math.pi / 2 + 0.4
            ex = hx + math.cos(a) * 46
            ey = hy - 70 + math.sin(a) * 9
            pygame.draw.line(s, P.GREY, (hx, hy - 74), (ex, ey), 2)
        for r in (16, 30, 44):
            pygame.draw.ellipse(s, P.GREY, (hx - r, hy - 70 - r * 0.2, r * 2, r * 0.4), 1)
        for k, col in enumerate((P.WARATAH, P.BONE, P.WATTLE)):
            pygame.draw.rect(s, col, (hx - 30 + k * 18, hy - 66, 10, 14))
        return s

    def _world(self, rnd):
        s = pygame.Surface((T.WORLD_W, H), pygame.SRCALPHA)
        # paling fence
        top = GY - 62
        pygame.draw.rect(s, P.FENCE_SHADE, (0, top + 10, T.WORLD_W, 6))
        pygame.draw.rect(s, P.FENCE_SHADE, (0, top + 42, T.WORLD_W, 6))
        x = 0
        while x < T.WORLD_W:
            ph = rnd.randint(-3, 3)
            pygame.draw.polygon(s, P.FENCE, [(x, GY), (x, top + ph + 4), (x + 6, top + ph), (x + 12, top + ph + 4),
                                             (x + 12, GY)])
            pygame.draw.line(s, P.FENCE_SHADE, (x + 12, top + ph + 4), (x + 12, GY), 2)
            x += 14
        # nature strip (red earth + tufts)
        pygame.draw.rect(s, P.RED_EARTH, (0, GY + 20, T.WORLD_W, H - GY - 20))
        for _ in range(140):
            gx = rnd.randint(0, T.WORLD_W)
            gy = rnd.randint(GY + 26, H - 4)
            for k in (-3, 0, 3):
                pygame.draw.line(s, P.OCHRE if k else P.EUCALYPT, (gx, gy), (gx + k, gy - 6), 2)
        # footpath
        pygame.draw.rect(s, P.CONCRETE, (0, GY, T.WORLD_W, 20))
        pygame.draw.line(s, P.CONCRETE_SHADE, (0, GY), (T.WORLD_W, GY), 2)
        for x in range(0, T.WORLD_W, 60):
            pygame.draw.line(s, P.CONCRETE_SHADE, (x, GY), (x - 6, GY + 20), 2)
        pygame.draw.line(s, P.OCHRE, (0, GY + 20), (T.WORLD_W, GY + 20), 3)
        # letterboxes
        for lx in (150, 1010, 1330):
            pygame.draw.rect(s, P.FENCE_SHADE, (lx + 8, GY - 40, 6, 40))
            art.opoly(s, P.WARATAH, [(lx, GY - 40), (lx + 22, GY - 40), (lx + 22, GY - 58), (lx + 11, GY - 64),
                                     (lx, GY - 58)])
            pygame.draw.rect(s, P.CHARCOAL, (lx + 5, GY - 52, 12, 3))
        # council signs
        for sx in (380, 1080):
            self._sign(s, sx)
        # the gum tree trunk + limbs
        self._trunk(s, rnd)
        return s

    def _sign(self, s, x):
        pygame.draw.rect(s, P.GREY, (x - 2, GY - 92, 5, 92))
        c = (x, GY - 112)
        pts = [(c[0], c[1] - 30), (c[0] + 30, c[1]), (c[0], c[1] + 30), (c[0] - 30, c[1])]
        art.opoly(s, P.WATTLE, pts, 3)
        # magpie silhouette swooping a stick figure
        pygame.draw.polygon(s, P.CHARCOAL, [(c[0] - 14, c[1] - 12), (c[0] + 4, c[1] - 8), (c[0] + 12, c[1] - 2),
                                            (c[0] + 2, c[1] - 4), (c[0] - 8, c[1] - 4)])
        pygame.draw.circle(s, P.CHARCOAL, (c[0] - 2, c[1] + 6), 3)
        pygame.draw.line(s, P.CHARCOAL, (c[0] - 2, c[1] + 8), (c[0] - 2, c[1] + 16), 2)
        pygame.draw.line(s, P.CHARCOAL, (c[0] - 7, c[1] + 10), (c[0] + 3, c[1] + 10), 2)
        plate = pygame.Rect(0, 0, 76, 26)
        plate.midtop = (x, GY - 78)
        pygame.draw.rect(s, P.WATTLE, plate)
        pygame.draw.rect(s, P.CHARCOAL, plate, 2)
        from .fx import font
        f = font(9, italic=False)
        for i, line in enumerate(("SWOOPING BIRD", "AHEAD")):
            t = f.render(line, True, P.CHARCOAL)
            s.blit(t, (x - t.get_width() / 2, plate.y + 3 + i * 11))

    def _trunk(self, s, rnd):
        # tapering ghost-gum trunk from the footpath to the nest fork
        pts = [(NX - 24, GY + 4), (NX - 15, T.TRUNK_TOP_Y + 20), (NX - 10, NY + 6), (NX + 10, NY + 6),
               (NX + 15, T.TRUNK_TOP_Y + 20), (NX + 24, GY + 4)]
        art.opoly(s, P.GHOST_GUM, pts, 3)
        for _ in range(16):
            y = rnd.randint(NY + 30, GY - 10)
            x = NX + rnd.randint(-10, 8)
            pygame.draw.line(s, P.BARK_SHADE, (x, y), (x + rnd.randint(-2, 2), y + rnd.randint(10, 26)), 2)
        # roots
        for d in (-1, 1):
            art.opoly(s, P.GHOST_GUM, [(NX + d * 18, GY - 10), (NX + d * 40, GY + 4), (NX + d * 14, GY + 4)], 2)
        # limbs up into the canopy
        for (x0, y0), (x1, y1), w in (((NX - 6, NY + 8), (NX - 100, 160), 10), ((NX + 6, NY + 8), (NX + 105, 155), 10),
                                      ((NX, NY), (NX - 15, 120), 9), ((NX - 55, 194), (NX - 135, 175), 6),
                                      ((NX + 60, 190), (NX + 140, 180), 6)):
            art.oline(s, P.GHOST_GUM, (x0, y0), (x1, y1), w)

    def _canopy(self, rnd):
        s = pygame.Surface((T.WORLD_W, H), pygame.SRCALPHA)
        blobs = []
        for _ in range(26):
            blobs.append((NX + rnd.randint(-210, 210), rnd.randint(80, 190), rnd.randint(26, 46)))
        for x, y, r in blobs:
            pygame.draw.circle(s, P.DEEP_GUM, (x, y + 6), r + 3)
        for x, y, r in blobs:
            pygame.draw.circle(s, P.EUCALYPT, (x, y), r)
        # leaf texture and wattle flecks, kept inside the foliage
        for _ in range(70):
            bx, by, br = rnd.choice(blobs)
            a = rnd.uniform(0, math.tau)
            rr = rnd.uniform(0, br - 8)
            pygame.draw.ellipse(s, P.DEEP_GUM, (bx + math.cos(a) * rr - 5, by + math.sin(a) * rr - 2, 10, 4))
        for _ in range(18):
            bx, by, br = rnd.choice(blobs)
            pygame.draw.circle(s, P.WATTLE, (bx + rnd.randint(-br // 2, br // 2), by + rnd.randint(-br // 2, br // 2)), 2)
        return s

    def _ring(self):
        s = pygame.Surface((T.WORLD_W, H), pygame.SRCALPHA)
        rx, ry = T.TERRITORY_RX, T.TERRITORY_RY
        n = 90
        for i in range(0, n, 2):
            a0 = i / n * math.tau
            a1 = (i + 1) / n * math.tau
            p0 = (NX + math.cos(a0) * rx, NY + math.sin(a0) * ry)
            p1 = (NX + math.cos(a1) * rx, NY + math.sin(a1) * ry)
            pygame.draw.line(s, (*P.BONE, 90), p0, p1, 3)
        return s

    # -- drawing ----------------------------------------------------------

    def draw_back(self, dst, cam):
        cx, cy = cam
        dst.blit(self.sky, (0, 0))
        dst.blit(self.far, (-cx * self.FAR, -cy * 0.2))
        dst.blit(self.mid, (-cx * self.MID, -cy * 0.5))
        dst.blit(self.world, (-cx, -cy))
        dst.blit(self.canopy, (-cx, -cy))

    def draw_ring(self, dst, cam, strength):
        if strength <= 0:
            return
        self.ring.set_alpha(int(255 * strength))
        dst.blit(self.ring, (-cam[0], -cam[1]))

    def draw_nest(self, dst, cam, eggs, t, threatened=False):
        x, y = NX - cam[0], NY - cam[1]
        # trophy hats hang off the back and sides of the nest
        for i in range(min(self.trophy_hats, 6)):
            hx = x + (-30 if i % 2 == 0 else 30) + (i // 2) * (6 if i % 2 else -6)
            art.draw_bucket_hat(dst, (hx, y + 2 - (i // 2) * 7))
        # eggs peek out above the rim
        for i in range(eggs):
            ex = x - 15 + i * 10
            art.oellipse(dst, P.EGG, (ex - 5, y - 13, 10, 12), 1)
            pygame.draw.circle(dst, P.EGG_SPOT, (ex - 1, y - 9), 1)
        art.oellipse(dst, P.NEST, (x - 30, y - 6, 60, 18), 2)
        for k in range(7):
            sx = x - 26 + k * 9
            pygame.draw.line(dst, P.NEST_SHADE, (sx, y - 2), (sx + 9, y + 8), 2)
            pygame.draw.line(dst, P.NEST_SHADE, (sx + 8, y - 3), (sx - 2, y + 9), 1)
        if threatened and int(t * 6) % 2 == 0:
            pygame.draw.ellipse(dst, P.WARATAH, (x - 36, y - 20, 72, 34), 3)
