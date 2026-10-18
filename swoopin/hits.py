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
    if m.state == "fly" and m.peck_cd <= 0:
        tip = m.tip()
        for th in targets:
            zone = classify(th.zones(), tip, 4)
            if zone:
                m.peck_cd = T.PECK_COOLDOWN
                if not m.grounded:
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
    game.wave_hits += 1

    # One burst per hit, placed on the victim (fx keeps it off the magpie).
    hx, hy = th.head_pos()
    mx = game.magpie.pos[0]
    spot = (hx + (40 if hx >= mx else -40), hy - 26)
    if zone == "eye":
        fx.text(random.choice(WORDS["eye"]), spot, "big", 30)
        fx.big_hit()
        audio.play("eye")
    else:
        if ko and T.THREATS[th.kind]["hp"] > 1:
            word, style = random.choice(WORDS["ko"]), "ko"  # finally dropped a tough one
        else:
            word, style = random.choice(WORDS[zone if zone in ("helmet", "backhead") else kind]), "hit"
        fx.text(word, spot, style, 22 if kind == "peck" else 27)
        fx.shake.add(T.SHAKE_SMALL if kind != "peck" else 1.5)
        audio.play({"swoop": "bang", "claw": "claw", "peck": "peck"}[kind])

    part = PARTICLES.get(th.kind)
    if part:
        fx.burst(part, point, 7 if kind != "peck" else 3)
    if th.kind == "djiti":
        audio.play("chatter", 0.8)
    elif th.flies:
        audio.play("caw", 0.7, min_gap=0.4)
    elif th.kind == "cat":
        audio.play("meow", 0.7)
    elif th.kind == "dad":
        audio.play("yell", 0.9, min_gap=0.6)

    label = None
    if th.is_kid:
        if getattr(th, "icecream", None):
            th.icecream = None
            fx.prop("icecream", (th.pos[0] + th.facing * 10, th.pos[1] - 40), (th.facing * 90, -260))
        if zone in ("head", "eye") and getattr(th, "hat", None):
            hat = th.hat
            th.hat = None
            game.steal_hat(th, hat)
        if not was_fleeing:
            if th.innocent:  # scared stiff, and now screaming for mum
                audio.play("mum", 1.0, min_gap=0.5)
                fx.text("MUUUUM!", (hx, hy - 4), "plain", 18, drift=-45)
                pts += T.INNOCENT_BONUS * mult
                label = "CHEEKY!"
            else:
                audio.play("waah", 0.8, min_gap=0.5)

    if ko:
        fx.big_hit()
        audio.play("ko", 0.6)
        pts += th.score * T.KO_BONUS_MULT * mult
        game.wave_kos += 1
        if th.is_kid:
            game.kid_hit(th)
        if th.first_seen is not None and game.clock - th.first_seen <= T.QUICK_KO_WINDOW and not th.innocent:
            pts += T.QUICK_KO_BONUS
            label = label or "QUICK!"
    game.add_score(pts, (spot[0], spot[1] - 30), label=label)

    if game.combo >= 5 and game.combo % 5 == 0:
        # shout it up by the combo counter, not over the action
        fx.text(random.choice(WORDS["combo"]), (game.cam[0] + 170, game.cam[1] + 100), "big", 24, life=0.9,
                drift=0)
        audio.play("chortle", 0.8)
