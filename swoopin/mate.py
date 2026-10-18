"""The partner magpie. Press Q and your mate flies in for a while to swoop
anything going for the nest. She leaves the innocent kids and mums alone."""

import math

import pygame

from . import art, hits
from . import palette as P
from . import tuning as T
from .magpie import BEAK_TIP, REST_Y

# states a threat can be in and still be worth going after
HUNTABLE = ("approach", "attack", "climb", "wait", "aim", "cool")


def huntable(th):
    """Raiders on their way in, plus anything running off with an egg."""
    if th.innocent or not th.hittable:
        return False
    return th.state in HUNTABLE or getattr(th, "carrying", False)


class Mate:
    def __init__(self, game):
        self.game = game
        # fly in high from the side of the screen the player isn't on
        side = -1 if game.magpie.pos[0] > T.NEST_X else 1
        self.pos = [T.NEST_X + side * (T.SCREEN_W / 2 + 40), -40.0]
        self.vel = [-side * T.MATE_SPEED, 120.0]
        self.facing = -side
        self.state = "hunt"  # hunt | dive | leave
        self.t = 0.0
        self.time_left = T.MATE_TIME
        self.target = None
        self.dive_t = 0.0
        self.hit_cd = 0.0
        self.flap = 0.0
        self.alive = True

    # -- geometry ---------------------------------------------------------

    @property
    def angle(self):
        vx, vy = self.vel
        base = -math.degrees(math.atan2(vy, abs(vx) + 140)) * 0.7
        return max(-55.0, min(35.0, base)) * self.facing

    def tip(self):
        ox, oy = art.xform(BEAK_TIP, self.facing, self.angle)
        return self.pos[0] + ox, self.pos[1] + oy

    # -- AI ---------------------------------------------------------------

    def pick_target(self):
        """The raider closest to the nest, with anyone at it or carrying an egg first."""
        best, best_score = None, None
        for th in self.game.threats:
            if not huntable(th):
                continue
            x, y = th.center()
            if not (0 <= x <= T.WORLD_W and -20 <= y <= T.GROUND_Y):
                continue
            urgent = th.threatening or getattr(th, "carrying", False)
            score = math.hypot(x - T.NEST_X, y - T.NEST_Y) - (400 if urgent else 0)
            if best_score is None or score < best_score:
                best, best_score = th, score
        return best

    @staticmethod
    def aim_point(th):
        """Go for the head if there is one, otherwise the middle."""
        for name, c, r in th.zones():
            if name in ("head", "helmet"):
                return c
        return th.center()

    def steer(self, goal, speed, dt):
        dx, dy = goal[0] - self.pos[0], goal[1] - self.pos[1]
        d = math.hypot(dx, dy) or 1
        want = (dx / d * speed, dy / d * speed)
        k = min(1.0, T.MATE_STEER * dt)
        self.vel[0] += (want[0] - self.vel[0]) * k
        self.vel[1] += (want[1] - self.vel[1]) * k
        return d

    def update(self, dt):
        g = self.game
        self.t += dt
        self.flap += dt * (12 if self.state == "dive" else 22)
        self.hit_cd = max(0.0, self.hit_cd - dt)
        self.time_left -= dt
        if self.time_left <= 0 and self.state != "leave":
            self.state = "leave"
            self.target = None
            hx, hy = self.pos
            g.fx.text("HOORAY, LOVE!", (hx, hy - 30), "plain", 18, drift=-40)

        if self.state == "leave":
            # off up into the gum canopy and away
            self.steer((self.pos[0] + self.facing * 200, -200), T.MATE_SPEED, dt)
            if self.pos[1] < -80:
                self.alive = False
        else:
            if self.target is None or not huntable(self.target):
                self.target = self.pick_target()
                self.state = "hunt"
            th = self.target
            if th is None:
                # nothing to hit: circle the nest
                a = self.t * 1.6
                goal = (T.NEST_X + math.cos(a) * T.MATE_ORBIT_RX, T.NEST_Y - 40 + math.sin(a) * T.MATE_ORBIT_RY)
                self.steer(goal, T.MATE_SPEED * 0.8, dt)
            else:
                goal = self.aim_point(th)
                if self.state == "dive":
                    self.dive_t -= dt
                    # steer so her beak (not her body) lands on the target
                    tx, ty = self.tip()
                    self.steer((goal[0] - (tx - self.pos[0]), goal[1] - (ty - self.pos[1])),
                               T.MATE_DIVE_SPEED, dt * 2.5)
                    if self.dive_t <= 0:
                        self.state = "hunt"
                else:
                    # line up a little above, then drop on them
                    d = self.steer((goal[0], goal[1] - 40), T.MATE_SPEED, dt)
                    if d < T.MATE_DIVE_RANGE and self.hit_cd <= 0:
                        self.state = "dive"
                        self.dive_t = 0.5
                if self.state == "dive" and self.hit_cd <= 0:
                    zones = th.zones()
                    # beak contact, or her body right on top of them
                    zone = hits.classify(zones, self.tip(), 9) or hits.classify(zones, self.pos, 12)
                    if zone:
                        hits.apply_hit(g, th, "swoop", zone, self.tip(), mate=True)
                        self.hit_cd = T.MATE_HIT_COOLDOWN
                        self.state = "hunt"
                        self.vel[1] = T.SWOOP_BOUNCE  # pop back up like the player does
                        self.vel[0] *= 0.45
                        self.target = None

        if abs(self.vel[0]) > 20:
            self.facing = 1 if self.vel[0] > 0 else -1
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.pos[0] = max(14.0, min(T.WORLD_W - 14.0, self.pos[0]))
        if self.pos[1] > REST_Y - 10:
            self.pos[1] = REST_Y - 10
            self.vel[1] = min(self.vel[1], 0.0)

    # -- drawing ----------------------------------------------------------

    def draw(self, dst, cam):
        cx, cy = cam
        surf, anchor = art.draw_magpie(self.flap, tucked=self.state == "dive", female=True)
        # flicker as she's about to head off
        fading = self.state != "leave" and self.time_left < 2.0 and int(self.t * 8) % 2 == 0
        art.blit_actor(dst, surf, anchor, (self.pos[0] - cx, self.pos[1] - cy), self.facing, self.angle,
                       150 if fading else 255)
        if self.state == "dive":
            for k in (0.5, 1.0):
                x, y = self.pos[0] - cx, self.pos[1] - cy
                pygame.draw.line(dst, P.BONE, (x - self.facing * 30 * k, y - 4),
                                 (x - self.facing * 56 * k, y - 4), 2)
