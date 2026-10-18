"""Swoopin: entry point, game loop and scene manager."""

import json
import math
import os
import random
import sys
from pathlib import Path

import pygame

from . import art, hits, stats
from . import palette as P
from . import tuning as T
from .audio import Audio
from .fx import FX, outlined_text
from .hud import HUD
from .level import Level
from .magpie import Controls, Magpie
from .spawner import Spawner
from .threats import Poop, progress_bar

W, H = T.SCREEN_W, T.SCREEN_H
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "swoopin"
SCORE_FILE = DATA_DIR / "highscore.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


def load_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except Exception:
        return {}


def save_settings(settings):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings))
    except OSError:
        pass


def load_high():
    try:
        return json.loads(SCORE_FILE.read_text())
    except Exception:
        return {"score": 0, "time": 0}


def save_high(score, time_survived):
    best = load_high()
    if score <= best.get("score", 0):
        return False
    try:
        SCORE_FILE.parent.mkdir(parents=True, exist_ok=True)
        SCORE_FILE.write_text(json.dumps({"score": score, "time": round(time_survived, 1)}))
    except OSError:
        pass
    return True


class Game:
    def __init__(self, audio=True):
        self.audio = Audio(audio)
        self.level = Level()
        self.hud = HUD()
        self.scene = "title"
        self.paused = False
        self.debug = False
        self.fps = 60.0
        self.high = load_high()
        self.title_t = 0.0
        self.new_game()
        self.scene = "title"

    # -- setup ------------------------------------------------------------

    def new_game(self):
        self.magpie = Magpie()
        self.threats = []
        self.projectiles = []
        self.fx = FX()
        self.fx.avoid = lambda: self.magpie.pos
        self.hud = HUD()
        self.level.trophy_hats = 0
        self.score = 0
        self.combo = 0
        self.eggs = T.START_EGGS
        self.carried = 0
        self.in_transit = 0
        self.timers = []
        self.wave_hits = 0
        self.wave_kos = 0
        self.wave_eggs_lost = 0
        self.cam = [T.NEST_X - W / 2, 0.0]
        self.end_t = None
        self.new_best = False
        self.seen_perch_tip = False
        self.stats = stats.Stats()
        self.end_screen_t = 0.0
        self.spawner = Spawner(self)
        self.scene = "play"
        self.paused = False
        self.audio.play("carol", 0.8)
        self.banner("WAVE 1")
        self.banner("PROTECT THE NEST!", sub=True)

    @property
    def d(self):
        return self.spawner.d

    @property
    def clock(self):
        return self.spawner.t

    # -- callbacks used by threats / hits ---------------------------------

    def combo_mult(self):
        return min(T.COMBO_MAX_MULT, 1 + max(0, self.combo - 1) // T.COMBO_STEP)

    def add_score(self, pts, pos, label=None):
        pts = int(pts)
        self.score += pts
        text = f"{label} +{pts}" if label else f"+{pts}"
        self.fx.text(text, (pos[0], pos[1] - 26), "plain", 16, drift=-55, life=0.85)

    def banner(self, text, sub=False):
        self.hud.banner(text, sub)

    def later(self, delay, fn):
        self.timers.append([delay, fn])

    def notify_ko(self, th):
        if th.is_kid and self.spawner.phase >= 3:
            for o in self.threats:
                if (o is not th and o.is_kid and not o.innocent and o.state == "approach"
                        and abs(o.pos[0] - th.pos[0]) < 170):
                    o.scatter_t = 1.4

    def kid_hit(self, th):
        self.spawner.kid_hit(th)

    def say_flee(self, th):
        if th.is_kid and th.innocent:  # off home, crying for mum
            self.fx.text("MUUUUM!", th.head_pos(), "plain", 20, drift=-40)
            self.audio.play("mum", 0.8, min_gap=0.8)
        elif th.is_kid:
            self.fx.text(random.choice(hits.WORDS["flee"]), th.head_pos(), "plain", 20, drift=-40)
            self.audio.play("waah", 0.6, min_gap=0.8)
        elif th.kind == "mum":
            self.fx.text("I'LL BE TALKING TO YOUR MOTHER!", th.head_pos(), "plain", 15, drift=-40)
        elif th.kind == "cat":
            self.fx.text("HISSS!", th.head_pos(), "plain", 18, drift=-40)
            self.audio.play("hiss", 0.8)

    def nest_hit(self, th):
        if self.eggs <= 0:
            return
        self.eggs -= 1
        self.wave_eggs_lost += 1
        self.stats.eggs_lost += 1
        self.combo = 0
        self.fx.text("CRACK!", (T.NEST_X, T.NEST_Y - 30), "bad", 32, life=0.9)
        self.fx.shake.add(T.SHAKE_BIG)
        self.audio.play("crack")
        x = T.NEST_X + random.uniform(-14, 14)
        self.fx.prop("egg", (x, T.NEST_Y - 6), (th.side * 60, -120), life=0.65)
        self.later(0.62, lambda: self.fx.splat((x + th.side * 36, T.GROUND_Y + 10)))
        self.check_over()

    def steal_egg(self, th):
        if self.eggs <= 0:
            return False
        self.eggs -= 1
        self.carried += 1
        self.wave_eggs_lost += 1
        self.stats.eggs_lost += 1
        self.combo = 0
        self.fx.text("EGG NICKED!", (T.NEST_X, T.NEST_Y - 30), "bad", 26, life=0.9)
        self.audio.play("crack", 0.6)
        return True

    def egg_dropped(self, th):
        self.carried -= 1
        self.in_transit += 1

        def arrive():
            self.in_transit -= 1
            self.eggs = min(T.MAX_EGGS, self.eggs + 1)
            self.wave_eggs_lost = max(0, self.wave_eggs_lost - 1)
            self.stats.eggs_lost -= 1
            self.stats.eggs_saved += 1
            self.fx.text("EGG SAVED!", (T.NEST_X, T.NEST_Y - 40), "good", 26, life=0.9)
            self.add_score(T.EGG_SAVED_BONUS, (T.NEST_X, T.NEST_Y - 60))
            self.audio.play("egg")

        self.fx.prop("egg", tuple(th.pos), (0, 0), target=(T.NEST_X, T.NEST_Y - 8), on_arrive=arrive, spin=300)

    def egg_escaped(self, th):
        self.carried -= 1
        x = min(max(th.pos[0], self.cam[0] + 80), self.cam[0] + W - 80)
        self.fx.text("EGG GONE!", (x, 90), "bad", 24, life=1.0)
        self.check_over()

    def steal_hat(self, th, hat):
        hx, hy = th.head_pos()

        def arrive():
            self.level.trophy_hats += 1
            self.add_score(T.HAT_BONUS, (T.NEST_X, T.NEST_Y - 40), label="HAT NICKED!")

        self.fx.prop("hat" if hat == "bucket" else "cap", (hx, hy), (0, 0), target=(T.NEST_X, T.NEST_Y - 6),
                     on_arrive=arrive, spin=360)

    def threat_exited(self, th):
        self.spawner.queue_return(th)

    def spawn_projectile(self, p):
        self.projectiles.append(p)

    def magpie_hurt(self, src, word):
        m = self.magpie
        self.combo = 0
        self.stats.times_hurt += 1
        if word == "PEPPERED!":
            self.stats.times_shot += 1
        self.fx.text(word, (m.pos[0], m.pos[1] - 30), "bad", 22)
        self.fx.burst("feather", m.pos, 6)
        self.fx.burst("feather_w", m.pos, 3)
        self.fx.shake.add(T.SHAKE_SMALL)
        self.audio.play("hurt")

    def on_wave_start(self, n):
        self.banner(f"WAVE {n}")

    def on_wave_end(self, n):
        perfect = self.wave_eggs_lost == 0
        self.banner(f"WAVE {n} DONE  -  {self.wave_hits} HITS  {self.wave_kos} KOs", sub=True)
        if perfect:
            self.stats.perfect_waves += 1
            self.score += T.PERFECT_WAVE_BONUS
            self.banner(f"PERFECT WAVE +{T.PERFECT_WAVE_BONUS}", sub=True)
            if self.eggs + self.carried + self.in_transit < T.MAX_EGGS:
                self.eggs += 1
                self.stats.eggs_restored += 1
                self.banner("+1 EGG", sub=True)
                self.audio.play("egg")
        self.audio.play("carol", 0.5)
        self.wave_hits = self.wave_kos = self.wave_eggs_lost = 0

    def check_over(self):
        if self.eggs <= 0 and self.carried <= 0 and self.in_transit <= 0 and self.end_t is None:
            self.end_t = 1.6
            self.banner("NEST RAIDED!")

    # -- update -----------------------------------------------------------

    def update(self, dt, ctl):
        if self.scene == "title":
            self.title_t += dt
            return
        if self.scene in ("over", "victory"):
            self.end_screen_t += dt
            self.fx.update(dt)
            self.hud.update(dt)
            return
        if self.paused:
            return
        if self.fx.hitpause > 0:
            self.fx.hitpause -= 1
            self.fx.shake.update(dt)
            return

        if self.end_t is not None:
            self.end_t -= dt
            ctl = Controls()
            if self.end_t <= 0:
                self.finish(victory=False)
                return

        for ev in self.magpie.update(dt, ctl):
            if ev == "flap":
                self.audio.play("flap", 0.5)
            elif ev == "swoop":
                self.stats.swoops += 1
                self.audio.play("swoop")
            elif ev == "poop":
                self.stats.poops += 1
                m = self.magpie
                self.projectiles.append(Poop(m.vent(), (m.vel[0] * T.POOP_CARRY, max(m.vel[1], 0) * 0.3 + 60)))
                self.audio.play("fart", 0.9)
            elif ev == "claw":
                self.stats.claws += 1
                self.audio.play("claw", 0.7)
            elif ev == "landed":
                self.combo = 0
            elif ev == "perched" and not self.seen_perch_tip:
                self.seen_perch_tip = True
                self.banner("ON GUARD! CLAW FROM THE NEST", sub=True)
            elif ev == "pulled":
                self.banner("BACK TO THE NEST!", sub=True)

        if self.magpie.perched:
            self.stats.perch_time += dt
        if self.end_t is None:
            self.spawner.update(dt)
        for th in self.threats:
            th.update(dt)
        self.threats = [th for th in self.threats if th.alive]
        for p in self.projectiles:
            p.update(dt, self)
        self.projectiles = [p for p in self.projectiles if p.alive]
        if self.end_t is None:
            hits.resolve(self)
        for tm in self.timers:
            tm[0] -= dt
            if tm[0] <= 0:
                tm[1]()
        self.timers = [tm for tm in self.timers if tm[0] > 0]
        self.fx.update(dt)
        self.hud.update(dt)
        self.update_camera(dt)

        if self.clock >= T.SEASON_LENGTH and self.end_t is None:
            self.finish(victory=True)

    def update_camera(self, dt):
        m = self.magpie
        target = (T.NEST_X - W / 2) * 0.3 + (m.pos[0] - W / 2) * 0.7
        target = max(0, min(T.WORLD_W - W, target))
        self.cam[0] += (target - self.cam[0]) * min(1.0, 5 * dt)

    def finish(self, victory):
        self.scene = "victory" if victory else "over"
        self.end_t = None
        self.end_screen_t = 0.0
        self.fx.clear()
        if victory:
            bonus = self.eggs * T.EGG_SURVIVAL_BONUS
            self.score += bonus
            self.egg_bonus = bonus
            self.audio.play("carol")
        else:
            self.egg_bonus = 0
        self.survived = min(self.clock, T.SEASON_LENGTH)
        self.new_best = save_high(self.score, self.survived)
        self.high = load_high()

    # -- drawing ----------------------------------------------------------

    def draw(self, dst):
        if self.scene == "title":
            self.draw_title(dst)
            return
        sx, sy = self.fx.shake.offset()
        cam = (self.cam[0] + sx, self.cam[1] + sy)
        self.level.draw_back(dst, cam)
        m = self.magpie
        self.level.draw_ring(dst, cam, 0.25 if not m.outside else 0.6 + 0.4 * math.sin(m.t * 10))
        threatened = any(th.threatening for th in self.threats)
        self.level.draw_nest(dst, cam, self.eggs, m.t, threatened)
        self.fx.draw_ground(dst, cam)
        for th in sorted(self.threats, key=lambda t: (t.flies, t.climbs)):
            th.draw(dst, cam)
            if th.state == "ko":
                hx, hy = th.head_pos()
                art.stars(dst, (hx - cam[0], hy - cam[1] - (28 if th.climbs else 4)), m.t + id(th) % 7)
            if th.progress > 0 and th.state == "attack":
                progress_bar(dst, th.head_pos(), th.progress, cam)
        for p in self.projectiles:
            p.draw(dst, cam)
        m.draw(dst, cam)
        if m.perched:
            self.level.draw_nest_front(dst, cam)
        self.fx.draw_air(dst, cam)
        if self.scene == "play":
            self.hud.draw(dst, self)
        if self.debug:
            self.hud.draw_debug(dst, self)
        if self.paused:
            self.overlay(dst, "PAUSED", ["P / ESC  resume", "Q  quit to title"])
        elif self.scene in ("over", "victory"):
            stats.draw(dst, self, self.end_screen_t)

    def overlay(self, dst, title, lines):
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((*P.CHARCOAL, 150))
        dst.blit(shade, (0, 0))
        img = self.hud.tc.get(title, 54, P.WATTLE, P.WARATAH, 4)
        dst.blit(img, (W / 2 - img.get_width() / 2, 120))
        y = 210
        for line in lines:
            if line:
                li = self.hud.tc.get(line, 22, P.BONE, P.CHARCOAL, 2)
                dst.blit(li, (W / 2 - li.get_width() / 2, y))
            y += 32

    def draw_title(self, dst):
        t = self.title_t
        cam = (T.NEST_X - W / 2, 0)
        self.level.draw_back(dst, cam)
        self.level.draw_nest(dst, cam, T.START_EGGS, t)
        # attract-mode magpie circling the nest
        a = t * 1.1
        x = T.NEST_X + math.cos(a) * 170 - cam[0]
        y = T.NEST_Y - 30 + math.sin(a * 2) * 50
        facing = -1 if math.sin(a) > 0 else 1
        surf, anchor = art.draw_magpie(t * 14)
        art.blit_actor(dst, surf, anchor, (x, y), facing, 8 * math.cos(a * 2))
        tc = self.hud.tc
        logo = tc.get("SWOOPIN", 96, P.WATTLE, P.WARATAH, 6)
        logo = pygame.transform.rotozoom(logo, 4 + math.sin(t * 2) * 2, 1.0)
        dst.blit(logo, (W / 2 - logo.get_width() / 2, 20))
        sub = tc.get("Defend the nest. Swoop the lot of 'em.", 22, P.BONE, P.CHARCOAL, 2)
        dst.blit(sub, (W / 2 - sub.get_width() / 2, 150))
        controls = ["SPACE / W / UP / CLICK   flap", "S / DOWN   swoop dive", "SHIFT / X   claw / peck",
                    "A D / LEFT RIGHT   steer  (or walk, when landed)", "CTRL   poop  (while flying)",
                    "P / ESC   pause      F11   fullscreen"]
        y = 284
        panel = pygame.Surface((440, 25 * len(controls) + 12), pygame.SRCALPHA)
        panel.fill((*P.CHARCOAL, 150))
        dst.blit(panel, (W / 2 - 220, y - 7))
        for c in controls:
            img = tc.get(c, 16, P.BONE, P.CHARCOAL, 1, False)
            dst.blit(img, (W / 2 - img.get_width() / 2, y))
            y += 25
        if int(t * 2) % 2 == 0:
            ps = tc.get("PRESS SPACE", 32, P.WATTLE, P.CHARCOAL, 3)
            dst.blit(ps, (W / 2 - ps.get_width() / 2, 460))
        best = self.high.get("score", 0)
        if best:
            img = tc.get(f"BEST {best:,}", 18, P.BONE, P.CHARCOAL, 2)
            dst.blit(img, (W - img.get_width() - 16, H - 34))

    # -- input ------------------------------------------------------------

    def handle_key(self, key):
        """Scene-level keys. Returns False to quit."""
        if key == pygame.K_F1:
            self.debug = not self.debug
        elif key == pygame.K_F11:
            toggle_fullscreen()
        elif self.scene == "title":
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self.new_game()
            elif key == pygame.K_ESCAPE:
                return False
        elif self.scene in ("over", "victory"):
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                self.new_game()
            elif key == pygame.K_ESCAPE:
                self.scene = "title"
                self.title_t = 0
        elif self.scene == "play":
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.paused = not self.paused
            elif key == pygame.K_q and self.paused:
                self.scene = "title"
                self.title_t = 0
        return True


FLAP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
SWOOP_KEYS = (pygame.K_DOWN, pygame.K_s)
CLAW_KEYS = (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_x)
POOP_KEYS = (pygame.K_LCTRL, pygame.K_RCTRL)


def toggle_fullscreen():
    """Switch modes. SCALED keeps 960x540 crisp: exact 2x at 1080p, 4x at 4K,
    letterboxed on other aspect ratios."""
    pygame.display.toggle_fullscreen()
    full = bool(pygame.display.is_fullscreen())
    pygame.mouse.set_visible(not full)
    settings = load_settings()
    settings["fullscreen"] = full
    save_settings(settings)


def open_window():
    settings = load_settings()
    full = settings.get("fullscreen", False)
    if "--fullscreen" in sys.argv:
        full = True
    elif "--windowed" in sys.argv:
        full = False
    flags = pygame.SCALED | (pygame.FULLSCREEN if full else pygame.RESIZABLE)
    try:
        screen = pygame.display.set_mode((W, H), flags, vsync=1)
    except pygame.error:
        screen = pygame.display.set_mode((W, H), flags)
    pygame.mouse.set_visible(not full)
    return screen


def main():
    pygame.init()
    pygame.display.set_caption("Swoopin")
    screen = open_window()
    game = Game(audio="--mute" not in sys.argv)
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = min(clock.tick(T.FPS) / 1000.0, 1 / 30)
        game.fps = clock.get_fps()
        ctl = Controls()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN and ev.mod & pygame.KMOD_ALT:
                toggle_fullscreen()
            elif ev.type == pygame.KEYDOWN:
                in_play = game.scene == "play" and not game.paused
                if in_play and ev.key in FLAP_KEYS:
                    ctl.flap = True
                elif in_play and ev.key in SWOOP_KEYS:
                    ctl.swoop = True
                elif in_play and ev.key in CLAW_KEYS:
                    ctl.claw = True
                elif in_play and ev.key in POOP_KEYS:
                    ctl.poop = True
                else:
                    running = game.handle_key(ev.key) and running
            elif ev.type == pygame.MOUSEBUTTONDOWN and game.scene == "play" and not game.paused:
                if ev.button == 1:
                    ctl.flap = True
                elif ev.button == 3:
                    ctl.swoop = True
        keys = pygame.key.get_pressed()
        ctl.left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        ctl.right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        game.update(dt, ctl)
        game.draw(screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
