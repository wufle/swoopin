"""Attackers. Each has hit zones, a route to the nest, and a KO/recover cycle.

Hit zones are (name, local offset, radius) in priority order, defined in the
same local space as the art (facing right, relative to the sprite anchor).
"""

import math
import random

import pygame

from . import art
from . import palette as P
from . import tuning as T

GY = T.GROUND_Y
NX, NY = T.NEST_X, T.NEST_Y


def lerp(a, b, k):
    return a + (b - a) * k


def trunk_half_width(y):
    k = (y - NY) / (GY - NY)
    return lerp(11, 24, max(0.0, min(1.0, k)))


class Threat:
    kind = "?"
    is_kid = False
    flies = False
    climbs = False
    ZONES = []

    def __init__(self, game, side):
        self.game = game
        self.side = side  # -1 came from the left, +1 from the right
        st = T.THREATS[self.kind]
        d = game.d
        self.max_hp = st["hp"] + (1 if d >= T.HP_PLUS_ONE_AT else 0) + (1 if d >= T.HP_PLUS_TWO_AT else 0)
        self.hp = float(self.max_hp)
        self.speed = st["speed"] * (1 + T.SPEED_SCALE_MAX * d)
        self.score = st["score"]
        self.attack_time = st["attack_time"] * lerp(T.ATTACK_TIME_SCALE_START, T.ATTACK_TIME_SCALE_END, d)
        self.pos = [0.0, 0.0]
        self.vel = [0.0, 0.0]
        self.facing = -side
        self.angle = 0.0
        self.state = "approach"
        self.t = 0.0
        self.anim = random.uniform(0, 6)
        self.progress = 0.0
        self.ko_t = 0.0
        self.scared_t = 0.0
        self.first_seen = None
        self.succeeded = False
        self.ko_count = 0

    # -- queries ----------------------------------------------------------

    @property
    def alive(self):
        return self.state != "gone"

    @property
    def hittable(self):
        return self.state not in ("ko", "falling", "gone")

    @property
    def threatening(self):
        return self.state in ("attack",) or (self.climbs and self.state == "climb" and self.pos[1] < NY + 80)

    def zone_list(self):
        return self.ZONES

    def zones(self):
        if not self.hittable:
            return []
        out = []
        for name, (lx, ly), r in self.zone_list():
            ox, oy = art.xform((lx, ly), self.facing, self.angle)
            out.append((name, (self.pos[0] + ox, self.pos[1] + oy), r))
        return out

    def center(self):
        zs = self.zone_list()
        lx, ly = zs[-1][1]
        ox, oy = art.xform((lx, ly), self.facing, self.angle)
        return self.pos[0] + ox, self.pos[1] + oy

    def head_pos(self):
        for name, (lx, ly), r in self.ZONES:
            if name in ("head", "helmet"):
                ox, oy = art.xform((lx, ly - r - 4), self.facing, self.angle)
                return self.pos[0] + ox, self.pos[1] + oy
        return self.center()

    # -- damage -----------------------------------------------------------

    def take_damage(self, dmg, from_pos):
        """Apply damage. Returns True if this knocked the threat out."""
        if self.state in ("flee", "flee_win") and not getattr(self, "carrying", False):
            self.on_hurt(from_pos)  # already running away: points, but no second KO
            return False
        self.hp -= dmg
        self.progress = max(0.0, self.progress - 0.4)
        if self.hp <= 0:
            self.knock_out()
            return True
        self.on_hurt(from_pos)
        return False

    def knock_out(self):
        self.hp = 0
        self.ko_count += 1
        self.state = "ko"
        d = self.game.d
        self.ko_t = lerp(T.KO_RECOVER_START, T.KO_RECOVER_END, d)
        self.game.notify_ko(self)

    def on_hurt(self, from_pos):
        self.scared_t = 0.8

    # -- lifecycle --------------------------------------------------------

    def update(self, dt):
        self.t += dt
        self.scared_t = max(0.0, self.scared_t - dt)
        if self.first_seen is None and self.on_screen():
            self.first_seen = self.game.clock

    def on_screen(self):
        cx = self.game.cam[0]
        return cx - 10 < self.pos[0] < cx + T.SCREEN_W + 10 and -10 < self.pos[1] < T.SCREEN_H

    def exit_check(self):
        if self.pos[0] < -120 or self.pos[0] > T.WORLD_W + 120 or self.pos[1] < -160:
            self.state = "gone"
            self.game.threat_exited(self)


# --------------------------------------------------------------------------
# Ground walkers: kids, bike kids, posties
# --------------------------------------------------------------------------

class Walker(Threat):
    stop_dist = 46
    can_throw = False

    def __init__(self, game, side):
        super().__init__(game, side)
        self.pos = [NX + side * (T.WORLD_W / 2 + 60), float(GY)]
        self.target_x = NX + side * self.stop_dist
        self.scatter_t = 0.0
        self.throw_t = random.uniform(1.0, 3.0)
        self.throw_anim = 0.0
        self.nest_toss_t = 0.0
        self.duck_t = 0.0
        self.duck_checked = -1
        self.knock_v = 0.0
        self.fall_t = 0.0

    def ko_angle(self):
        return 90 * self.facing

    def update(self, dt):
        super().update(dt)
        g = self.game
        self.throw_anim = max(0.0, self.throw_anim - dt * 3)
        self.duck_t = max(0.0, self.duck_t - dt)
        # knockback slide
        if self.knock_v:
            self.pos[0] += self.knock_v * dt
            self.knock_v *= max(0.0, 1 - 6 * dt)
            if abs(self.knock_v) < 5:
                self.knock_v = 0.0

        if self.state == "ko":
            self.fall_t = min(1.0, self.fall_t + dt * 5)
            self.angle = self.ko_angle() * self.fall_t
            self.ko_t -= dt
            if self.ko_t <= 0:
                self.state = "flee"
                self.angle = 0
                self.fall_t = 0
                self.facing = self.side
                self.hp = 0.0
                g.say_flee(self)
            return
        if self.state in ("flee", "flee_win"):
            self.facing = self.side
            self.anim += dt * 10
            self.pos[0] += self.side * self.speed * (1.1 if self.state == "flee" else 1.3) * dt
            self.exit_check()
            return

        self.maybe_duck()
        self.anim += dt * (10 if self.state != "attack" else 0)
        if self.scatter_t > 0:
            self.scatter_t -= dt
            self.facing = self.side
            self.pos[0] += self.side * self.speed * 1.2 * dt
            self.anim += dt * 6
            return

        if self.state == "approach":
            self.facing = -self.side
            dx = self.target_x - self.pos[0]
            step = self.speed * dt * (0.35 if self.scared_t > 0 else 1.0)
            if abs(dx) <= step:
                self.pos[0] = self.target_x
                self.state = "attack"
            else:
                self.pos[0] += math.copysign(step, dx)
            self.maybe_throw(dt)
        elif self.state == "attack":
            self.facing = -self.side
            if abs(self.pos[0] - self.target_x) > 8:
                self.state = "approach"
                return
            if self.scared_t <= 0:
                self.progress += dt / self.attack_time
            self.nest_toss_t -= dt
            if self.nest_toss_t <= 0:
                self.nest_toss_t = 0.55
                self.throw_anim = 1.0
                self.toss_at_nest()
            if self.progress >= 1.0:
                self.progress = 0.0
                self.succeeded = True
                g.nest_hit(self)
                self.state = "flee_win"

    def toss_at_nest(self):
        hx, hy = self.head_pos()
        self.game.fx.prop("rock", (hx, hy), (0, 0), target=(NX + random.uniform(-12, 12), NY - 4), spin=600)

    def maybe_throw(self, dt):
        g = self.game
        if not self.can_throw or g.clock < 90 or self.scared_t > 0:
            return
        self.throw_t -= dt
        if self.throw_t > 0:
            return
        m = g.magpie
        dx = m.pos[0] - self.pos[0]
        if abs(dx) > 340 or m.pos[1] > GY - 30:
            self.throw_t = 0.5
            return
        self.throw_t = lerp(T.THROW_INTERVAL_START, T.THROW_INTERVAL_END, g.d) * random.uniform(0.8, 1.3)
        self.throw_anim = 1.0
        hx, hy = self.head_pos()
        speed = 430
        lead = T.THROW_LEAD_MAX * g.d
        tx = m.pos[0] + m.vel[0] * 0.5 * lead
        ty = m.pos[1] + m.vel[1] * 0.3 * lead
        ddx, ddy = tx - hx, ty - hy
        dist = math.hypot(ddx, ddy) or 1
        tof = dist / speed
        vx = ddx / tof
        vy = ddy / tof - 0.5 * T.GRAVITY * 0.6 * tof
        g.spawn_projectile(Projectile("stick" if random.random() < 0.6 else "rock", (hx, hy), (vx, vy)))
        self.facing = 1 if dx > 0 else -1

    def maybe_duck(self):
        g = self.game
        m = g.magpie
        if g.d < T.DUCK_FROM or self.state not in ("approach", "attack"):
            return
        if m.state != "swoop" or m.swoop_id == self.duck_checked:
            return
        dx = self.pos[0] - m.pos[0]
        if abs(dx) < 200 and math.copysign(1, dx) == math.copysign(1, m.vel[0]) and m.pos[1] < self.pos[1]:
            self.duck_checked = m.swoop_id
            chance = T.DUCK_CHANCE_MAX * (g.d - T.DUCK_FROM) / (1 - T.DUCK_FROM)
            if random.random() < chance:
                self.duck_t = 0.55

    def on_hurt(self, from_pos):
        super().on_hurt(from_pos)
        away = 1 if self.pos[0] > from_pos[0] else -1
        if self.state == "attack" or self.state == "approach":
            self.knock_v = away * 220


class Kid(Walker):
    kind = "kid"
    is_kid = True
    can_throw = True
    ZONES = [("eye", (5, -54), 3.5), ("head", (0, -52), 11), ("body", (0, -36), 14)]
    DUCK_ZONES = [("body", (0, -28), 12)]

    def __init__(self, game, side, helmet=False):
        super().__init__(game, side)
        self.shirt = random.choice(art.SHIRTS)
        self.helmet = helmet
        self.hat = None if helmet else random.choice(["bucket", "bucket", "cap", None])
        self.icecream = random.choice([P.WARATAH, P.BONE, None]) if not helmet else None

    def zone_list(self):
        return self.DUCK_ZONES if self.duck_t > 0 else self.ZONES

    def draw(self, dst, cam):
        ko = self.state == "ko"
        scared = self.scared_t > 0 or self.state in ("flee", "flee_win") or self.scatter_t > 0
        surf, anchor = art.draw_kid(self.anim, self.shirt, self.hat, self.helmet, ko=ko, duck=self.duck_t > 0,
                                    scared=scared and not ko, throwing=self.throw_anim, icecream=self.icecream)
        art.blit_actor(dst, surf, anchor, (self.pos[0] - cam[0], self.pos[1] - cam[1] - (6 if ko else 0)),
                       self.facing, self.angle)


class BikeKid(Walker):
    kind = "bike"
    is_kid = True
    stop_dist = 58
    ZONES = [("eye", (7, -52), 3.5), ("backhead", (-8, -48), 6), ("helmet", (2, -60), 10), ("head", (4, -48), 8),
             ("body", (-2, -30), 16)]

    def __init__(self, game, side):
        super().__init__(game, side)
        self.shirt = random.choice(art.SHIRTS)
        self.crashed = False

    def knock_out(self):
        super().knock_out()
        if not self.crashed:
            self.crashed = True
            fx = self.game.fx
            fx.prop("bikeframe", (self.pos[0], self.pos[1] - 16), (-self.facing * 60, -200), life=5.0)
            fx.prop("wheel", (self.pos[0] + self.facing * 18, self.pos[1] - 12), (self.facing * 120, -260),
                    life=6.0, spin=0)

    def draw(self, dst, cam):
        ko = self.state == "ko"
        p = (self.pos[0] - cam[0], self.pos[1] - cam[1])
        if self.crashed:
            surf, anchor = art.draw_kid(self.anim, self.shirt, None, False, ko=ko, scared=not ko)
            art.blit_actor(dst, surf, anchor, (p[0], p[1] - (6 if ko else 0)), self.facing, self.angle)
            return
        scared = self.scared_t > 0 or self.state in ("flee", "flee_win")
        surf, anchor = art.draw_bike_kid(self.anim, self.shirt, ko=ko, scared=scared)
        art.blit_actor(dst, surf, anchor, p, self.facing, self.angle)

    def update(self, dt):
        if self.crashed and self.state == "flee":
            self.speed = T.THREATS["kid"]["speed"] * 1.6
        super().update(dt)


class Postie(Walker):
    kind = "postie"
    stop_dist = 70
    ZONES = [("eye", (10, -68), 3.5), ("helmet", (2, -77), 9), ("head", (5, -66), 9), ("body", (0, -40), 20)]

    def ko_angle(self):
        return 70 * self.facing

    def knock_out(self):
        super().knock_out()
        for _ in range(8):
            self.game.fx.prop("letter", (self.pos[0] - self.facing * 30, self.pos[1] - 40),
                              (random.uniform(-160, 160), random.uniform(-380, -160)), life=4.0)

    def toss_at_nest(self):
        hx, hy = self.head_pos()
        self.game.fx.prop("letter", (hx, hy), (0, 0), target=(NX + random.uniform(-12, 12), NY - 4), spin=500)

    def draw(self, dst, cam):
        ko = self.state == "ko"
        surf, anchor = art.draw_postie(self.anim, ko=ko)
        art.blit_actor(dst, surf, anchor, (self.pos[0] - cam[0], self.pos[1] - cam[1]), self.facing, self.angle)


# --------------------------------------------------------------------------
# Birds
# --------------------------------------------------------------------------

class Bird(Threat):
    flies = True
    nest_offset = (0, -16)
    weave_freq = 3.0
    weave_amp = 60.0
    lunge_speed = 420
    LUNGE_CD = (1.4, 2.4)
    lunge_sound = "caw"

    def __init__(self, game, side, entry=None, decoy=False):
        super().__init__(game, side)
        cx = game.cam[0]
        if entry == "top":
            self.pos = [cx + random.uniform(80, T.SCREEN_W - 80), -40.0]
        elif entry == "high_side":
            self.pos = [NX + side * (T.WORLD_W / 2 + 40), random.uniform(40, 170)]
        else:
            self.pos = [NX + side * random.uniform(200, T.WORLD_W / 2 + 40), -40.0]
        self.decoy = decoy
        self.decoy_t = random.uniform(6, 9) if decoy else 0
        self.lunge_cd = 1.0
        self.stagger = 0.0
        self.carrying = False
        self.weave = random.uniform(0, 6)
        self.ground_t = 0.0

    def target(self):
        if self.decoy and self.decoy_t > 0:
            m = self.game.magpie
            return m.pos[0] - self.side * 70, m.pos[1] - 40
        return NX + self.nest_offset[0] * self.side, NY + self.nest_offset[1]

    def update(self, dt):
        super().update(dt)
        g = self.game
        self.anim += dt * 14
        self.stagger = max(0.0, self.stagger - dt)
        if self.state == "falling":
            self.vel[1] += T.GRAVITY * 0.9 * dt
            self.pos[0] += self.vel[0] * dt
            self.pos[1] += self.vel[1] * dt
            self.angle += 540 * dt
            if self.pos[1] >= GY - 6:
                self.pos[1] = GY - 6
                self.state = "ko"
                self.angle = 180
                g.fx.shake.add(T.SHAKE_SMALL)
                g.audio.play("thud")
            return
        if self.state == "ko":
            self.ko_t -= dt
            if self.ko_t <= 0:
                self.state = "flee"
                self.angle = 0
                self.vel = [self.side * self.speed, -self.speed]
            return
        if self.state in ("flee", "flee_win"):
            sp = self.speed * (1.0 if self.carrying else 1.2)
            self.vel[0] += (self.side * sp - self.vel[0]) * min(1, 3 * dt)
            self.vel[1] += (-sp * 0.7 - self.vel[1]) * min(1, 3 * dt)
            self.pos[0] += self.vel[0] * dt
            self.pos[1] += self.vel[1] * dt
            self.facing = 1 if self.vel[0] > 0 else -1
            self.angle = 0
            self.exit_check()
            return

        if self.decoy:
            self.decoy_t -= dt
        tx, ty = self.target()
        dx, dy = tx - self.pos[0], ty - self.pos[1]
        dist = math.hypot(dx, dy) or 1
        if self.state == "attack":
            self.pos[0] += (tx - self.pos[0]) * min(1, 6 * dt) + math.sin(self.t * 20) * 0.6
            self.pos[1] += (ty - self.pos[1]) * min(1, 6 * dt)
            self.facing = -self.side if abs(dx) < 4 else (1 if dx > 0 else -1)
            if self.stagger <= 0:
                self.progress += dt / self.attack_time
            if dist > 24:
                self.state = "approach"
            if self.progress >= 1.0:
                self.progress = 0
                self.complete_attack()
            return
        # approach / harass
        weave = math.sin(self.t * self.weave_freq + self.weave) * self.weave_amp
        want = self.speed * (0.4 if self.stagger > 0 else 1.0)
        nx, ny = dx / dist, dy / dist
        tvx = nx * want + (-ny) * weave * 0.6
        tvy = ny * want + nx * weave * 0.6
        self.vel[0] += (tvx - self.vel[0]) * min(1, 4 * dt)
        self.vel[1] += (tvy - self.vel[1]) * min(1, 4 * dt)
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.pos[1] = min(self.pos[1], GY - 30)
        if abs(self.vel[0]) > 10:
            self.facing = 1 if self.vel[0] > 0 else -1
        if self.decoy and self.decoy_t > 0:
            self.harass(dt)
        elif dist < 18:
            self.state = "attack"

    def harass(self, dt):
        m = self.game.magpie
        self.lunge_cd -= dt
        dx, dy = m.pos[0] - self.pos[0], m.pos[1] - self.pos[1]
        d = math.hypot(dx, dy)
        if self.lunge_cd <= 0 and d < 150:
            self.lunge_cd = random.uniform(*self.lunge_cd_range()) * (1.3 - self.game.d * 0.5)
            self.vel = [dx / (d or 1) * self.lunge_speed, dy / (d or 1) * self.lunge_speed]
            self.game.audio.play(self.lunge_sound)
        if d < 22 and m.hurt(self.pos[0]):
            self.game.magpie_hurt(self, "PECKED!")

    def lunge_cd_range(self):
        return self.LUNGE_CD

    def complete_attack(self):
        self.succeeded = True
        self.game.nest_hit(self)
        self.state = "flee_win"

    def knock_out(self):
        super().knock_out()
        self.state = "falling"
        self.vel = [self.vel[0] * 0.3, -120]

    def on_hurt(self, from_pos):
        super().on_hurt(from_pos)
        dx, dy = self.pos[0] - from_pos[0], self.pos[1] - from_pos[1]
        d = math.hypot(dx, dy) or 1
        self.vel = [dx / d * 320, dy / d * 320 - 80]
        self.stagger = 0.6
        if self.state == "attack":
            self.state = "approach"


class Crow(Bird):
    kind = "crow"
    ZONES = [("eye", (17, -8), 3), ("head", (14, -6), 8), ("body", (-3, 0), 12)]

    def draw(self, dst, cam):
        ko = self.state in ("ko", "falling")
        surf, anchor = art.draw_crow(self.anim, ko=ko)
        art.blit_actor(dst, surf, anchor, (self.pos[0] - cam[0], self.pos[1] - cam[1]), self.facing, self.angle)


class Butcherbird(Bird):
    kind = "butcherbird"
    nest_offset = (-6, -14)
    ZONES = [("eye", (13, -6), 2.5), ("head", (11, -5), 6), ("body", (-2, 0), 10)]

    def complete_attack(self):
        if self.game.steal_egg(self):
            self.carrying = True
            self.state = "flee_win"
        else:
            super().complete_attack()

    def knock_out(self):
        if self.carrying:
            self.carrying = False
            self.game.egg_dropped(self)
        super().knock_out()

    def exit_check(self):
        super().exit_check()
        if self.state == "gone" and self.carrying:
            self.carrying = False
            self.game.egg_escaped(self)

    def draw(self, dst, cam):
        ko = self.state in ("ko", "falling")
        surf, anchor = art.draw_butcherbird(self.anim, ko=ko, carrying=self.carrying)
        art.blit_actor(dst, surf, anchor, (self.pos[0] - cam[0], self.pos[1] - cam[1]), self.facing, self.angle)


class DjitiDjiti(Bird):
    """Willie wagtail (Noongar: Djiti Djiti). Tiny, fearless, mobs the magpie.

    Spends most of its visit darting at the magpie with chattering pecks,
    then, if nobody has dealt with it, dives on the nest.
    """

    kind = "djiti"
    nest_offset = (4, -12)
    weave_freq = 9.0
    weave_amp = 110.0
    lunge_speed = 540
    LUNGE_CD = (0.8, 1.5)
    lunge_sound = "chatter"
    ZONES = [("eye", (11, -5), 2), ("head", (9, -4), 5), ("body", (-2, 0), 8)]

    def __init__(self, game, side, entry=None):
        super().__init__(game, side, entry, decoy=True)
        self.decoy_t = random.uniform(9, 13)
        self.wag = 0.0

    def update(self, dt):
        self.wag += dt * 16
        super().update(dt)

    def harass(self, dt):
        before = self.lunge_cd
        super().harass(dt)
        if self.lunge_cd > before and random.random() < 0.5:
            self.game.fx.text("CHIT-CHIT!", (self.pos[0], self.pos[1] - 18), "plain", 15, drift=-40, life=0.6)

    def draw(self, dst, cam):
        ko = self.state in ("ko", "falling")
        surf, anchor = art.draw_djiti(self.anim, self.wag, ko=ko)
        art.blit_actor(dst, surf, anchor, (self.pos[0] - cam[0], self.pos[1] - cam[1]), self.facing, self.angle)


# --------------------------------------------------------------------------
# Climbers: cats and goannas come up the trunk
# --------------------------------------------------------------------------

class Climber(Threat):
    climbs = True

    def __init__(self, game, side, waits=False):
        super().__init__(game, side)
        self.pos = [NX + side * (T.WORLD_W / 2 + 60), float(GY)]
        self.climb_speed = T.CLIMB_SPEED[self.kind] * (1 + T.SPEED_SCALE_MAX * game.d)
        self.wait_t = random.uniform(4, 7) if waits else 0.0
        if waits:
            self.state = "wait"
        self.fall_v = 0.0

    @property
    def threatening(self):
        return self.state == "attack" or (self.state == "climb" and self.pos[1] < NY + 90)

    def trunk_x(self):
        return NX + self.side * trunk_half_width(self.pos[1])

    def climb_pose(self):
        # facing right + rotate 90 CCW -> head up, feet against the trunk (left side)
        self.facing = -self.side
        self.angle = -90 * self.side

    def update(self, dt):
        super().update(dt)
        g = self.game
        if self.state == "wait":
            # lurk near the edge until the magpie is on the far side of the tree
            hold_x = NX + self.side * (T.WORLD_W / 2 - 50)
            self.facing = -self.side
            if abs(self.pos[0] - hold_x) > 2:
                self.pos[0] += math.copysign(min(abs(hold_x - self.pos[0]), self.speed * dt), hold_x - self.pos[0])
                self.anim += dt * 8
            self.wait_t -= dt
            far_side = (g.magpie.pos[0] - NX) * self.side < -40
            if far_side or self.wait_t <= 0:
                self.state = "approach"
                if far_side:
                    self.speed *= 1.3
            return
        if self.state == "falling":
            self.fall_v += T.GRAVITY * dt
            self.pos[1] += self.fall_v * dt
            self.pos[0] += self.side * 60 * dt
            self.angle += 600 * dt * self.side
            if self.pos[1] >= GY:
                self.pos[1] = GY
                self.state = "ko"
                self.angle = 180
                self.facing = -self.side
                g.audio.play("thud")
                g.fx.shake.add(T.SHAKE_SMALL)
            return
        if self.state == "ko":
            self.ko_t -= dt
            if self.ko_t <= 0:
                self.state = "flee"
                self.angle = 0
                self.pos[1] = GY
                g.say_flee(self)
            return
        if self.state in ("flee", "flee_win"):
            if self.pos[1] < GY:  # scramble back down first
                self.pos[1] = min(GY, self.pos[1] + self.climb_speed * 3 * dt)
                self.pos[0] = self.trunk_x()
                self.facing = self.side
                self.angle = -90 * self.side + 180
                if self.pos[1] >= GY:
                    self.angle = 0
                return
            self.facing = self.side
            self.angle = 0
            self.anim += dt * 12
            self.pos[0] += self.side * self.speed * 1.4 * dt
            self.exit_check()
            return
        if self.state == "approach":
            self.facing = -self.side
            self.anim += dt * 10
            tx = NX + self.side * trunk_half_width(GY)
            dx = tx - self.pos[0]
            step = self.speed * dt
            if abs(dx) <= step:
                self.pos[0] = tx
                self.state = "climb"
                self.climb_pose()
            else:
                self.pos[0] += math.copysign(step, dx)
            return
        if self.state == "climb":
            self.climb_pose()
            self.anim += dt * 8
            if self.scared_t <= 0:
                self.pos[1] -= self.climb_speed * dt
            self.pos[0] = self.trunk_x()
            if self.pos[1] <= NY + 24:
                self.pos[1] = NY + 24
                self.state = "attack"
            return
        if self.state == "attack":
            self.climb_pose()
            self.pos[0] = self.trunk_x()
            if self.scared_t <= 0:
                self.progress += dt / self.attack_time
            if self.progress >= 1.0:
                self.progress = 0
                self.succeeded = True
                g.nest_hit(self)
                self.state = "flee_win"

    def on_hurt(self, from_pos):
        super().on_hurt(from_pos)
        if self.state in ("climb", "attack"):
            self.state = "climb"
            self.pos[1] = min(GY - 10, self.pos[1] + 40)
        self.scared_t = 0.5

    def knock_out(self):
        super().knock_out()
        if self.pos[1] < GY - 4:
            self.state = "falling"
            self.fall_v = -150


def _climber_pos(th, cam, lift):
    y = th.pos[1] - cam[1] - (lift if th.state == "ko" else 0)
    return th.pos[0] - cam[0], y


class Cat(Climber):
    kind = "cat"
    ZONES = [("eye", (26, -28), 3), ("head", (22, -26), 10), ("body", (0, -18), 15)]

    def draw(self, dst, cam):
        surf, anchor = art.draw_cat(self.anim, ko=self.state in ("ko", "falling"))
        art.blit_actor(dst, surf, anchor, _climber_pos(self, cam, 30), self.facing, self.angle)


class Goanna(Climber):
    kind = "goanna"
    ZONES = [("eye", (40, -23), 4.5), ("head", (38, -20), 11), ("body", (-2, -15), 20)]

    def draw(self, dst, cam):
        surf, anchor = art.draw_goanna(self.anim, ko=self.state in ("ko", "falling"))
        art.blit_actor(dst, surf, anchor, _climber_pos(self, cam, 26), self.facing, self.angle)


# --------------------------------------------------------------------------
# Projectiles thrown at the magpie
# --------------------------------------------------------------------------

class Projectile:
    def __init__(self, kind, pos, vel):
        self.kind = kind
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.angle = 0.0
        self.alive = True
        self.surf, self.anchor = art.draw_prop(kind)

    def update(self, dt, game):
        self.vel[1] += T.GRAVITY * 0.6 * dt
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.angle += 720 * dt
        m = game.magpie
        if math.hypot(m.pos[0] - self.pos[0], m.pos[1] - self.pos[1]) < 18:
            if m.hurt(self.pos[0] - self.vel[0]):
                game.magpie_hurt(self, "OUCH!")
            self.alive = False
            game.fx.prop(self.kind, self.pos, (-self.vel[0] * 0.3, -100), life=2.0)
        elif self.pos[1] >= GY + 4 or self.pos[0] < -50 or self.pos[0] > T.WORLD_W + 50:
            self.alive = False
            game.fx.prop(self.kind, self.pos, (self.vel[0] * 0.3, -abs(self.vel[1]) * 0.3), life=2.0)

    def draw(self, dst, cam):
        art.blit_actor(dst, self.surf, self.anchor, (self.pos[0] - cam[0], self.pos[1] - cam[1]), 1, self.angle)


def progress_bar(dst, pos, k, cam):
    x, y = pos[0] - cam[0] - 16, pos[1] - cam[1] - 12
    pygame.draw.rect(dst, P.CHARCOAL, (x - 1, y - 1, 34, 7))
    pygame.draw.rect(dst, P.WARATAH, (x, y, 32 * max(0.0, min(1.0, k)), 5))
