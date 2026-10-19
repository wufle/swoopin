"""The player: Flappy-style flight, swoop dive, claw slash, territory leash."""

import math
from dataclasses import dataclass

import pygame

from . import art
from . import palette as P
from . import tuning as T

BEAK_TIP = (36, -4)  # local offset of the beak tip from the sprite anchor
REST_Y = T.GROUND_Y - 24  # anchor height when standing: feet on the footpath
PERCH_Y = T.NEST_Y - 26  # anchor height when standing in the nest


@dataclass
class Controls:
    flap: bool = False
    swoop: bool = False
    claw: bool = False
    left: bool = False
    right: bool = False
    poop: bool = False


class Magpie:
    def __init__(self):
        self.pos = [T.NEST_X - 60.0, T.NEST_Y - 40.0]
        self.vel = [0.0, 0.0]
        self.facing = 1
        self.state = "fly"  # fly | swoop | stun
        self.grounded = False
        self.swoop_t = 0.0
        self.swoop_cd = 0.0
        self.swoop_id = 0
        self.swoop_hits = set()
        self.claw_t = 0.0
        self.claw_cd = 0.0
        self.claw_hits = set()
        self.peck_cd = 0.0
        self.poop_cd = 0.0
        self.stun_t = 0.0
        self.invuln = 0.0
        self.flap_phase = 0.0
        self.flap_anim = 0.0
        self.territory = 1.0
        self.outside = False
        self.pulled = False
        self.trail = []
        self.walk = 0.0
        self.walking = False
        self.perched = False
        self.t = 0.0

    # -- geometry ---------------------------------------------------------

    @property
    def angle(self):
        vx, vy = self.vel
        if self.grounded:
            return 0.0
        base = -math.degrees(math.atan2(vy, abs(vx) + 140)) * 0.7
        return max(-55.0, min(35.0, base)) * self.facing

    def tip(self):
        ox, oy = art.xform(BEAK_TIP, self.facing, self.angle)
        return self.pos[0] + ox, self.pos[1] + oy

    def vent(self):
        """Where a poop leaves the bird: just under the tail."""
        ox, oy = art.xform((-24, 6), self.facing, self.angle)
        return self.pos[0] + ox, self.pos[1] + oy

    def claw_center(self):
        if self.perched:  # reach down over the rim of the nest
            return self.pos[0] + self.facing * (T.CLAW_REACH + 2), self.pos[1] + 14
        if self.grounded:  # on foot: slash at shin height
            return self.pos[0] + self.facing * (T.CLAW_REACH + 4), self.pos[1] - 2
        return self.pos[0] + self.facing * T.CLAW_REACH, self.pos[1] + 8

    # -- control ----------------------------------------------------------

    def bounce(self):
        """A swoop connected: pop back up so hits can be chained."""
        self.state = "fly"
        self.swoop_cd = T.SWOOP_COOLDOWN * 0.5
        self.vel[1] = T.SWOOP_BOUNCE
        self.vel[0] *= 0.45
        self.flap_anim = 0.25

    def hurt(self, from_x, stun=None):
        if self.invuln > 0 or self.state == "stun":
            return False
        self.state = "stun"
        self.stun_t = stun or T.HIT_STUN_TIME
        self.invuln = T.INVULN_TIME
        self.vel[0] = 160 if self.pos[0] > from_x else -160
        self.vel[1] = -120
        return True

    def update(self, dt, ctl):
        """Advance one step. Returns a list of event names."""
        events = []
        self.t += dt
        for name in ("swoop_cd", "claw_cd", "peck_cd", "poop_cd", "invuln", "flap_anim"):
            setattr(self, name, max(0.0, getattr(self, name) - dt))
        self.claw_t = max(0.0, self.claw_t - dt)

        if self.state == "stun":
            self.stun_t -= dt
            if self.stun_t <= 0:
                self.state = "fly"
        else:
            self.walking = False
            if self.grounded:
                # on the ground the magpie strolls about on two legs
                if ctl.left and not ctl.right:
                    self.facing = -1
                    self.vel[0] = -T.WALK_SPEED
                    self.walking = True
                elif ctl.right and not ctl.left:
                    self.facing = 1
                    self.vel[0] = T.WALK_SPEED
                    self.walking = True
                else:
                    self.vel[0] = 0.0
                if self.walking:
                    self.walk += dt * T.WALK_SPEED / art.MAGPIE_STEP_PX * math.tau
            elif ctl.left and not ctl.right:
                self.facing = -1
                self.vel[0] -= T.H_ACCEL * dt
            elif ctl.right and not ctl.left:
                self.facing = 1
                self.vel[0] += T.H_ACCEL * dt
            if ctl.flap:
                if self.state == "swoop":
                    self.state = "fly"
                    self.swoop_cd = T.SWOOP_COOLDOWN
                self.vel[1] = T.FLAP_IMPULSE
                self.vel[0] += self.facing * T.FLAP_FORWARD
                self.flap_anim = 0.22
                self.grounded = False
                events.append("flap")
            if ctl.swoop and self.state == "fly" and self.swoop_cd <= 0 and not self.grounded:
                self.state = "swoop"
                self.swoop_t = T.SWOOP_TIME
                self.swoop_id += 1
                self.swoop_hits = set()
                self.vel = [self.facing * T.SWOOP_VX, T.SWOOP_VY]
                events.append("swoop")
            if ctl.poop and self.poop_cd <= 0 and not self.grounded:
                self.poop_cd = T.POOP_COOLDOWN
                events.append("poop")
            if ctl.claw and self.claw_cd <= 0:
                self.claw_t = T.CLAW_ACTIVE
                self.claw_cd = T.CLAW_COOLDOWN
                self.claw_hits = set()
                events.append("claw")

        # physics
        cap = T.H_MAX
        if self.state == "swoop":
            self.vel[1] += T.GRAVITY * 0.35 * dt
            self.swoop_t -= dt
            if self.swoop_t <= 0:
                self.state = "fly"
                self.swoop_cd = T.SWOOP_COOLDOWN
            cap = T.SWOOP_VX * 1.1
        else:
            self.vel[1] = min(T.MAX_FALL, self.vel[1] + T.GRAVITY * dt)
            if (not (ctl.left or ctl.right) or self.state == "stun") and not self.grounded:
                self.vel[0] *= max(0.0, 1 - T.H_DRAG * dt)
            elif self.grounded and self.state == "stun":
                self.vel[0] *= max(0.0, 1 - 8 * dt)

        # territory leash
        dx = self.pos[0] - T.NEST_X
        dy = self.pos[1] - T.NEST_Y
        e = (dx / T.TERRITORY_RX) ** 2 + (dy / T.TERRITORY_RY) ** 2
        self.outside = e > 1.0
        if self.outside:
            self.territory = max(0.0, self.territory - T.TERRITORY_DRAIN * dt)
            cap *= T.TERRITORY_SLOW
            self.vel[0] -= math.copysign(T.TERRITORY_HEADWIND, dx) * dt
            if self.territory <= 0 and not self.pulled:
                self.pulled = True
                events.append("pulled")
        else:
            self.territory = min(1.0, self.territory + T.TERRITORY_REFILL * dt)
        if self.pulled:
            d = math.hypot(dx, dy) or 1
            self.vel[0] -= dx / d * T.TERRITORY_PULL * dt
            self.vel[1] -= dy / d * T.TERRITORY_PULL * 0.5 * dt
            cap = max(cap, 380)
            if e < 0.55:
                self.pulled = False
        self.vel[0] = max(-cap, min(cap, self.vel[0]))

        prev_y = self.pos[1]
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt

        # the nest: drop gently onto it to stand guard; walk off the rim or flap to leave.
        # A swoop passes straight through so dives at raiders on the nest still connect.
        on_nest = abs(self.pos[0] - T.NEST_X) <= T.PERCH_HALF_WIDTH
        if self.perched:
            if self.vel[1] < 0 or not on_nest:
                self.perched = False
                self.grounded = False
            else:
                self.pos[1] = PERCH_Y
                self.vel[1] = 0
        elif (on_nest and self.state == "fly" and self.vel[1] >= 0
              and prev_y <= PERCH_Y + 2 <= self.pos[1] + 2):
            self.perched = True
            self.grounded = True
            self.pos[1] = PERCH_Y
            self.vel = [0.0, 0.0]
            events += ["landed", "perched"]

        # bounds
        if self.pos[0] < 14:
            self.pos[0], self.vel[0] = 14, 0
        elif self.pos[0] > T.WORLD_W - 14:
            self.pos[0], self.vel[0] = T.WORLD_W - 14, 0
        if self.pos[1] < 16:
            self.pos[1] = 16
            self.vel[1] = max(self.vel[1], 0)

        # ground: the magpie always lands on its feet, even out of a dive
        if self.pos[1] >= REST_Y:
            self.pos[1] = REST_Y
            if not self.grounded:
                events.append("landed")
                if self.state == "swoop":
                    self.state = "fly"
                    self.swoop_cd = T.SWOOP_COOLDOWN
                    self.vel[0] *= 0.3  # skid to a stop
            self.vel[1] = 0
            self.grounded = True
        elif self.vel[1] < 0 or (self.grounded and not self.perched and self.pos[1] < REST_Y - 1):
            self.grounded = False

        self.flap_phase += dt * (30 if self.flap_anim > 0 else 5)
        if self.state == "swoop":
            self.trail.append((self.pos[0], self.pos[1]))
        elif self.trail:
            self.trail.pop(0)
        self.trail = self.trail[-8:]
        return events

    # -- drawing ----------------------------------------------------------

    def draw(self, dst, cam):
        cx, cy = cam
        # speed lines while swooping
        for i, (x, y) in enumerate(self.trail):
            k = (i + 1) / max(1, len(self.trail))
            pygame.draw.line(dst, P.BONE, (x - cx - self.facing * 30 * k, y - cy - 6),
                             (x - cx - self.facing * 60 * k, y - cy - 6), 2)
            pygame.draw.line(dst, P.BONE, (x - cx - self.facing * 24 * k, y - cy + 6),
                             (x - cx - self.facing * 50 * k, y - cy + 6), 2)
        blink = self.invuln > 0 and int(self.t * 16) % 2 == 0
        flap = self.flap_phase if not self.grounded else 1.2
        bob = 0.0
        if self.grounded and self.walking:
            bob = abs(math.sin(self.walk)) * 2  # up and down once per step
        surf, anchor = art.draw_magpie(flap, tucked=self.state == "swoop", stunned=self.state == "stun",
                                       flash=blink, standing=self.grounded,
                                       walk=self.walk if self.walking else None)
        art.blit_actor(dst, surf, anchor, (self.pos[0] - cx, self.pos[1] - cy - bob), self.facing, self.angle,
                       140 if blink else 255)
        if self.claw_t > 0:
            k = 1 - self.claw_t / T.CLAW_ACTIVE
            ccx, ccy = self.claw_center()
            for j in range(3):
                off = (j - 1) * 8
                start = math.radians(-60 + k * 40)
                rect = pygame.Rect(0, 0, T.CLAW_RADIUS * 2, T.CLAW_RADIUS * 2)
                rect.center = (ccx - cx, ccy - cy + off)
                if self.facing > 0:
                    pygame.draw.arc(dst, P.BONE, rect, start, start + 1.4, 3)
                else:
                    pygame.draw.arc(dst, P.BONE, rect, math.pi - start - 1.4, math.pi - start, 3)
        if self.state == "stun":
            art.stars(dst, (self.pos[0] - cx, self.pos[1] - cy - 18), self.t)
        if self.pulled:
            from .fx import outlined_text
            img = outlined_text("!", 22, P.WATTLE, P.CHARCOAL, None, 2, italic=False)
            dst.blit(img, (self.pos[0] - cx - img.get_width() / 2, self.pos[1] - cy - 50))
