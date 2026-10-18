"""On-screen touch controls for phones and tablets.

Hidden until the first finger touches the screen, so keyboard players never
see them. Multi-touch: hold a steer button with the left thumb while the
right thumb flaps, swoops and claws. Tapping any empty spot on the right
half of the screen also flaps.
"""

import math

import pygame

from . import palette as P
from . import tuning as T

W, H = T.SCREEN_W, T.SCREEN_H

# name -> (centre, radius, label). Held buttons steer; the rest fire on touch.
BUTTONS = {
    "left": ((72, 462), 50, "<"),
    "right": ((192, 462), 50, ">"),
    "mate": ((300, 492), 30, "MATE"),
    "flap": ((878, 450), 64, "FLAP"),
    "swoop": ((752, 484), 44, "SWOOP"),
    "claw": ((770, 368), 40, "CLAW"),
    "poop": ((884, 318), 32, "POOP"),
    "pause": ((930, 104), 24, "II"),
}
HELD = ("left", "right")
TITLE_BUTTON = (pygame.Rect(W / 2 - 90, 330, 180, 50), "TITLE")


def portrait():
    """True when a phone is held upright (browser only)."""
    try:
        import platform
        win = platform.window
        return win.innerHeight > win.innerWidth * 1.1
    except Exception:
        return False


class TouchPad:
    def __init__(self):
        self.active = False  # a finger has been seen
        self.fingers = {}  # finger id -> button under it (or None)
        self.last_touch = -99.0
        self.flash = {}  # button -> time it was last pressed, for the glow

    # -- input -----------------------------------------------------------

    @staticmethod
    def to_screen(ev):
        """Finger position (0..1 of the window) -> 960x540 game pixels,
        allowing for SCALED letterboxing on desktop touchscreens."""
        ww, wh = pygame.display.get_window_size()
        s = min(ww / W, wh / H) or 1
        ox, oy = (ww - W * s) / 2, (wh - H * s) / 2
        return (ev.x * ww - ox) / s, (ev.y * wh - oy) / s

    @staticmethod
    def hit(pos):
        for name, (c, r, _) in BUTTONS.items():
            if math.dist(pos, c) <= r + 10:  # a little slack for thumbs
                return name
        return None

    def from_mouse(self, ev, now):
        """Mouse events SDL makes up from touches would double every tap."""
        return getattr(ev, "touch", False) or now - self.last_touch < 0.6

    def handle(self, ev, game, ctl, now):
        """Feed a FINGER* event. Returns False to quit (never, in practice)."""
        self.active = True
        self.last_touch = now
        pos = self.to_screen(ev)
        if ev.type == pygame.FINGERUP:
            self.fingers.pop(ev.finger_id, None)
            return True
        if ev.type == pygame.FINGERMOTION:
            # slide between the steer buttons without lifting
            if self.fingers.get(ev.finger_id) in HELD:
                b = self.hit(pos)
                self.fingers[ev.finger_id] = b if b in HELD else None
            return True
        # FINGERDOWN
        if game.scene == "title":
            return game.handle_key(pygame.K_SPACE)
        if game.scene in ("over", "victory"):
            if game.end_screen_t > 1.5:  # don't skip the stats by accident
                return game.handle_key(pygame.K_SPACE)
            return True
        if game.paused:
            if TITLE_BUTTON[0].inflate(20, 20).collidepoint(pos):
                return game.handle_key(pygame.K_q)
            return game.handle_key(pygame.K_p)
        b = self.hit(pos)
        if b is None and pos[0] > W / 2:
            b = "flap"
        self.fingers[ev.finger_id] = b
        if b:
            self.flash[b] = now
        if b in ("flap", "swoop", "claw", "poop"):
            setattr(ctl, b, True)
        elif b == "mate":
            return game.handle_key(pygame.K_q)
        elif b == "pause":
            return game.handle_key(pygame.K_p)
        return True

    def steer(self, ctl):
        held = set(self.fingers.values())
        ctl.left = ctl.left or "left" in held
        ctl.right = ctl.right or "right" in held

    # -- drawing ---------------------------------------------------------

    def draw(self, dst, game, tc, now):
        if not self.active or game.scene != "play":
            return
        if game.paused:
            rect, label = TITLE_BUTTON
            pygame.draw.rect(dst, P.CHARCOAL, rect, border_radius=10)
            pygame.draw.rect(dst, P.BONE, rect, 3, border_radius=10)
            img = tc.get(label, 22, P.BONE, P.CHARCOAL, 2)
            dst.blit(img, img.get_rect(center=rect.center))
            return
        held = set(self.fingers.values())
        for name, (c, r, label) in BUTTONS.items():
            if name == "mate" and game.mate_calls <= 0:
                continue
            lit = name in held or now - self.flash.get(name, -9) < 0.12
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            o = (r + 2, r + 2)
            pygame.draw.circle(s, (*(P.WATTLE if lit else P.CHARCOAL), 120 if lit else 80), o, r)
            pygame.draw.circle(s, (*P.BONE, 200 if lit else 120), o, r, 3)
            dst.blit(s, (c[0] - r - 2, c[1] - r - 2))
            size = 34 if len(label) == 1 else (22 if name == "flap" else 14)
            img = tc.get(label, size, P.BONE, P.CHARCOAL, 2, False)
            img.set_alpha(220)
            dst.blit(img, img.get_rect(center=c))


def draw_rotate_hint(dst, tc):
    shade = pygame.Surface((W, H), pygame.SRCALPHA)
    shade.fill((*P.CHARCOAL, 210))
    dst.blit(shade, (0, 0))
    for i, (text, size) in enumerate((("TURN YOUR PHONE SIDEWAYS", 44), ("Swoopin plays in landscape", 24))):
        img = tc.get(text, size, P.WATTLE if i == 0 else P.BONE, P.CHARCOAL, 3)
        dst.blit(img, (W / 2 - img.get_width() / 2, 200 + i * 70))
