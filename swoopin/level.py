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


class Layer:
    """A pre-drawn layer, cropped to what is actually drawn on it, in the
    display's pixel format and RLE-encoded so blits skip transparent runs and
    copy opaque ones. Blending whole transparent screens every frame was
    most of the frame time in the browser."""

    def __init__(self, surf, alpha=True):
        rect = surf.get_bounding_rect() if alpha else surf.get_rect()
        img = surf.subsurface(rect).copy()
        if pygame.display.get_surface() is not None:
            img = img.convert_alpha() if alpha else img.convert()
        if alpha:
            img.set_alpha(255, pygame.RLEACCEL)
        self.img, self.off = img, rect.topleft

    def blit(self, dst, x, y):
        dst.blit(self.img, (x + self.off[0], y + self.off[1]))


class Level:
    FAR = 0.25
    MID = 0.55

    def __init__(self):
        rnd = random.Random(7)
        self.sky = Layer(self._sky(), alpha=False)
        self.far = Layer(self._far(rnd))
        self.mid = Layer(self._mid(rnd))
        # the canopy scrolls with the world and is drawn straight after it
        world = self._world(rnd)
        world.blit(self._canopy(rnd), (0, 0))
        self.world = Layer(world)
        self.ring_src = self._ring()
        self.rings = {}  # faded copies of the ring, by strength step
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
        """Australian 'swooping birds' warning sign: yellow diamond with an inset
        black border, a magpie diving with wings raised at a person shielding
        their head, and a plate sized to its text. Drawn at 4x and smoothed down."""
        k = 4
        lines = ("SWOOPING", "BIRDS AHEAD")
        from .fx import font
        f = font(9 * k, italic=False)
        text = [f.render(line, True, P.CHARCOAL) for line in lines]
        R = 30  # diamond half-diagonal
        plate_w = max(t.get_width() for t in text) // k + 10
        plate_h = len(lines) * 10 + 6
        w = max(2 * R + 4, plate_w + 4)
        post = 64
        h = 2 * R + 4 + plate_h + post
        big = pygame.Surface((w * k, h * k), pygame.SRCALPHA)
        cx, cy = w * k / 2, (R + 2) * k

        def pt(px, py):
            return cx + px * k, cy + py * k

        # post
        pygame.draw.rect(big, P.GREY, (cx - 2 * k, cy, 5 * k, h * k - cy))
        pygame.draw.line(big, P.DARK_GREY, (cx + 2 * k, cy), (cx + 2 * k, h * k), k)
        # diamond with inset border
        outer = [pt(0, -R), pt(R, 0), pt(0, R), pt(-R, 0)]
        pygame.draw.polygon(big, P.CHARCOAL, outer)
        pygame.draw.polygon(big, P.WATTLE, [pt(0, -R + 2), pt(R - 2, 0), pt(0, R - 2), pt(-R + 2, 0)])
        pygame.draw.polygon(big, P.CHARCOAL, [pt(0, -R + 4.5), pt(R - 4.5, 0), pt(0, R - 4.5), pt(-R + 4.5, 0)],
                            int(1.2 * k))

        # magpie: the game's own sprite as a silhouette, wings up, diving down-left
        sprite, _ = art.draw_magpie(0.0)
        sil = pygame.mask.from_surface(sprite).to_surface(setcolor=(*P.CHARCOAL, 255), unsetcolor=(0, 0, 0, 0))
        sil = pygame.transform.flip(sil, True, False)
        sil = pygame.transform.rotozoom(sil, 22, k * 0.36)
        bx, by = pt(5, -6)
        layer = pygame.Surface(big.get_size(), pygame.SRCALPHA)
        layer.blit(sil, (bx - sil.get_width() / 2, by - sil.get_height() / 2))
        # keep the symbol inside the inner border
        clip = pygame.Surface(big.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(clip, (255, 255, 255, 255), [pt(0, -R + 6), pt(R - 6, 0), pt(0, R - 6), pt(-R + 6, 0)])
        layer.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        big.blit(layer, (0, 0))

        # person underneath, one arm flung up
        lw = int(1.8 * k)
        pygame.draw.circle(big, P.CHARCOAL, pt(-3, 6), 2.6 * k)
        pygame.draw.line(big, P.CHARCOAL, pt(-3, 9), pt(-3, 15.5), lw)
        pygame.draw.line(big, P.CHARCOAL, pt(-3, 15.5), pt(-6, 20.5), lw)
        pygame.draw.line(big, P.CHARCOAL, pt(-3, 15.5), pt(0, 20.5), lw)
        pygame.draw.lines(big, P.CHARCOAL, False, [pt(-3, 10), pt(0.5, 7), pt(2, 2.5)], lw)
        pygame.draw.line(big, P.CHARCOAL, pt(-3, 10), pt(-6.5, 14), lw)

        # text plate, sized to the words
        py0 = (2 * R + 4) * k
        plate = pygame.Rect(0, 0, plate_w * k, plate_h * k)
        plate.midtop = (cx, py0)
        pygame.draw.rect(big, P.CHARCOAL, plate, border_radius=k * 2)
        pygame.draw.rect(big, P.WATTLE, plate.inflate(-3 * k, -3 * k), border_radius=k)
        for i, t in enumerate(text):
            big.blit(t, (cx - t.get_width() / 2, py0 + (3.5 + i * 10) * k - k))

        small = pygame.transform.smoothscale(big, (w, h))
        s.blit(small, (x - w / 2, GY - h))

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
        # limbs fork out from the nest and every branch ends in foliage
        self.branch_tips = []
        fork = (NX, NY + 6)
        mains = [((NX - 160, 132), 12, 5, 34), ((NX + 12, 88), 11, 4, -14), ((NX + 166, 128), 12, 5, -36)]
        subs = []
        for end, w0, w1, bend in mains:
            pts = self._limb(s, fork, end, w0, w1, bend)
            self.branch_tips.append(end)
            # two side branches peel off each main limb
            for frac, out, up in ((0.5, 1, -1), (0.7, -1, -1)):
                start = pts[int(frac * (len(pts) - 1))]
                dx = end[0] - fork[0]
                side = 1 if dx >= 0 else -1
                tip = (start[0] + side * out * rnd.randint(35, 60) + (rnd.randint(-15, 15) if dx == 0 else 0),
                       start[1] + up * rnd.randint(40, 62))
                subs.append((start, tip))
        for start, tip in subs:
            self._limb(s, start, tip, 5, 2, rnd.randint(-12, 12))
            self.branch_tips.append(tip)

    def _limb(self, s, a, b, w0, w1, bend):
        """A tapering, gently curved ghost-gum limb. Returns its centre line."""
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        cx, cy = mx - dy / d * bend, my + dx / d * bend  # bezier control point
        line, left, right = [], [], []
        n = 14
        for i in range(n + 1):
            t = i / n
            x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * cx + t * t * b[0]
            y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * cy + t * t * b[1]
            tx = 2 * (1 - t) * (cx - a[0]) + 2 * t * (b[0] - cx)
            ty = 2 * (1 - t) * (cy - a[1]) + 2 * t * (b[1] - cy)
            tl = math.hypot(tx, ty) or 1
            w = (w0 + (w1 - w0) * t) / 2
            line.append((x, y))
            left.append((x - ty / tl * w, y + tx / tl * w))
            right.append((x + ty / tl * w, y - tx / tl * w))
        art.opoly(s, P.GHOST_GUM, left + right[::-1], 2)
        # a few grey bark patches
        for i in range(2, n - 2, 4):
            x, y = line[i]
            pygame.draw.ellipse(s, P.BARK_SHADE, (x - 2, y - 1, 5, 3))
        return line

    def _canopy(self, rnd):
        """Open, clumpy eucalypt foliage: a cluster of leaves around every branch
        tip, so no limb ends in mid-air and sky shows between the clumps."""
        s = pygame.Surface((T.WORLD_W, H), pygame.SRCALPHA)
        blobs = []
        for tx, ty in self.branch_tips:
            for _ in range(rnd.randint(5, 7)):
                r = rnd.randint(19, 32)
                blobs.append((tx + rnd.randint(-34, 34), ty + rnd.randint(-30, 8), r))
            # crown on top of each clump, so the canopy has some height
            blobs.append((tx + rnd.randint(-12, 12), ty - rnd.randint(32, 46), rnd.randint(20, 28)))
        # a few filler clumps between neighbouring tips keep it full but not solid
        tips = sorted(self.branch_tips)
        for (ax, ay), (bx, by) in zip(tips, tips[1:]):
            if math.hypot(bx - ax, by - ay) < 150:
                blobs.append(((ax + bx) / 2 + rnd.randint(-10, 10), (ay + by) / 2 - rnd.randint(5, 20),
                              rnd.randint(18, 26)))
        for x, y, r in blobs:  # shaded underside
            pygame.draw.circle(s, P.DEEP_GUM, (x, y + 5), r + 2)
        for x, y, r in blobs:
            pygame.draw.circle(s, P.EUCALYPT, (x, y), r)
        # drooping gum leaves and a little cream blossom, kept inside the clumps
        for _ in range(110):
            bx, by, br = rnd.choice(blobs)
            a = rnd.uniform(0, math.tau)
            rr = rnd.uniform(0, br - 6)
            lx, ly = bx + math.cos(a) * rr, by + math.sin(a) * rr
            pygame.draw.line(s, P.DEEP_GUM, (lx - 3, ly - 2), (lx + 3, ly + 3), 2)
        for _ in range(14):
            bx, by, br = rnd.choice(blobs)
            pygame.draw.circle(s, P.BONE, (bx + rnd.randint(-br // 2, br // 2), by + rnd.randint(-br // 2, br // 2)), 2)
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
        self.sky.blit(dst, 0, 0)
        self.far.blit(dst, -cx * self.FAR, -cy * 0.2)
        self.mid.blit(dst, -cx * self.MID, -cy * 0.5)
        self.world.blit(dst, -cx, -cy)

    def draw_ring(self, dst, cam, strength):
        if strength <= 0:
            return
        step = max(1, min(10, round(strength * 10)))
        ring = self.rings.get(step)
        if ring is None:
            img = self.ring_src.copy()
            img.fill((255, 255, 255, round(255 * step / 10)), special_flags=pygame.BLEND_RGBA_MULT)
            ring = self.rings[step] = Layer(img)
        ring.blit(dst, -cam[0], -cam[1])

    def _nest_bowl(self, dst, x, y):
        art.oellipse(dst, P.NEST, (x - 30, y - 6, 60, 18), 2)
        for k in range(7):
            sx = x - 26 + k * 9
            pygame.draw.line(dst, P.NEST_SHADE, (sx, y - 2), (sx + 9, y + 8), 2)
            pygame.draw.line(dst, P.NEST_SHADE, (sx + 8, y - 3), (sx - 2, y + 9), 1)

    def draw_nest_front(self, dst, cam):
        """Redraw the front of the bowl over a magpie standing in the nest."""
        x, y = T.NEST_X - cam[0], T.NEST_Y - cam[1]
        old = dst.get_clip()
        dst.set_clip(pygame.Rect(x - 32, y - 1, 64, 16).clip(old))
        self._nest_bowl(dst, x, y)
        dst.set_clip(old)

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
        self._nest_bowl(dst, x, y)
        if threatened and int(t * 6) % 2 == 0:
            pygame.draw.ellipse(dst, P.WARATAH, (x - 36, y - 20, 72, 34), 3)
