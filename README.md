# Swoopin

It's spring in an Aussie suburb, you're a magpie, and everyone is after your
eggs. Flap Flappy Bird-style around your gum tree and swoop the brats,
posties, crows, butcherbirds, Djiti Djiti (willie wagtails), cats and goannas
that come from every direction. Most attackers go down in one good hit, landing
with a comic-book **BANG!**, **CLAWED!** or **BULLSEYE!**. Kids go down with X's
for eyes.

Most kids are just walking past, terrified of you. Swooping them anyway gets
you a cheeky bonus and sends them screaming for mum. Hit too many and an
**angry dad with a shotgun** comes looking for you.

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
python -m swoopin               # --mute for no sound
python -m swoopin --fullscreen  # or --windowed; F11 / Alt+Enter toggles in game
```

Full screen is remembered between runs. The game renders at 960×540 and
scales crisply: exactly 2× at 1080p and 4× at 4K, with letterboxing on other
aspect ratios.

## Controls

| Key | Action |
|---|---|
| Space / W / Up / left-click | Flap (gravity always pulls you down) |
| S / Down / right-click | Swoop dive in the facing direction. A hit bounces you back up to chain combos |
| Shift / X | Claw: short-range slash. Does double damage to climbers on the trunk |
| A D / Left Right | Steer and turn in the air, or walk on two legs once you've landed |
| P / Esc | Pause (Q while paused quits to the title screen) |
| F1 | Debug overlay (difficulty, spawn stats) |
| F11 / Alt+Enter | Toggle fullscreen |

## Scoring

- Hits to the body score ×1, head ×2, the back of a cable-tie helmet ×3, and
  an **eye ×5**. An eye hit knocks a kid out straight away.
- Hits chained without touching the ground build a combo multiplier, up to ×5.
- You get bonus points for knockouts, for a knockout within a second of an
  attacker appearing, for nicking a kid's hat (it goes in your nest), for
  getting a stolen egg back, and for perfect waves. A perfect wave also gives
  back a lost egg.
- Swooping an innocent kid earns a **CHEEKY!** bonus but fills the
  **DAD-O-METER**. When it's full, an angry dad marches in, takes slow, visible
  aim (a dashed red line that locks just before he fires), and lets fly with a
  shotgun spread. Get out of the line, or swoop him to spoil his aim. He takes
  three hits.
- Land on the footpath (it never hurts) and you can walk around on two legs and
  peck at shins. Landing ends your combo.
- Flying too far from the nest drains your territory meter and drags you back.

## Code layout

All the art is drawn in code. The sounds are real recordings: Australian
magpies and ravens, a willie wagtail, kids, dads and a shotgun. They come from
Wikimedia Commons and Freesound under CC0 and CC BY-SA 4.0, with full credits
in [`swoopin/sounds/CREDITS.md`](swoopin/sounds/CREDITS.md).
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
  audio.py     sound playback (recordings + a few synth blips)
  sounds/      the recordings, with CREDITS.md
```
