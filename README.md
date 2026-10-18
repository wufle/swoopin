# Swoopin

It's spring in an Aussie suburb, you're a magpie, and everyone is after your
eggs. Flap Flappy Bird-style around your gum tree and swoop the kids, posties,
crows, butcherbirds, Djiti Djiti (willie wagtails), cats and goannas that come
from every direction. Each hit lands with a comic-book **BANG!**, **CLAWED!** or
**BULLSEYE!**, and a kid hit hard enough goes down with X's for eyes.

Survive the full 10-minute swooping season (Aug → Nov) and the chicks fledge.
Lose every egg and the nest is raided.

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```sh
python -m swoopin          # add --mute for no sound
```

## Controls

| Key | Action |
|---|---|
| Space / W / Up / left-click | Flap (gravity always pulls you down) |
| S / Down / right-click | Swoop dive in the facing direction. A hit bounces you back up to chain combos |
| Shift / X | Claw: short-range slash. Does double damage to climbers on the trunk |
| A D / Left Right | Steer and turn |
| P / Esc | Pause (Q while paused quits to the title screen) |
| F1 | Debug overlay (difficulty, spawn stats) |
| F11 | Fullscreen |

## Scoring

- Hits to the body score ×1, head ×2, the back of a cable-tie helmet ×3, and
  an **eye ×5**. An eye hit knocks a kid out straight away.
- Hits chained without touching the ground build a combo multiplier, up to ×5.
- You get bonus points for knockouts, for a knockout within a second of an
  attacker appearing, for nicking a kid's hat (it goes in your nest), for
  getting a stolen egg back, and for perfect waves. A perfect wave also gives
  back a lost egg.
- Flying too far from the nest drains your territory meter and drags you back.

## Code layout

All the art and sound are generated in code, so there are no asset files.
`swoopin/tuning.py` holds every gameplay and difficulty number, and
`swoopin/palette.py` holds every colour. See `PROMPT.md` for the full design.

```
swoopin/
  main.py      game loop, scenes, game rules
  magpie.py    flappy physics, swoop/claw, territory leash
  threats.py   every attacker type, hit zones, AI
  hits.py      hit classification, damage, scoring, comic words
  spawner.py   season clock, difficulty curve, waves, directions
  fx.py        comic text bursts, particles, props, screen shake
  level.py     parallax background, gum tree, nest
  hud.py       score, eggs, territory, season calendar, edge arrows
  art.py       all sprite drawing
  audio.py     synthesised sound effects
```
