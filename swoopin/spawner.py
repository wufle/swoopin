"""Season clock, difficulty curve, waves and directional spawn patterns."""

import random

from . import threats as TH
from . import tuning as T

# kind -> (unlock time, weight, direction)
POOL = {
    "kid": (0, 3.0, "ground"),
    "crow": (35, 1.6, "above"),
    "bike": (90, 1.5, "ground"),
    "cat": (100, 1.4, "below"),
    "djiti": (150, 1.0, "above"),
    "butcherbird": (210, 1.1, "above"),
    "postie": (360, 0.8, "ground"),
    "goanna": (400, 0.5, "below"),
}
# how many directions a wave can come from, per phase
DIRS_PER_PHASE = [1, 2, 3, 4, 4]
FIRST_GOANNA_AT = 400


def difficulty(t):
    k = max(0.0, min(1.0, t / T.SEASON_LENGTH))
    return k ** T.DIFFICULTY_EXPONENT


def phase_index(t):
    idx = 0
    for i, (start, _) in enumerate(T.PHASES):
        if t >= start:
            idx = i
    return idx


def lerp(a, b, k):
    return a + (b - a) * k


class Spawner:
    def __init__(self, game):
        self.game = game
        self.t = 0.0
        self.wave = 1
        self.wave_t = 0.0
        self.breather = False
        self.spawn_t = 1.5
        self.dirs = []
        self.returns = []  # (time, kind, side)
        self.phase = 0
        self.goanna_forced = False
        self.spawned = {k: 0 for k in POOL}
        self.spawned.update(innocent=0, dad=0)
        self.innocent_t = 2.5
        self.dad_rage = 0.0
        self.dad_side = 1
        self.pick_dirs()

    @property
    def d(self):
        return difficulty(self.t)

    def max_active(self):
        return round(lerp(T.MAX_ACTIVE_START, T.MAX_ACTIVE_END, self.d))

    def interval(self):
        return lerp(T.SPAWN_INTERVAL_START, T.SPAWN_INTERVAL_END, self.d)

    def unlocked(self):
        return [k for k, (t0, _, _) in POOL.items() if self.t >= t0]

    def pick_dirs(self):
        avail = set()
        for k in self.unlocked():
            avail.add(POOL[k][2])
        # "ground" can be either side: split into left/right
        options = []
        if "ground" in avail:
            options += ["left", "right"]
        if "above" in avail:
            options.append("above")
        if "below" in avail:
            options.append("below")
        n = min(len(options), DIRS_PER_PHASE[phase_index(self.t)])
        # bias the first waves towards the ground so the swoop gets learnt first
        if self.t < 35:
            options = ["left", "right"]
            n = 1
        self.dirs = random.sample(options, n)

    def update(self, dt):
        g = self.game
        self.t += dt
        self.wave_t += dt
        p = phase_index(self.t)
        if p != self.phase:
            self.phase = p
            g.banner(T.PHASES[p][1], sub=True)

        self.update_ambient(dt)

        if self.breather:
            if self.wave_t >= T.BREATHER:
                self.breather = False
                self.wave_t = 0.0
                self.wave += 1
                self.pick_dirs()
                self.spawn_t = 0.8
                g.on_wave_start(self.wave)
            return
        if self.wave_t >= T.WAVE_LENGTH:
            self.breather = True
            self.wave_t = 0.0
            g.on_wave_end(self.wave)
            return

        if not self.goanna_forced and self.t >= FIRST_GOANNA_AT:
            self.goanna_forced = True
            self.spawn("goanna", random.choice((-1, 1)))
            g.banner("GOANNA!", sub=True)

        # returning attackers
        for item in list(self.returns):
            if self.t >= item[0]:
                self.returns.remove(item)
                if self.active() < self.max_active() + 2:
                    self.spawn(item[1], item[2])

        self.spawn_t -= dt
        if self.spawn_t <= 0:
            self.spawn_t = self.interval() * random.uniform(0.7, 1.3)
            if self.active() < self.max_active():
                self.spawn_event()

    def update_ambient(self, dt):
        """Innocent kids wandering past, and the dads who come looking for them."""
        g = self.game
        self.innocent_t -= dt
        if self.innocent_t <= 0:
            self.innocent_t = lerp(T.INNOCENT_INTERVAL_START, T.INNOCENT_INTERVAL_END, self.d) * random.uniform(0.6, 1.4)
            strolling = sum(1 for th in g.threats if th.innocent and th.state == "stroll")
            if strolling < T.INNOCENT_MAX:
                side = random.choice((-1, 1))
                if random.random() < T.INNOCENT_BIKE_CHANCE:
                    th = TH.BikeKid(g, side, innocent=True)
                else:
                    th = TH.Kid(g, side, innocent=True)
                g.threats.append(th)
                self.spawned["innocent"] += 1
        self.dad_rage = max(0.0, self.dad_rage - T.DAD_RAGE_DECAY * dt)
        if self.dad_rage >= T.DAD_RAGE_THRESHOLD and self.count_alive("dad") < T.DAD_MAX:
            self.dad_rage = 0.0
            g.threats.append(TH.Dad(g, self.dad_side))
            self.spawned["dad"] += 1
            g.banner("ANGRY DAD!", sub=True)

    def kid_hit(self, th):
        # innocents are what really sets the dads off; nest-raiding brats had it coming
        self.dad_rage += 1.0 if th.innocent else T.DAD_RAGE_BRAT
        self.dad_side = th.side  # dad comes from the way the kid came

    def active(self):
        return sum(1 for th in self.game.threats
                   if th.state not in ("flee", "flee_win", "gone") and not th.innocent and th.kind != "dad")

    def spawn_event(self):
        direction = random.choice(self.dirs)
        if direction in ("left", "right"):
            want = "ground"
            side = -1 if direction == "left" else 1
        else:
            want = direction
            side = random.choice((-1, 1))
        kinds = [k for k in self.unlocked() if POOL[k][2] == want]
        if "goanna" in kinds and self.count_alive("goanna") >= (2 if self.phase >= 4 else 1):
            kinds.remove("goanna")
        if not kinds:
            return
        kind = random.choices(kinds, [POOL[k][1] for k in kinds])[0]
        d = self.d

        if kind == "crow" and self.phase >= 4 and random.random() < 0.3:
            self.crow_gang()
            return
        if kind == "crow" and self.phase >= 2 and random.random() < 0.5:
            self.spawn("crow", side, entry="top", decoy=True)
            self.spawn("crow", -side, entry="high_side")
            return
        if kind == "kid" and self.phase >= 3 and random.random() < 0.4:
            for i in range(random.randint(2, 3)):
                th = self.spawn("kid", side)
                th.pos[0] += side * i * 36
            return
        self.spawn(kind, side)

    def crow_gang(self):
        n = random.randint(3, 4)
        entries = ["top", "high_side", "high_side", "top"]
        for i in range(n):
            side = -1 if i % 2 == 0 else 1
            self.spawn("crow", side, entry=entries[i], decoy=(i == 0))
        self.game.banner("CROW GANG!", sub=True)

    def count_alive(self, kind):
        return sum(1 for th in self.game.threats if th.kind == kind and th.alive)

    def spawn(self, kind, side, entry=None, decoy=False):
        g = self.game
        d = self.d
        if kind == "kid":
            th = TH.Kid(g, side, helmet=self.phase >= 2 and random.random() < 0.6)
        elif kind == "bike":
            th = TH.BikeKid(g, side)
        elif kind == "postie":
            th = TH.Postie(g, side)
        elif kind == "crow":
            th = TH.Crow(g, side, entry or random.choice(["top", "high_side", None]), decoy)
            g.audio.play("caaaw", 0.7, min_gap=4.0)
        elif kind == "butcherbird":
            th = TH.Butcherbird(g, side, entry or random.choice(["top", "high_side"]))
        elif kind == "djiti":
            th = TH.DjitiDjiti(g, side, entry or random.choice(["top", "high_side"]))
            if self.spawned["djiti"] == 0:
                g.banner("DJITI DJITI!", sub=True)
        elif kind == "cat":
            th = TH.Cat(g, side, waits=self.phase >= 3 and random.random() < 0.6)
        elif kind == "goanna":
            th = TH.Goanna(g, side)
        else:
            raise ValueError(kind)
        self.spawned[kind] += 1
        g.threats.append(th)
        return th

    def queue_return(self, th):
        """A threat that was driven off may come back later."""
        d = self.d
        if th.succeeded or th.innocent or th.kind == "dad":
            return
        if random.random() < lerp(T.RETURN_CHANCE_START, T.RETURN_CHANCE_END, d):
            delay = lerp(T.RETURN_DELAY_START, T.RETURN_DELAY_END, d) * random.uniform(0.8, 1.2)
            self.returns.append((self.t + delay, th.kind, th.side))
