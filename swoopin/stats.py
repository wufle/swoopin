"""End-of-season statistics: counters kept during play, and the stats screen."""

from collections import Counter

import pygame

from . import art
from . import palette as P
from . import tuning as T

W, H = T.SCREEN_W, T.SCREEN_H

# knockout categories in display order: (key, label)
KO_ROWS = [
    ("innocent", "Innocent kids"),
    ("brat", "Brats"),
    ("bike", "Bike kids"),
    ("postie", "Posties"),
    ("crow", "Crows"),
    ("butcherbird", "Butcherbirds"),
    ("djiti", "Djiti Djiti"),
    ("cat", "Cats"),
    ("goanna", "Goannas"),
    ("dad", "Angry dads"),
    ("mum", "Mums"),
]


def ko_key(th):
    if th.is_kid and th.innocent:
        return "innocent"
    if th.kind == "kid":
        return "brat"
    return th.kind


class Stats:
    def __init__(self):
        self.swoops = 0
        self.swoop_hits = 0
        self.claws = 0
        self.hits = 0
        self.bullseyes = 0
        self.max_combo = 0
        self.kos = Counter()
        self.eggs_lost = 0
        self.eggs_saved = 0
        self.eggs_restored = 0
        self.perfect_waves = 0
        self.times_hurt = 0
        self.times_shot = 0
        self.perch_time = 0.0
        self.poops = 0
        self.poop_hits = 0

    def hit(self, game, th, kind, zone, ko):
        self.hits += 1
        if kind == "swoop":
            self.swoop_hits += 1
        if zone == "eye":
            self.bullseyes += 1
        self.max_combo = max(self.max_combo, game.combo)
        if ko:
            self.kos[ko_key(th)] += 1


# --------------------------------------------------------------------------
# icons
# --------------------------------------------------------------------------

_icons = {}


def icon(key, box=(40, 34)):
    if key in _icons:
        return _icons[key]
    if key == "innocent":
        s, _ = art.draw_kid(1.0, P.DEEP_GUM, "bucket", bag=True)
    elif key == "brat":
        s, _ = art.draw_kid(1.0, P.WARATAH, "cap", brat=True)
    elif key == "bike":
        s, _ = art.draw_bike_kid(1.0, P.OCHRE, brat=True)
    elif key == "postie":
        s, _ = art.draw_postie(1.0)
    elif key == "crow":
        s, _ = art.draw_crow(0.0)
    elif key == "butcherbird":
        s, _ = art.draw_butcherbird(0.0)
    elif key == "djiti":
        s, _ = art.draw_djiti(0.0, 1.0)
    elif key == "cat":
        s, _ = art.draw_cat(1.0)
    elif key == "goanna":
        s, _ = art.draw_goanna(1.0)
    elif key == "dad":
        s, _ = art.draw_dad(0.0)
    elif key == "mum":
        s, _ = art.draw_mum(0.0)
    else:
        s = pygame.Surface((1, 1), pygame.SRCALPHA)
    r = s.get_bounding_rect()
    s = s.subsurface(r).copy() if r.w and r.h else s
    k = min(box[0] / s.get_width(), box[1] / s.get_height())
    s = pygame.transform.smoothscale(s, (max(1, int(s.get_width() * k)), max(1, int(s.get_height() * k))))
    _icons[key] = s
    return s


def _dim(surf):
    s = surf.copy()
    s.set_alpha(70)
    return s


# --------------------------------------------------------------------------
# the screen
# --------------------------------------------------------------------------

def draw(dst, g, t):
    """Stats screen. t = seconds since the season ended (drives the reveal)."""
    st = g.stats
    tc = g.hud.tc
    shade = pygame.Surface((W, H), pygame.SRCALPHA)
    shade.fill((*P.CHARCOAL, 195))
    dst.blit(shade, (0, 0))

    victory = g.scene == "victory"
    title = tc.get("SEASON SURVIVED!" if victory else "NEST RAIDED!", 46, P.WATTLE, P.WARATAH, 4)
    dst.blit(title, (W / 2 - title.get_width() / 2, 12))
    mins, secs = divmod(int(g.survived), 60)
    if victory:
        sub = f"The chicks fledged!   {g.eggs} egg{'s' if g.eggs != 1 else ''} saved  +{g.egg_bonus:,}"
    else:
        sub = f"Survived {mins}:{secs:02d} of 10:00   -   reached wave {g.spawner.wave}"
    img = tc.get(sub, 17, P.BONE, P.CHARCOAL, 2, False)
    dst.blit(img, (W / 2 - img.get_width() / 2, 72))

    # score counts up
    k = min(1.0, t / 1.2)
    score = int(g.score * (1 - (1 - k) ** 3))
    img = tc.get(f"SCORE  {score:,}", 32, P.WATTLE, P.CHARCOAL, 3)
    dst.blit(img, (W / 2 - img.get_width() / 2, 98))
    if t > 1.2:
        best = "NEW HIGH SCORE!" if g.new_best else f"BEST  {g.high.get('score', 0):,}"
        img = tc.get(best, 16, P.WARATAH if g.new_best else P.BONE, P.CHARCOAL, 2)
        dst.blit(img, (W / 2 - img.get_width() / 2, 140))

    top = 172
    panel(dst, (40, top, 420, 318))
    panel(dst, (500, top, 420, 318))

    # left: your season
    acc = f"{100 * st.swoop_hits / st.swoops:.0f}%  ({st.swoop_hits}/{st.swoops})" if st.swoops else "-"
    pm, ps = divmod(int(st.perch_time), 60)
    rows = [
        ("Waves reached", f"{g.spawner.wave}"),
        ("Best combo", f"{st.max_combo}"),
        ("Swoop accuracy", acc),
        ("Bullseyes", f"{st.bullseyes}"),
        ("Total hits", f"{st.hits}"),
        ("Eggs lost", f"{st.eggs_lost}"),
        ("Eggs rescued / earned back", f"{st.eggs_saved} / {st.eggs_restored}"),
        ("Perfect waves", f"{st.perfect_waves}"),
        ("Hats nicked", f"{g.level.trophy_hats}"),
        ("Time guarding the nest", f"{pm}:{ps:02d}"),
        ("Angry dads / mums sent", f"{g.spawner.spawned.get('dad', 0)} / {g.spawner.spawned.get('mum', 0)}"),
        ("Shot by dads", f"{st.times_shot}"),
        ("Poops dropped / direct hits", f"{st.poops} / {st.poop_hits}"),
    ]
    header(dst, tc, "YOUR SEASON", 60, top + 10)
    y = top + 42
    for i, (label, value) in enumerate(rows):
        if t < 0.5 + i * 0.07:
            break
        dst.blit(tc.get(label, 15, P.BONE, P.CHARCOAL, 1, False), (60, y))
        v = tc.get(value, 15, P.WATTLE, P.CHARCOAL, 1, False)
        dst.blit(v, (440 - v.get_width(), y))
        y += 20

    # right: knockouts
    total = sum(st.kos.values())
    header(dst, tc, f"KNOCKOUTS  {total}", 520, top + 10)
    for i, (key, label) in enumerate(KO_ROWS):
        if t < 0.5 + (len(rows) + i) * 0.07 - 0.6:
            break
        col, row = i % 2, i // 2
        x = 520 + col * 200
        y = top + 42 + row * 45
        n = st.kos.get(key, 0)
        ic = icon(key)
        ic = ic if n else _dim(ic)
        dst.blit(ic, (x + 20 - ic.get_width() / 2, y + 17 - ic.get_height() / 2))
        fill = P.BONE if n else P.GREY
        dst.blit(tc.get(label, 13, fill, P.CHARCOAL, 1, False), (x + 46, y + 2))
        dst.blit(tc.get(f"{n}", 20, P.WATTLE if n else P.GREY, P.CHARCOAL, 2), (x + 46, y + 16))

    if t > 1.5:
        img = tc.get("SPACE  play again        ESC  title", 18, P.BONE, P.CHARCOAL, 2)
        dst.blit(img, (W / 2 - img.get_width() / 2, H - 38))


def panel(dst, rect):
    s = pygame.Surface(rect[2:], pygame.SRCALPHA)
    s.fill((*P.CHARCOAL, 170))
    dst.blit(s, rect[:2])
    pygame.draw.rect(dst, P.OCHRE, rect, 2, border_radius=6)


def header(dst, tc, text, x, y):
    img = tc.get(text, 18, P.WATTLE, P.WARATAH, 2)
    dst.blit(img, (x, y))
