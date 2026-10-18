"""Code-drawn art. Every draw_* returns (surface, anchor) facing right.

Swap any function here for a sprite loader later; callers only rely on the
(surface, anchor) contract and on the hit-zone offsets in threats.py.
"""

import math

import pygame

from . import palette as P

OUT = P.CHARCOAL


def _surf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def ocircle(s, col, c, r, w=2, out=OUT):
    pygame.draw.circle(s, col, c, r)
    pygame.draw.circle(s, out, c, r, w)


def oellipse(s, col, rect, w=2, out=OUT):
    pygame.draw.ellipse(s, col, rect)
    pygame.draw.ellipse(s, out, rect, w)


def opoly(s, col, pts, w=2, out=OUT):
    pygame.draw.polygon(s, col, pts)
    pygame.draw.polygon(s, out, pts, w)


def oline(s, col, a, b, w, out=OUT):
    pygame.draw.line(s, out, a, b, w + 3)
    pygame.draw.line(s, col, a, b, w)


def xeye(s, c, r=3, col=OUT):
    x, y = c
    pygame.draw.line(s, col, (x - r, y - r), (x + r, y + r), 2)
    pygame.draw.line(s, col, (x - r, y + r), (x + r, y - r), 2)


def xform(local, facing=1, angle=0.0):
    """Map a local offset (facing right, unrotated) to a world offset."""
    x, y = local
    x *= facing
    if angle:
        a = math.radians(angle)
        c, s = math.cos(a), math.sin(a)
        x, y = x * c + y * s, -x * s + y * c
    return x, y


def blit_actor(dst, surf, anchor, pos, facing=1, angle=0.0, alpha=255):
    ax, ay = anchor
    w, h = surf.get_size()
    if facing < 0:
        surf = pygame.transform.flip(surf, True, False)
        ax = w - ax
    if angle:
        cx, cy = w / 2, h / 2
        vx, vy = xform((ax - cx, ay - cy), 1, angle)
        surf = pygame.transform.rotate(surf, angle)
        rw, rh = surf.get_size()
        ax, ay = rw / 2 + vx, rh / 2 + vy
    if alpha < 255:
        surf.set_alpha(alpha)
    dst.blit(surf, (round(pos[0] - ax), round(pos[1] - ay)))


def stars(dst, pos, t, n=3, r=14):
    for i in range(n):
        a = t * 5 + i * math.tau / n
        x = pos[0] + math.cos(a) * r
        y = pos[1] + math.sin(a) * r * 0.4
        star(dst, (x, y), 4, P.WATTLE)


def star(dst, c, r, col):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
    pygame.draw.polygon(dst, col, pts)
    pygame.draw.polygon(dst, OUT, pts, 1)


# --------------------------------------------------------------------------
# Magpie
# --------------------------------------------------------------------------

def draw_magpie(flap, tucked=False, stunned=False, flash=False, standing=False, walk=0.0):
    s = _surf(76, 56)
    body = P.CHARCOAL
    white = P.BONE if not flash else P.WATTLE
    if standing:  # two legs, alternating stride; feet land 24px below the anchor
        tucked = True
        for hip_x, ph in ((33, 0.0), (40, math.pi)):
            fx = hip_x + math.sin(walk + ph) * 5
            lift = max(0.0, -math.cos(walk + ph)) * 3
            knee = (hip_x + (fx - hip_x) * 0.5 + 2, 43 - lift)
            pygame.draw.line(s, P.DARK_GREY, (hip_x, 36), knee, 3)
            pygame.draw.line(s, P.DARK_GREY, knee, (fx, 50 - lift), 3)
            pygame.draw.line(s, P.DARK_GREY, (fx - 3, 50 - lift), (fx + 5, 50 - lift), 2)
    # tail: white base, black tip band
    opoly(s, white, [(20, 27), (3, 22), (3, 34), (20, 32)], 2, P.DARK_GREY)
    pygame.draw.polygon(s, body, [(3, 22), (9, 23), (9, 33), (3, 34)])
    # body
    oellipse(s, body, (16, 18, 36, 22), 2, P.DARK_GREY)
    # white undertail
    pygame.draw.ellipse(s, white, (19, 30, 12, 7))
    # far wing / near wing
    sx, sy = 36, 25
    if tucked:
        wing = [(sx + 4, sy - 2), (sx - 20, sy - 4), (sx - 24, sy + 2), (sx - 2, sy + 4)]
        opoly(s, body, wing, 2, P.DARK_GREY)
        pygame.draw.polygon(s, white, [(sx + 2, sy - 1), (sx - 8, sy - 2), (sx - 6, sy + 3), (sx + 1, sy + 3)])
    else:
        lift = math.cos(flap)
        tip = (sx - 18, sy - 24 * lift)
        mid = (sx - 4, sy - 14 * lift)
        wing = [(sx + 6, sy - 1), mid, tip, (sx - 22, sy - 10 * lift + 3), (sx - 10, sy + 3)]
        opoly(s, body, wing, 2, P.DARK_GREY)
        patch = [(sx + 5, sy - 1), (sx + (mid[0] - sx) * 0.6 + 2, sy + (mid[1] - sy) * 0.6),
                 (sx - 6, sy + (mid[1] - sy) * 0.4 + 2), (sx - 4, sy + 3)]
        pygame.draw.polygon(s, white, patch)
    # head + white nape
    ocircle(s, body, (54, 21), 10, 2, P.DARK_GREY)
    pygame.draw.polygon(s, white, [(44, 15), (49, 12), (50, 28), (43, 30)])
    pygame.draw.circle(s, body, (55, 21), 8)
    # eye
    if stunned:
        xeye(s, (57, 18), 3, P.BONE)
    else:
        pygame.draw.circle(s, P.MAGPIE_EYE, (57, 18), 3)
        pygame.draw.circle(s, OUT, (57, 18), 1)
    # beak
    opoly(s, P.BEAK, [(61, 18), (74, 22), (61, 25)], 1)
    pygame.draw.polygon(s, P.DARK_GREY, [(70, 21), (74, 22), (70, 23)])
    return s, (38, 26)


# --------------------------------------------------------------------------
# Kids
# --------------------------------------------------------------------------

SHIRTS = [P.DEEP_GUM, P.WARATAH, P.DENIM, P.OCHRE]


def draw_kid(walk, shirt=P.DEEP_GUM, hat="bucket", helmet=False, ko=False,
             duck=False, scared=False, throwing=0.0, icecream=None, brat=False, bag=False):
    s = _surf(64, 84)
    fx, fy = 32, 80  # feet anchor
    dy = 10 if duck else 0
    if bag:  # school backpack, behind the body
        pygame.draw.rect(s, P.OCHRE, (fx - 17, fy - 48 + dy, 10, 16), border_radius=3)
        pygame.draw.rect(s, OUT, (fx - 17, fy - 48 + dy, 10, 16), 2, border_radius=3)
    # legs
    sw = math.sin(walk) * 6 if not duck else 0
    for side, ph in ((-3, sw), (3, -sw)):
        hip = (fx + side, fy - 24)
        foot = (fx + side + ph, fy - 3)
        if duck:
            knee = (fx + side + 8, fy - 14)
            oline(s, P.SKIN, hip, knee, 4)
            oline(s, P.SKIN, knee, foot, 4)
        else:
            oline(s, P.SKIN, hip, foot, 4)
        pygame.draw.ellipse(s, OUT, (foot[0] - 3, foot[1] - 2, 9, 5))
    # shorts
    pygame.draw.rect(s, P.DENIM, (fx - 8, fy - 32 + dy * 0.5, 16, 10), border_radius=2)
    pygame.draw.rect(s, OUT, (fx - 8, fy - 32 + dy * 0.5, 16, 10), 2, border_radius=2)
    # torso
    top = fy - 50 + dy
    pygame.draw.rect(s, shirt, (fx - 9, top, 18, 20), border_radius=4)
    pygame.draw.rect(s, OUT, (fx - 9, top, 18, 20), 2, border_radius=4)
    # arms
    sh = (fx, top + 5)
    if scared:
        flail = math.sin(walk * 2.2) * 5
        oline(s, P.SKIN, sh, (fx - 10, top - 14 + flail), 3)
        oline(s, P.SKIN, sh, (fx + 10, top - 14 - flail), 3)
    elif throwing > 0:
        a = -math.pi * 0.85 + throwing * math.pi * 0.9
        hand = (sh[0] + math.cos(a) * 16, sh[1] + math.sin(a) * 16)
        oline(s, P.SKIN, sh, hand, 3)
        oline(s, P.SKIN, sh, (fx - 6, top + 18), 3)
    else:
        oline(s, P.SKIN, sh, (fx - sw * 0.8, top + 18), 3)
        hand = (fx + 9, top + 14)
        oline(s, P.SKIN, sh, hand, 3)
        if icecream:
            opoly(s, P.TAN, [(hand[0] - 3, hand[1] - 2), (hand[0] + 4, hand[1] - 2), (hand[0] + 0.5, hand[1] + 8)], 1)
            ocircle(s, icecream, (hand[0] + 0.5, hand[1] - 5), 4, 1)
    # head
    hc = (fx, fy - 52 + dy)
    ocircle(s, P.SKIN, hc, 11)
    ex, ey = hc[0] + 5, hc[1] - 2
    if ko:
        xeye(s, (ex, ey), 3)
        pygame.draw.line(s, OUT, (hc[0] + 2, hc[1] + 6), (hc[0] + 8, hc[1] + 5), 2)
    else:
        pygame.draw.circle(s, OUT, (ex, ey), 2)
        if scared:
            pygame.draw.circle(s, OUT, (hc[0] + 6, hc[1] + 6), 3)
            pygame.draw.line(s, OUT, (ex - 3, ey - 7), (ex + 3, ey - 5), 2)
        elif brat:  # scowl + smirk
            pygame.draw.line(s, OUT, (ex - 4, ey - 6), (ex + 3, ey - 3), 2)
            pygame.draw.line(s, OUT, (hc[0] + 3, hc[1] + 6), (hc[0] + 8, hc[1] + 4), 2)
        else:
            pygame.draw.arc(s, OUT, (hc[0] + 2, hc[1] + 1, 7, 6), math.pi * 1.1, math.pi * 1.9, 2)
    # headwear
    if helmet:  # ice-cream container
        pygame.draw.rect(s, P.BONE, (hc[0] - 11, hc[1] - 16, 22, 12), border_radius=2)
        pygame.draw.rect(s, P.WARATAH, (hc[0] - 11, hc[1] - 11, 22, 3))
        pygame.draw.rect(s, OUT, (hc[0] - 11, hc[1] - 16, 22, 12), 2, border_radius=2)
        pygame.draw.line(s, OUT, (hc[0] - 13, hc[1] - 4), (hc[0] + 13, hc[1] - 4), 3)
    elif hat == "bucket":
        draw_bucket_hat(s, (hc[0], hc[1] - 8))
    elif hat == "cap":
        draw_cap(s, (hc[0], hc[1] - 8))
    else:
        pygame.draw.arc(s, P.STRIPE, (hc[0] - 11, hc[1] - 11, 22, 22), math.radians(30), math.radians(170), 5)
    return s, (fx, fy)


def draw_bucket_hat(s, c):
    x, y = c
    opoly(s, P.WATTLE, [(x - 15, y + 3), (x + 15, y + 3), (x + 10, y - 2), (x - 10, y - 2)], 2)
    oellipse(s, P.WATTLE, (x - 9, y - 9, 18, 10), 2)


def draw_cap(s, c):
    x, y = c
    oellipse(s, P.WARATAH, (x - 10, y - 6, 20, 12), 2)
    opoly(s, P.WARATAH, [(x + 6, y + 1), (x + 18, y + 3), (x + 6, y + 5)], 2)


def draw_bike_kid(walk, shirt=P.WARATAH, ko=False, scared=False, brat=False):
    s = _surf(76, 84)
    fx, fy = 38, 80
    # wheels
    for wx in (fx - 18, fx + 18):
        pygame.draw.circle(s, OUT, (wx, fy - 12), 12, 3)
        for k in range(3):
            a = walk * 1.5 + k * math.pi / 3
            pygame.draw.line(s, P.GREY, (wx - math.cos(a) * 10, fy - 12 - math.sin(a) * 10),
                             (wx + math.cos(a) * 10, fy - 12 + math.sin(a) * 10), 1)
    # frame
    for a, b in (((fx - 18, fy - 12), (fx - 2, fy - 30)), ((fx - 2, fy - 30), (fx + 12, fy - 30)),
                 ((fx + 12, fy - 30), (fx + 18, fy - 12)), ((fx - 18, fy - 12), (fx + 2, fy - 14)),
                 ((fx + 2, fy - 14), (fx + 12, fy - 30)), ((fx - 2, fy - 30), (fx + 2, fy - 14))):
        oline(s, P.WARATAH, a, b, 2)
    oline(s, OUT, (fx + 12, fy - 30), (fx + 14, fy - 38), 2)  # handlebar
    # rider leg
    ped = (fx + 2 + math.cos(walk) * 5, fy - 14 + math.sin(walk) * 5)
    oline(s, P.SKIN, (fx - 2, fy - 34), ped, 4)
    # torso leaning forward
    opoly(s, shirt, [(fx - 7, fy - 34), (fx + 3, fy - 32), (fx + 8, fy - 50), (fx - 3, fy - 52)], 2)
    oline(s, P.SKIN, (fx + 4, fy - 47), (fx + 14, fy - 38), 3)
    # head + helmet
    hc = (fx + 2, fy - 50)
    ocircle(s, P.SKIN, hc, 11)
    ex, ey = hc[0] + 5, hc[1] - 2
    if ko:
        xeye(s, (ex, ey), 3)
    else:
        pygame.draw.circle(s, OUT, (ex, ey), 2)
        if scared:
            pygame.draw.circle(s, OUT, (hc[0] + 6, hc[1] + 6), 3)
        elif brat:
            pygame.draw.line(s, OUT, (ex - 4, ey - 6), (ex + 3, ey - 3), 2)
    # helmet dome with cable ties
    dome = [(hc[0] + math.cos(math.radians(a)) * 13, hc[1] - 5 - math.sin(math.radians(a)) * 10)
            for a in range(0, 181, 15)]
    opoly(s, P.OCHRE, dome, 2)
    for k in range(5):
        a = math.radians(150 - k * 30)
        bx, by = hc[0] + math.cos(a) * 10, hc[1] - 8 - math.sin(a) * 6
        pygame.draw.line(s, OUT, (bx, by), (bx + math.cos(a) * 9, by - math.sin(a) * 9 - 3), 2)
    return s, (fx, fy)


def draw_postie(walk, ko=False):
    s = _surf(96, 92)
    fx, fy = 48, 88
    for wx in (fx - 24, fx + 24):
        ocircle(s, P.DARK_GREY, (wx, fy - 13), 13, 3)
        pygame.draw.circle(s, P.GREY, (wx, fy - 13), 5)
    # bike body
    opoly(s, P.WARATAH, [(fx - 24, fy - 22), (fx + 22, fy - 22), (fx + 26, fy - 36), (fx + 10, fy - 30),
                         (fx - 10, fy - 30), (fx - 28, fy - 32)], 2)
    # rear rack + postbag
    oellipse(s, P.OCHRE, (fx - 40, fy - 44, 22, 18), 2)
    pygame.draw.line(s, OUT, (fx - 38, fy - 36), (fx - 20, fy - 36), 2)
    oline(s, OUT, (fx + 24, fy - 34), (fx + 22, fy - 50), 2)
    # rider: hi-vis jacket
    oline(s, P.DENIM, (fx - 4, fy - 34), (fx + 10, fy - 26), 5)
    opoly(s, P.WATTLE, [(fx - 10, fy - 34), (fx + 4, fy - 34), (fx + 8, fy - 58), (fx - 6, fy - 60)], 2)
    pygame.draw.line(s, P.BONE, (fx - 8, fy - 44), (fx + 5, fy - 44), 2)
    oline(s, P.WATTLE, (fx + 4, fy - 54), (fx + 20, fy - 48), 4)
    # head + helmet
    hc = (fx + 4, fy - 68)
    ocircle(s, P.SKIN, hc, 11)
    ocircle(s, P.WARATAH, (hc[0] - 1, hc[1] - 3), 12)
    pygame.draw.rect(s, P.SKIN, (hc[0] + 1, hc[1] - 4, 11, 12))
    pygame.draw.line(s, OUT, (hc[0] + 1, hc[1] - 5), (hc[0] + 13, hc[1] - 5), 3)
    ex, ey = hc[0] + 6, hc[1]
    if ko:
        xeye(s, (ex, ey), 3)
    else:
        pygame.draw.circle(s, OUT, (ex, ey), 2)
        pygame.draw.line(s, OUT, (ex - 2, ey + 6), (ex + 4, ey + 6), 2)  # moustache
    return s, (fx, fy)


def draw_dad(walk, ko=False):
    """Big bloke: navy singlet over a beer gut, stubbies, thongs, akubra, mo."""
    s = _surf(84, 112)
    fx, fy = 42, 108
    sw = math.sin(walk) * 7
    for side, ph in ((-6, sw), (6, -sw)):
        oline(s, P.SKIN, (fx + side, fy - 34), (fx + side + ph, fy - 4), 7)
        pygame.draw.ellipse(s, P.WARATAH, (fx + side + ph - 6, fy - 5, 14, 5))  # thongs
    pygame.draw.rect(s, P.TAN, (fx - 15, fy - 46, 30, 16), border_radius=3)  # stubbies
    pygame.draw.rect(s, OUT, (fx - 15, fy - 46, 30, 16), 2, border_radius=3)
    oellipse(s, P.SKIN, (fx - 14, fy - 66, 34, 28))  # gut
    opoly(s, P.DENIM, [(fx - 15, fy - 54), (fx - 13, fy - 84), (fx + 13, fy - 84), (fx + 17, fy - 56),
                       (fx + 4, fy - 50)], 2)
    oline(s, P.SKIN, (fx + 6, fy - 80), (fx + 22, fy - 66), 6)  # arm forward to the gun
    oline(s, P.SKIN, (fx - 8, fy - 80), (fx - 14, fy - 58), 6)
    hc = (fx + 4, fy - 86)
    ocircle(s, P.SKIN, hc, 12)
    pygame.draw.circle(s, P.WARATAH, (hc[0] + 6, hc[1] + 4), 4)  # red-faced
    ex, ey = hc[0] + 5, hc[1] - 2
    if ko:
        xeye(s, (ex, ey), 3)
    else:
        pygame.draw.circle(s, OUT, (ex, ey), 2)
        pygame.draw.line(s, OUT, (ex - 5, ey - 6), (ex + 4, ey - 3), 3)  # furious brow
    pygame.draw.line(s, OUT, (hc[0] + 2, hc[1] + 7), (hc[0] + 13, hc[1] + 7), 4)  # mo
    # akubra
    opoly(s, P.FENCE, [(hc[0] - 18, hc[1] - 8), (hc[0] + 20, hc[1] - 8), (hc[0] + 14, hc[1] - 12),
                       (hc[0] - 12, hc[1] - 12)], 2)
    opoly(s, P.FENCE, [(hc[0] - 9, hc[1] - 11), (hc[0] - 7, hc[1] - 22), (hc[0] + 9, hc[1] - 22),
                       (hc[0] + 11, hc[1] - 11)], 2)
    pygame.draw.line(s, P.FENCE_SHADE, (hc[0] - 9, hc[1] - 13), (hc[0] + 11, hc[1] - 13), 3)
    return s, (fx, fy)


def draw_shotgun():
    """Pointing right; anchor at the shoulder end of the stock. Muzzle 46px out."""
    s = _surf(70, 16)
    opoly(s, P.FENCE, [(4, 6), (22, 5), (22, 11), (4, 13)], 2)  # stock
    pygame.draw.line(s, OUT, (20, 7), (62, 7), 5)  # barrel
    pygame.draw.line(s, P.DARK_GREY, (22, 6), (62, 6), 1)
    opoly(s, P.FENCE, [(34, 9), (46, 9), (46, 13), (34, 13)], 1)  # pump
    return s, (16, 8)


# --------------------------------------------------------------------------
# Birds
# --------------------------------------------------------------------------

def draw_crow(flap, ko=False, carrying=False):
    s = _surf(64, 48)
    c = (32, 24)
    opoly(s, P.CHARCOAL, [(c[0] - 12, c[1]), (c[0] - 30, c[1] - 4), (c[0] - 28, c[1] + 6)], 2, P.DARK_GREY)
    oellipse(s, P.CHARCOAL, (c[0] - 18, c[1] - 8, 32, 17), 2, P.DARK_GREY)
    lift = math.cos(flap)
    opoly(s, P.CHARCOAL, [(c[0] + 2, c[1] - 2), (c[0] - 8, c[1] - 20 * lift), (c[0] - 22, c[1] - 14 * lift),
                          (c[0] - 10, c[1] + 2)], 2, P.DARK_GREY)
    ocircle(s, P.CHARCOAL, (c[0] + 14, c[1] - 6), 8, 2, P.DARK_GREY)
    opoly(s, P.DARK_GREY, [(c[0] + 20, c[1] - 9), (c[0] + 31, c[1] - 4), (c[0] + 20, c[1] - 2)], 1)
    if ko:
        xeye(s, (c[0] + 17, c[1] - 8), 3, P.BONE)
    else:
        pygame.draw.circle(s, P.BONE, (c[0] + 17, c[1] - 8), 3)
        pygame.draw.circle(s, OUT, (c[0] + 17, c[1] - 8), 1)
    if carrying:
        oellipse(s, P.EGG, (c[0] + 22, c[1] - 6, 9, 11), 1)
    return s, c


def draw_butcherbird(flap, ko=False, carrying=False):
    s = _surf(52, 40)
    c = (26, 20)
    opoly(s, P.CHARCOAL, [(c[0] - 9, c[1]), (c[0] - 22, c[1] - 3), (c[0] - 21, c[1] + 4)], 1)
    oellipse(s, P.BONE, (c[0] - 13, c[1] - 6, 24, 13), 2)
    pygame.draw.ellipse(s, P.GREY, (c[0] - 12, c[1] - 6, 22, 7))
    lift = math.cos(flap)
    opoly(s, P.DARK_GREY, [(c[0] + 1, c[1] - 2), (c[0] - 6, c[1] - 15 * lift), (c[0] - 16, c[1] - 10 * lift),
                           (c[0] - 8, c[1] + 2)], 2)
    pygame.draw.line(s, P.BONE, (c[0] - 4, c[1] - 1), (c[0] - 10, c[1] - 6 * lift), 2)
    ocircle(s, P.CHARCOAL, (c[0] + 11, c[1] - 5), 6, 2, P.DARK_GREY)
    pygame.draw.polygon(s, P.BEAK, [(c[0] + 15, c[1] - 7), (c[0] + 24, c[1] - 5), (c[0] + 22, c[1] - 2),
                                    (c[0] + 15, c[1] - 3)])
    pygame.draw.line(s, OUT, (c[0] + 22, c[1] - 5), (c[0] + 23, c[1] - 2), 2)
    if ko:
        xeye(s, (c[0] + 13, c[1] - 6), 2, P.BONE)
    else:
        pygame.draw.circle(s, P.MAGPIE_EYE, (c[0] + 13, c[1] - 6), 2)
    if carrying:
        oellipse(s, P.EGG, (c[0] - 2, c[1] + 5, 9, 11), 1)
    return s, c


def draw_djiti(flap, wag, ko=False):
    """Djiti Djiti (willie wagtail): black back, white belly and brow, fanned wagging tail."""
    s = _surf(46, 34)
    c = (24, 17)
    # fanned tail, wagging side to side
    tw = math.sin(wag) * 7
    opoly(s, P.CHARCOAL, [(c[0] - 6, c[1]), (c[0] - 21, c[1] - 7 + tw), (c[0] - 22, c[1] + 2 + tw)], 1, P.DARK_GREY)
    oellipse(s, P.BONE, (c[0] - 9, c[1] - 4, 18, 10), 1, P.DARK_GREY)
    pygame.draw.ellipse(s, P.CHARCOAL, (c[0] - 9, c[1] - 5, 18, 6))
    lift = math.cos(flap)
    opoly(s, P.CHARCOAL, [(c[0] + 1, c[1] - 2), (c[0] - 4, c[1] - 12 * lift), (c[0] - 12, c[1] - 8 * lift),
                          (c[0] - 6, c[1] + 1)], 1, P.DARK_GREY)
    ocircle(s, P.CHARCOAL, (c[0] + 9, c[1] - 4), 5, 1, P.DARK_GREY)
    pygame.draw.line(s, P.BONE, (c[0] + 8, c[1] - 7), (c[0] + 13, c[1] - 7), 1)  # white brow
    pygame.draw.line(s, P.DARK_GREY, (c[0] + 13, c[1] - 4), (c[0] + 18, c[1] - 3), 2)
    if ko:
        xeye(s, (c[0] + 11, c[1] - 5), 2, P.BONE)
    else:
        pygame.draw.circle(s, P.BONE, (c[0] + 11, c[1] - 5), 1)
    return s, c


# --------------------------------------------------------------------------
# Climbers
# --------------------------------------------------------------------------

def draw_cat(walk, ko=False):
    s = _surf(76, 48)
    fx, fy = 36, 44
    sw = math.sin(walk) * 5
    for lx, ph in ((fx - 12, sw), (fx - 6, -sw), (fx + 10, -sw), (fx + 16, sw)):
        oline(s, P.TAN, (lx, fy - 14), (lx + ph, fy - 2), 4)
    # tail
    t = math.sin(walk * 0.5) * 4
    pygame.draw.lines(s, OUT, False, [(fx - 18, fy - 18), (fx - 28, fy - 26), (fx - 30 + t, fy - 38)], 7)
    pygame.draw.lines(s, P.TAN, False, [(fx - 18, fy - 18), (fx - 28, fy - 26), (fx - 30 + t, fy - 38)], 4)
    oellipse(s, P.TAN, (fx - 22, fy - 26, 44, 16), 2)
    for k in range(3):
        pygame.draw.line(s, P.STRIPE, (fx - 12 + k * 9, fy - 25), (fx - 14 + k * 9, fy - 15), 3)
    hc = (fx + 22, fy - 26)
    opoly(s, P.TAN, [(hc[0] - 8, hc[1] - 5), (hc[0] - 6, hc[1] - 15), (hc[0] - 1, hc[1] - 8)], 2)
    opoly(s, P.TAN, [(hc[0] + 1, hc[1] - 8), (hc[0] + 5, hc[1] - 16), (hc[0] + 8, hc[1] - 5)], 2)
    ocircle(s, P.TAN, hc, 10)
    ex, ey = hc[0] + 4, hc[1] - 2
    if ko:
        xeye(s, (ex, ey), 3)
    else:
        pygame.draw.circle(s, P.EUCALYPT, (ex, ey), 3)
        pygame.draw.line(s, OUT, (ex, ey - 2), (ex, ey + 2), 2)
    pygame.draw.circle(s, P.WARATAH, (hc[0] + 9, hc[1] + 2), 2)
    for k in (-1, 1):
        pygame.draw.line(s, OUT, (hc[0] + 8, hc[1] + 3), (hc[0] + 18, hc[1] + 3 + k * 3), 1)
    return s, (fx, fy)


def draw_goanna(walk, ko=False):
    s = _surf(120, 44)
    fx, fy = 58, 40
    sw = math.sin(walk) * 6
    for lx, ph, up in ((fx - 18, sw, 1), (fx + 16, -sw, 1)):
        oline(s, P.GOANNA, (lx, fy - 12), (lx + ph - 6, fy - 2), 5)
        oline(s, P.GOANNA, (lx, fy - 12), (lx - ph + 6, fy - 2), 5)
    # tail
    tail = [(fx - 24, fy - 18), (fx - 58, fy - 10 + sw * 0.5), (fx - 58, fy - 8 + sw * 0.5), (fx - 24, fy - 8)]
    opoly(s, P.GOANNA, tail, 2)
    oellipse(s, P.GOANNA, (fx - 30, fy - 24, 58, 18), 2)
    for k in range(6):
        pygame.draw.circle(s, P.WATTLE if k % 2 else P.BONE, (fx - 22 + k * 9, fy - 17 + (k % 2) * 4), 2)
    # head
    oellipse(s, P.GOANNA, (fx + 22, fy - 28, 34, 16), 2)
    ex, ey = fx + 40, fy - 23
    if ko:
        xeye(s, (ex, ey), 4)
    else:
        ocircle(s, P.WATTLE, (ex, ey), 4, 1)
        pygame.draw.circle(s, OUT, (ex + 1, ey), 2)
    flick = int(walk * 3) % 4 == 0
    if flick and not ko:
        pygame.draw.line(s, P.WARATAH, (fx + 55, fy - 20), (fx + 62, fy - 20), 2)
    return s, (fx, fy)


# --------------------------------------------------------------------------
# Props
# --------------------------------------------------------------------------

def draw_prop(kind, spin=0.0):
    if kind == "icecream":
        s = _surf(16, 22)
        opoly(s, P.TAN, [(3, 8), (13, 8), (8, 21)], 1)
        ocircle(s, P.WARATAH, (8, 6), 5, 1)
        return s, (8, 11)
    if kind == "hat":
        s = _surf(34, 16)
        draw_bucket_hat(s, (17, 10))
        return s, (17, 8)
    if kind == "cap":
        s = _surf(34, 16)
        draw_cap(s, (14, 10))
        return s, (17, 8)
    if kind == "letter":
        s = _surf(14, 10)
        pygame.draw.rect(s, P.BONE, (0, 0, 14, 10))
        pygame.draw.rect(s, OUT, (0, 0, 14, 10), 1)
        pygame.draw.line(s, OUT, (0, 0), (7, 5), 1)
        pygame.draw.line(s, OUT, (14, 0), (7, 5), 1)
        return s, (7, 5)
    if kind == "stick":
        s = _surf(22, 6)
        pygame.draw.line(s, P.FENCE_SHADE, (1, 3), (21, 3), 4)
        return s, (11, 3)
    if kind == "rock":
        s = _surf(10, 10)
        ocircle(s, P.GREY, (5, 5), 4, 1)
        return s, (5, 5)
    if kind == "egg":
        s = _surf(12, 14)
        oellipse(s, P.EGG, (1, 1, 10, 12), 1)
        return s, (6, 7)
    if kind == "wheel":
        s = _surf(28, 28)
        pygame.draw.circle(s, OUT, (14, 14), 12, 3)
        for k in range(3):
            a = spin + k * math.pi / 3
            pygame.draw.line(s, P.GREY, (14 - math.cos(a) * 10, 14 - math.sin(a) * 10),
                             (14 + math.cos(a) * 10, 14 + math.sin(a) * 10), 1)
        return s, (14, 14)
    if kind == "bikeframe":
        s = _surf(40, 26)
        for a, b in (((4, 22), (16, 6)), ((16, 6), (30, 6)), ((30, 6), (36, 22)), ((4, 22), (20, 20))):
            oline(s, P.WARATAH, a, b, 2)
        return s, (20, 22)
    if kind == "feather":
        s = _surf(10, 5)
        pygame.draw.ellipse(s, P.CHARCOAL, (0, 0, 10, 5))
        return s, (5, 2)
    if kind == "feather_w":
        s = _surf(10, 5)
        pygame.draw.ellipse(s, P.BONE, (0, 0, 10, 5))
        pygame.draw.ellipse(s, P.DARK_GREY, (0, 0, 10, 5), 1)
        return s, (5, 2)
    if kind == "leaf":
        s = _surf(10, 5)
        pygame.draw.ellipse(s, P.EUCALYPT, (0, 0, 10, 5))
        return s, (5, 2)
    if kind == "pellet":
        s = _surf(4, 4)
        pygame.draw.circle(s, P.CHARCOAL, (2, 2), 2)
        return s, (2, 2)
    if kind == "smoke":
        s = _surf(16, 16)
        pygame.draw.circle(s, (*P.GREY, 150), (8, 8), 7)
        return s, (8, 8)
    if kind == "fur":
        s = _surf(7, 4)
        pygame.draw.ellipse(s, P.TAN, (0, 0, 7, 4))
        return s, (3, 2)
    raise ValueError(kind)
