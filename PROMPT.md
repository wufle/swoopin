# Swoopin — Game Build Prompt

## Concept

Build **Swoopin**, a 2D arcade game with Flappy Bird-style flight. The player
is an Australian magpie during swooping season. The magpie's job is to
**protect its nest** in a gum tree. It scores points by swooping kids who
wander too close and by fighting off animals that come after the eggs.
Attackers come from **every direction**, so the magpie can never stray far
from home. The tone is cartoon comedy with a bit of violence: kids who get
swooped hard enough fall flat on the ground with **X's for eyes**, hats and
ice creams go flying, and every hit gets a comic-book sound effect.

## Tech

- Python 3 + `pygame-ce`, with the same layout as my other projects
  (`swoopin/` package, `main.py` entry point, `requirements.txt`, `.venv`).
- **Draw all art in code** (shapes, polygons, gradients) so the game runs with
  no external image files. Keep the drawing code in its own module so real
  sprites can replace it later.
- Fixed internal resolution (e.g. 960×540) scaled to the window, 60 FPS,
  movement based on delta time.
- Generate sound effects in code as well (e.g. with `numpy`), or leave stub
  hooks for them. The game must still run with no audio device.

## Flight and controls (Flappy-style)

- **Gravity always pulls the magpie down.** **Space / Up / W / left-click**
  gives one flap, an upward impulse with a little forward push. The player
  has to keep tapping to stay in the air.
- **Left / Right (A / D)** changes facing and adds some horizontal drift.
  Horizontal speed is limited, and the magpie doesn't hover in place.
- **Swoop:** **Down / S** while in the air tucks the wings for a fast dive in
  the facing direction. A swoop that connects bounces the magpie back up a
  little, so the player can chain hits Flappy-style.
- **Claw:** **Shift / X** gives a short-range slash with a brief cooldown. It's
  the move for knocking cats and goannas off the trunk.
- Hitting the ground or a fence makes the magpie stumble: a short stun and a
  combo reset. It doesn't die, but threats keep coming while it recovers.
- **Esc / P**: pause.

## Territory: stay near the nest

- The nest sits in a gum tree at the **centre of the play area**. The world
  is only a little wider than the screen, about 1.5 screens. The camera
  follows the magpie gently but stays centred on the nest, so the nest is
  always on screen or just off it with an arrow pointing to it.
- A **territory ring** (a faint dashed circle or the shadow of the tree's
  canopy) marks the safe range. Flying outside it:
  - drains a "territory" meter on the HUD, and
  - makes the magpie fly slower, as if pushing into a headwind.
  When the meter empties, the magpie is pulled back toward the nest.
- An off-screen threat shows up as an **edge-of-screen warning arrow**
  coloured by type, so the player knows where to head.

## Core loop

1. Threats come in waves from **every direction**:
   - **Left and right**: kids, bikes and posties along the footpath and road.
   - **Above**: crows and butcherbirds diving in from the sky.
   - **Below**: cats and goannas climbing up the trunk.
   - **Behind**: later waves add threats from both sides at once and from
     diagonal flight paths.
2. The magpie swoops or claws a threat to drive it off. Each hit knocks the
   threat back. A threat that takes enough hits is **knocked out**: kids
   collapse flat with X-eyes and stars circling their heads, birds tumble out
   of the sky, and cats fall off the trunk. Knocked-out threats lie there for
   a moment, then get up and slink off-screen.
3. A threat that reaches the nest damages it, shown as a cracked or stolen
   egg. The game ends when every egg is gone.
4. Each wave ends with a short score tally, then the next wave is harder.
   See **Pacing and difficulty** below.

## Pacing and difficulty

**Target session length:** an average player loses at around **3–5 minutes**,
and a really good player can last up to **10 minutes**. At **10:00** swooping
season ends: the chicks fledge, and the player gets a victory screen ("SEASON
SURVIVED!") with a score bonus for every egg still in the nest. No run lasts
longer than 10 minutes.

- **Waves:** each wave lasts about **30–40 s** with a 3 s breather and tally in
  between, giving roughly 15–18 waves over 10 minutes. A season clock on the
  HUD counts up toward 10:00, drawn as a calendar going from Aug to Nov.
- **Eggs:** start with **4 eggs**. A perfect wave (no egg lost) restores one
  egg, up to 4, so a skilled player can recover from mistakes.
- **Difficulty rises gradually and continuously.** Scale everything from one
  `difficulty` value (0.0 → 1.0 over 10 minutes, on a gentle ease-in curve),
  never with sudden jumps. All tuning numbers go in one `tuning.py`.

Attackers get **stronger and smarter in their attempts** as the season goes
on:

| Phase | Time | What changes |
|---|---|---|
| Early season | 0:00–1:30 | One direction at a time, slow walkers, lone crows. Teaches flap, swoop and claw |
| Building | 1:30–3:30 | Two directions at once. Kids start throwing sticks. Cats join in. Bikes appear |
| Peak season | 3:30–6:00 | Three or four directions. Kids wear **ice-cream-container helmets** (take less damage on the head, but eye hits still count), wave sticks overhead, and throw rocks with better aim. Crows come in **pairs**, with one acting as a decoy. Butcherbirds steal eggs |
| Late season | 6:00–8:30 | Posties, groups of kids that scatter and regroup, cats that wait until the magpie is on the far side, and the first goanna |
| Final push | 8:30–10:00 | Everything mixed and coordinated. A **crow gang** of 3–4 attacks from different angles, goannas climb while kids come from both sides, and attackers recover from a KO faster |

Each attacker type has its own scaling as `difficulty` rises:
- **Health:** more hits needed to KO, roughly +1 hit at the midpoint and +2 near the end.
- **Speed:** about 1.0× at the start, rising to about 1.6× by the end.
- **Spawn rate and group size:** both rise gradually.
- **Smarts:** dodging swoops (a kid ducks if the magpie dives in a straight
  line), better-aimed projectiles, and approaching from the side the magpie
  isn't facing.
- **Persistence:** chased-off attackers come back sooner, and knocked-out ones
  get up faster.

**Tuning goal:** a player who never claws and only swoops should lose around
the 3:00 mark. Someone who uses all their moves well and keeps combos going
should get to 7–9 minutes. Reaching 10:00 should feel earned. Add a debug key
(F1) that shows the current `difficulty` value and spawn stats to help with
tuning.

## Threats

| Threat | Comes from | Behaviour | Notes |
|---|---|---|---|
| Kid on foot | Left/right | Walks toward the tree, throws sticks or rocks up at the magpie | 2 hits to KO: falls flat, X-eyes, drops an ice cream |
| Kid on a bike | Left/right | Fast, wears a helmet with cable ties sticking up | Hitting the helmet scores less, hitting the back of the head scores more. On KO, the bike crashes and the wheel keeps spinning |
| Postie on a motorbike | Left/right | Fast and tough | 4 hits. Letters spray everywhere on KO |
| Crow / raven | Above / diagonal | Dives at the nest and fights in the air | Has an eye zone |
| Butcherbird | Above | Small, quick, grabs an egg and runs | Chase it down to get the egg back |
| Djiti Djiti (willie wagtail; Noongar name) | Above / sides | Tiny, fast, erratic. Fearlessly mobs the magpie with chattering pecks, then dives on the nest if left alone | Very hard to hit, worth 35. Appears from about 2:30 |
| Cat | Below (trunk) | Climbs the trunk | Must be clawed off before it reaches the nest |
| Goanna | Below (trunk) | Slow, tough, climbs | Boss-style threat in later waves, with a big eye zone |

## Hits and scoring

- Each threat has **hit zones**: body, head, and a small **eye zone**. Every
  threat has one, kids included.
- Body hit gives the base score, head hit ×2, and a **direct hit to the eye**
  ×5 plus a big "BULLSEYE!" burst. An eye hit on a kid knocks them out
  instantly with X-eyes.
- **Knockout bonus** when a threat is KO'd rather than just chased off.
- **Combo multiplier** for hits chained without touching the ground, shown on
  the HUD. The bounce after a swoop is what makes chains possible.
- Bonuses for a KO within a second of a threat appearing, a perfect wave with
  no lost eggs, getting a stolen egg back, and stealing a kid's hat (it lands
  in the nest as a trophy).

## Comic hit text

- Every hit spawns **comic-book onomatopoeia** at the point of impact, with
  bold outlined lettering inside a jagged starburst. The text pops in at a
  slightly larger size, wobbles, then fades out over about 0.6 s.
- The word depends on the kind of hit:
  - Swoop: **BANG!**, **SWOOP!**, **WHACK!**, **THWACK!**
  - Claw: **CLAWED!**, **SCRATCH!**, **SNIP!**
  - Peck: **PECK!**, **BONK!**
  - Eye: **BULLSEYE!**, **RIGHT IN THE EYE!**
  - Combos: **STREWTH!**, **CRIKEY!**, **FAIR DINKUM!**
  - Kid flees: **WAAAH!**, **MUUUUM!**
  - Knockout: **KO!**, **LIGHTS OUT!**, **DOWN 'E GOES!**
- Add a little screen shake and a 2–3 frame hit-pause on big hits.
- Feathers, leaves and dropped items burst out as particles.

## Art direction: Australiana palette

Use a warm, sun-bleached Australian suburban and bush setting. Keep the colours
to this palette so everything looks consistent:

| Role | Colour | Hex |
|---|---|---|
| Sky (top) | Hot pale blue | `#8EC9E8` |
| Sky (horizon) | Dusty haze | `#F2D9A6` |
| Red earth / dirt | Outback red | `#B5452B` |
| Ochre ground | Ochre | `#CC7A2E` |
| Gum leaves | Eucalyptus green | `#6B8F71` |
| Dark foliage | Deep gum | `#3E5641` |
| Gum bark | Ghost-gum white | `#E9E4D8` |
| Wattle highlights | Wattle yellow | `#F4C430` |
| Accent | Waratah red | `#C8102E` |
| Outlines / magpie black | Charcoal | `#1E1E1E` |
| Magpie white | Bone white | `#F7F5EF` |
| Comic text fill | Wattle yellow + Waratah red outline + Charcoal shadow | |

- Background layers with parallax: far blue ranges, mid gum trees and a
  Hills Hoist, front footpath, fence palings, letterboxes, a "SWOOPING BIRD
  AHEAD" council sign.
- Chunky cartoon shapes with thick charcoal outlines.
- The magpie has a recognisable black-and-white pattern, a red-brown eye and
  a pale blue-grey beak.

## Juice and feel

- The magpie carolling plays when the game starts and when a wave is cleared.
- Wing-flap animation, plus a speed-line trail while swooping.
- Kids run off with their arms flailing above their heads. Knocked-out kids
  lie flat with X-eyes and little stars or birds circling their heads.
- Ice creams, hats and sticks get dropped and bounce around as physics props.

## HUD and screens

- HUD: score, combo multiplier, eggs left, wave number, territory meter,
  plus edge-of-screen arrows for off-screen threats.
- Title screen with "SWOOPIN" in comic lettering over the gum tree, then
  "Press Space".
- Game over screen with the final score, time survived, and eggs saved.
- Victory screen at 10:00 ("SEASON SURVIVED!") with the egg bonus.
- A local high score saved to a JSON
  file under `~/.local/share/swoopin/`.

## Code structure

```
swoopin/
  main.py          # entry, game loop, scene manager
  palette.py       # all colours above, nowhere else
  magpie.py        # flappy physics, swoop/claw states, territory leash
  threats.py       # threat base class + each type
  hits.py          # hit zones, collision, scoring
  fx.py            # comic text bursts, particles, screen shake
  level.py         # parallax background, tree, nest
  hud.py           # score, eggs, territory meter, edge arrows, season clock
  tuning.py        # every difficulty/pacing number in one place
  spawner.py       # waves, difficulty curve, directional spawn patterns
  audio.py
```

## Done when

- `python -m swoopin` starts a game that can be played from the title screen
  through game over.
- Flappy-style flight feels good: tap to flap, dive to swoop, bounce on a hit.
- Threats come from left, right, above and below, and the territory leash works.
- A full season runs 10:00 with a gradual difficulty ramp and the victory
  screen. An average run ends in 3–5 minutes.
- At least 4 threat types, eye-hit bonuses, and X-eyed KOs working.
- Comic text shows up on every hit, and the word fits the kind of hit.
- All colours come from `palette.py`.
- No external image files are needed.
