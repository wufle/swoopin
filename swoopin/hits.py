"""Hit detection, damage, scoring and the comic word for each hit."""

import math
import random

from . import tuning as T

WORDS = {
    "swoop": ["BANG!", "SWOOP!", "WHACK!", "THWACK!"],
    "claw": ["CLAWED!", "SCRATCH!", "SNIP!"],
    "peck": ["PECK!", "BONK!"],
    "eye": ["BULLSEYE!", "RIGHT IN THE EYE!"],
    "helmet": ["TONK!", "BONK!"],
    "backhead": ["SMACK!", "THWACK!"],
    "ko": ["KO!", "LIGHTS OUT!", "DOWN 'E GOES!"],
    "combo": ["STREWTH!", "CRIKEY!", "FAIR DINKUM!"],
    "flee": ["WAAAH!", "MUUUUM!"],
}

PARTICLES = {"crow": "feather", "djiti": "feather", "butcherbird": "feather_w", "cat": "fur", "goanna": "leaf"}


def classify(zones, point, slack):
    """First zone (in priority order) that the point lands in."""
    px, py = point
    for name, (cx, cy), r in zones:
        s = min(slack, 3) if name == "eye" else slack
        if math.hypot(px - cx, py - cy) <= r + s:
            return name
    return None


def resolve(game):
    m = game.magpie
    targets = [th for th in game.threats if th.hittable]
    if m.state == "swoop":
        tip = m.tip()
        for th in targets:
            if id(th) in m.swoop_hits:
                continue
            zone = classify(th.zones(), tip, 9)
            if zone:
                m.swoop_hits.add(id(th))
                apply_hit(game, th, "swoop", zone, tip)
                m.bounce()
                break
    if m.claw_t > 0:
        c = m.claw_center()
        for th in targets:
            if id(th) in m.claw_hits:
                continue
            zone = classify(th.zones(), c, T.CLAW_RADIUS * 0.7)
            if zone:
                m.claw_hits.add(id(th))
                apply_hit(game, th, "claw", zone, c)
    if m.state == "fly" and m.peck_cd <= 0 and not m.grounded:
        tip = m.tip()
        for th in targets:
            zone = classify(th.zones(), tip, 4)
            if zone:
                m.peck_cd = T.PECK_COOLDOWN
                m.vel[0] = -m.facing * 140
                apply_hit(game, th, "peck", zone, tip)
                break


def apply_hit(game, th, kind, zone, point):
    fx, audio = game.fx, game.audio
    if kind == "swoop":
        dmg = T.DMG_SWOOP
    elif kind == "claw":
        dmg = T.DMG_CLAW_CLIMBER if th.climbs else T.DMG_CLAW
    else:
        dmg = T.DMG_PECK
    if zone == "eye":
        dmg *= T.EYE_DAMAGE_MULT
        if th.is_kid:
            dmg = max(dmg, th.hp)  # one in the eye and they're down
    elif zone == "helmet" or (zone == "head" and getattr(th, "helmet", False)):
        dmg *= T.HELMET_DAMAGE_MULT
    elif zone == "backhead":
        dmg *= T.BACKHEAD_DAMAGE_MULT

    game.combo += 1
    mult = game.combo_mult()
    pts = th.score * T.ZONE_SCORE[zone] * mult
    was_fleeing = th.state in ("flee", "flee_win")
    ko = th.take_damage(dmg, game.magpie.pos)
    game.add_score(pts, point)
    game.wave_hits += 1

    # comic word
    if zone == "eye":
        fx.text(random.choice(WORDS["eye"]), point, "big", 34)
        fx.big_hit()
        audio.play("eye")
    else:
        key = zone if zone in ("helmet", "backhead") else kind
        size = 22 if kind == "peck" else 30
        fx.text(random.choice(WORDS[key]), point, "hit", size)
        fx.shake.add(T.SHAKE_SMALL if kind != "peck" else 1.5)
        audio.play({"swoop": "bang", "claw": "claw", "peck": "peck"}[kind])

    part = PARTICLES.get(th.kind)
    if part:
        fx.burst(part, point, 7 if kind != "peck" else 3)
    if th.flies:
        audio.play("caw", 0.6)
    elif th.kind == "cat":
        audio.play("meow", 0.7)

    if th.is_kid:
        if getattr(th, "icecream", None):
            th.icecream = None
            fx.prop("icecream", (th.pos[0] + th.facing * 10, th.pos[1] - 40), (th.facing * 90, -260))
        if zone in ("head", "eye") and getattr(th, "hat", None):
            hat = th.hat
            th.hat = None
            game.steal_hat(th, hat)
        if not ko and random.random() < 0.35 and not was_fleeing:
            fx.text(random.choice(WORDS["flee"]), th.head_pos(), "plain", 20, drift=-40)
            audio.play("waah", 0.6)

    if ko:
        bonus = th.score * T.KO_BONUS_MULT * mult
        hx, hy = th.head_pos()
        fx.text(random.choice(WORDS["ko"]), (hx, hy - 34), "ko", 32, life=0.9)
        fx.big_hit()
        audio.play("ko")
        game.add_score(bonus, (hx, hy - 70), label="KO")
        game.wave_kos += 1
        if th.first_seen is not None and game.clock - th.first_seen <= T.QUICK_KO_WINDOW:
            game.add_score(T.QUICK_KO_BONUS, (hx, hy - 96), label="QUICK!")

    if game.combo >= 5 and game.combo % 5 == 0:
        m = game.magpie
        fx.text(random.choice(WORDS["combo"]), (m.pos[0], m.pos[1] - 60), "big", 30, life=0.9)
        audio.play("egg", 0.5)
