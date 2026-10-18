"""Score, combo, eggs, territory meter, season calendar, edge arrows, banners."""

import math

import pygame

from . import art
from . import palette as P
from . import tuning as T
from .fx import font, outlined_text

W, H = T.SCREEN_W, T.SCREEN_H
MONTHS = ["AUG", "SEP", "OCT", "NOV"]


class TextCache:
    def __init__(self):
        self.cache = {}

    def get(self, text, size, fill=P.BONE, outline=P.CHARCOAL, thick=2, italic=True):
        key = (text, size, fill, outline, thick, italic)
        img = self.cache.get(key)
        if img is None:
            if len(self.cache) > 400:
                self.cache.clear()
            img = outlined_text(text, size, fill, outline, None, thick, italic)
            self.cache[key] = img
        return img


class HUD:
    def __init__(self):
        self.tc = TextCache()
        self.banners = []  # [text, sub, t]

    def banner(self, text, sub=False):
        self.banners.append([text, sub, 0.0])

    def update(self, dt):
        for b in self.banners:
            b[2] += dt
        self.banners = [b for b in self.banners if b[2] < 2.2]

    def draw(self, dst, g):
        tc = self.tc
        # score + combo
        dst.blit(tc.get(f"{g.score:,}", 30, P.WATTLE, P.CHARCOAL, 3), (10, 4))
        mult = g.combo_mult()
        if g.combo > 0:
            col = P.WATTLE if mult == 1 else P.WARATAH
            dst.blit(tc.get(f"COMBO {g.combo}  x{mult}", 16, P.BONE, col, 2), (14, 44))
        # territory meter
        m = g.magpie
        if m.territory < 1.0 or m.outside:
            x, y, w = 16, 70, 120
            lab = tc.get("TERRITORY", 12, P.BONE, P.CHARCOAL, 2, False)
            dst.blit(lab, (x - 4, y - 6))
            pygame.draw.rect(dst, P.CHARCOAL, (x, y + 14, w + 4, 10))
            col = P.EUCALYPT if m.territory > 0.35 else P.WARATAH
            pygame.draw.rect(dst, col, (x + 2, y + 16, w * m.territory, 6))
        # dad-o-meter: how close the street is to sending out an angry dad
        rage = g.spawner.dad_rage
        if rage > 0.05 or any(th.kind == "dad" for th in g.threats):
            x, y = 16, 100 if (m.territory < 1.0 or m.outside) else 70
            dst.blit(tc.get("DAD-O-METER", 12, P.BONE, P.CHARCOAL, 2, False), (x - 4, y - 6))
            n = T.DAD_RAGE_THRESHOLD
            for i in range(n):
                fill = min(1.0, max(0.0, rage - i))
                r = pygame.Rect(x + i * 22, y + 14, 18, 10)
                pygame.draw.rect(dst, P.CHARCOAL, r)
                if fill > 0:
                    pygame.draw.rect(dst, P.WARATAH, (r.x + 2, r.y + 2, (r.w - 4) * fill, r.h - 4))
        # eggs
        cx = W // 2
        for i in range(T.MAX_EGGS):
            ex = cx - (T.MAX_EGGS - 1) * 14 + i * 28
            rect = (ex - 9, 10, 18, 24)
            if i < g.eggs:
                art.oellipse(dst, P.EGG, rect, 2)
                pygame.draw.circle(dst, P.EGG_SPOT, (ex - 2, 18), 2)
                pygame.draw.circle(dst, P.EGG_SPOT, (ex + 3, 25), 1)
            else:
                pygame.draw.ellipse(dst, P.CHARCOAL, rect, 2)
        # season calendar
        sx, sy, sw = W - 250, 12, 230
        pygame.draw.rect(dst, P.CHARCOAL, (sx - 2, sy - 2, sw + 4, 22), border_radius=4)
        k = min(1.0, g.clock / T.SEASON_LENGTH)
        pygame.draw.rect(dst, P.OCHRE, (sx, sy, sw * k, 18), border_radius=3)
        for i, mname in enumerate(MONTHS):
            img = tc.get(mname, 11, P.BONE, P.CHARCOAL, 1, False)
            dst.blit(img, (sx + i * sw / 4 + sw / 8 - img.get_width() / 2, sy + 1))
            if i:
                pygame.draw.line(dst, P.CHARCOAL, (sx + i * sw / 4, sy), (sx + i * sw / 4, sy + 18), 1)
        secs = int(g.clock)
        clock = tc.get(f"{secs // 60}:{secs % 60:02d}", 16, P.BONE, P.CHARCOAL, 2)
        dst.blit(clock, (sx + sw - clock.get_width() + 6, sy + 22))
        wave = tc.get(f"WAVE {g.spawner.wave}", 16, P.BONE, P.CHARCOAL, 2)
        dst.blit(wave, (sx - 6, sy + 22))

        self.edge_arrows(dst, g)
        self.draw_banners(dst)

    def edge_arrows(self, dst, g):
        cx, cy = g.cam
        pad = 26
        for th in g.threats:
            if th.state in ("gone", "flee", "flee_win", "ko", "falling", "stroll") or th.innocent:
                continue
            x, y = th.center()
            sx, sy = x - cx, y - cy
            if 0 <= sx <= W and 0 <= sy <= H:
                continue
            ax = min(max(sx, pad), W - pad)
            ay = min(max(sy, pad + 40), H - pad)
            ang = math.atan2(sy - ay, sx - ax)
            col = P.THREAT_COLOURS.get(th.kind, P.WARATAH)
            self.arrow(dst, (ax, ay), ang, col, th.threatening)
        # the nest itself, if the magpie strays far enough to lose sight of it
        nx, ny = T.NEST_X - cx, T.NEST_Y - cy
        if not (0 <= nx <= W):
            ax = min(max(nx, pad), W - pad)
            self.arrow(dst, (ax, ny), 0 if nx > W else math.pi, P.EGG, False, label="NEST")

    def arrow(self, dst, pos, ang, col, urgent, label=None):
        x, y = pos
        r = 13 if not urgent else 16
        tip = (x + math.cos(ang) * r, y + math.sin(ang) * r)
        l = (x + math.cos(ang + 2.5) * r, y + math.sin(ang + 2.5) * r)
        rr = (x + math.cos(ang - 2.5) * r, y + math.sin(ang - 2.5) * r)
        pygame.draw.polygon(dst, col, [tip, l, rr])
        pygame.draw.polygon(dst, P.WARATAH if urgent else P.BONE, [tip, l, rr], 3)
        if label:
            img = self.tc.get(label, 11, P.BONE, P.CHARCOAL, 1, False)
            dst.blit(img, (x - img.get_width() / 2, y + 14))

    def draw_banners(self, dst):
        y = 150
        for text, sub, t in self.banners:
            k = t / 2.2
            size = 26 if sub else 46
            img = self.tc.get(text, size, P.WATTLE if not sub else P.BONE, P.WARATAH if not sub else P.CHARCOAL, 3)
            scale = 1.0 + max(0.0, 0.3 - t) * 1.5
            if scale != 1.0:
                img = pygame.transform.rotozoom(img, 0, scale)
            if k > 0.75:
                img = img.copy()
                img.set_alpha(int(255 * (1 - (k - 0.75) / 0.25)))
            dst.blit(img, (W / 2 - img.get_width() / 2, y))
            y += img.get_height() + 4

    def draw_debug(self, dst, g):
        s = g.spawner
        counts = {}
        for th in g.threats:
            counts[th.kind] = counts.get(th.kind, 0) + 1
        lines = [
            f"d={s.d:.3f}  phase={T.PHASES[s.phase][1]}  t={g.clock:.1f}",
            f"active={s.active()}/{s.max_active()}  interval={s.interval():.2f}s  dirs={','.join(s.dirs)}",
            f"returns queued={len(s.returns)}  dad rage={s.dad_rage:.2f}  fps={g.fps:.0f}",
            "alive: " + "  ".join(f"{k}:{v}" for k, v in sorted(counts.items())),
            "spawned: " + "  ".join(f"{k}:{v}" for k, v in s.spawned.items() if v),
        ]
        f = font(13, bold=False, italic=False)
        y = H - 18 * len(lines) - 6
        bg = pygame.Surface((W, 18 * len(lines) + 8), pygame.SRCALPHA)
        bg.fill((*P.CHARCOAL, 180))
        dst.blit(bg, (0, y - 4))
        for line in lines:
            dst.blit(f.render(line, True, P.BONE), (8, y))
            y += 18
