"""Every gameplay, pacing and difficulty number in one place."""

# Screen / world
SCREEN_W, SCREEN_H = 960, 540  # the browser build widens SCREEN_W to fit wide phones (web/main.py)
WORLD_W = 1440
GROUND_Y = 478
NEST_X, NEST_Y = WORLD_W // 2, 232
TRUNK_TOP_Y = 248
FPS = 60

# Season
SEASON_LENGTH = 600.0  # 10:00, then the chicks fledge
WAVE_LENGTH = 35.0
BREATHER = 3.0
START_EGGS = 4
MAX_EGGS = 4
EGG_SURVIVAL_BONUS = 500
PERFECT_WAVE_BONUS = 250
DIFFICULTY_EXPONENT = 1.5  # ease-in curve on season progress

# Magpie flight (Flappy-style)
GRAVITY = 1250.0
FLAP_IMPULSE = -400.0
FLAP_FORWARD = 50.0
H_ACCEL = 700.0
H_DRAG = 2.2
H_MAX = 250.0
MAX_FALL = 620.0
SWOOP_VX = 470.0
SWOOP_VY = 400.0
SWOOP_TIME = 0.6
SWOOP_COOLDOWN = 0.3
SWOOP_BOUNCE = -440.0
CLAW_ACTIVE = 0.16
CLAW_COOLDOWN = 0.42
CLAW_REACH = 24
CLAW_RADIUS = 24
PECK_COOLDOWN = 0.4
POOP_COOLDOWN = 0.55
POOP_CARRY = 0.5  # fraction of the magpie's speed the poop keeps as it drops
POOP_BONUS = 25  # extra points for a direct hit from above
DMG_POOP = 0.5  # only for non-kids; kids are just grossed out and go home
STUN_TIME = 0.6
WALK_SPEED = 95.0
PERCH_HALF_WIDTH = 24  # how far either side of the nest centre the magpie can stand
PERCHED_RAID_SLOW = 0.5  # raiders right at the nest work this much slower with the magpie on it
HIT_STUN_TIME = 0.45
INVULN_TIME = 1.0

# Territory leash (ellipse around the nest)
TERRITORY_RX = 520.0
TERRITORY_RY = 380.0
TERRITORY_DRAIN = 0.4
TERRITORY_REFILL = 0.55
TERRITORY_SLOW = 0.6
TERRITORY_HEADWIND = 260.0
TERRITORY_PULL = 900.0

# Partner magpie: press Q and your mate flies in to help for a while
MATE_CALLS = 3  # per game
MATE_TIME = 10.0  # seconds she stays before heading off
MATE_SPEED = 300.0  # cruising speed while hunting
MATE_DIVE_SPEED = 520.0
MATE_DIVE_RANGE = 110  # starts a dive when this close to her target
MATE_STEER = 4.0  # how quickly she turns toward where she wants to go
MATE_HIT_COOLDOWN = 0.55
MATE_ORBIT_RX, MATE_ORBIT_RY = 150, 60  # circles the nest when there's nothing to hit

# Damage
DMG_SWOOP = 1.0
DMG_CLAW = 1.0
DMG_CLAW_CLIMBER = 2.0
DMG_PECK = 0.5
EYE_DAMAGE_MULT = 2.0
HELMET_DAMAGE_MULT = 0.5
BACKHEAD_DAMAGE_MULT = 1.5

# Score multipliers per hit zone
ZONE_SCORE = {"body": 1, "head": 2, "helmet": 1, "backhead": 3, "eye": 5}
KO_BONUS_MULT = 3
QUICK_KO_WINDOW = 1.0  # seconds after first appearing on screen
QUICK_KO_BONUS = 100
HAT_BONUS = 30
EGG_SAVED_BONUS = 150
COMBO_STEP = 3  # hits per +1 multiplier
COMBO_MAX_MULT = 5

# Threat base stats: hp, speed (px/s), score, time at nest to do damage.
# Most things go down in one good hit; posties, goannas and dads take more.
# Only multi-hit types get extra hp as the season goes on.
THREATS = {
    "kid": dict(hp=1, speed=55, score=10, attack_time=3.0),
    "bike": dict(hp=1, speed=120, score=15, attack_time=2.6),
    "postie": dict(hp=2, speed=190, score=25, attack_time=2.0),
    "crow": dict(hp=1, speed=90, score=20, attack_time=2.2),
    "butcherbird": dict(hp=1, speed=150, score=25, attack_time=1.2),
    "djiti": dict(hp=1, speed=185, score=35, attack_time=1.6),
    "cat": dict(hp=1, speed=70, score=20, attack_time=1.2),
    "goanna": dict(hp=3, speed=50, score=40, attack_time=1.3),
    "dad": dict(hp=3, speed=70, score=60, attack_time=99),
    "mum": dict(hp=2, speed=60, score=20, attack_time=99),
}

# Innocent kids just walking past: scared of the magpie, but cheeky bonus
# points if you get them anyway. Too many kids hit brings out angry dads.
INNOCENT_INTERVAL_START = 5.5
INNOCENT_INTERVAL_END = 3.2
INNOCENT_MAX = 4
INNOCENT_BIKE_CHANCE = 0.3
INNOCENT_BONUS = 50
INNOCENT_PANIC_RANGE = 160
KID_FLEE_MULT = 2.4  # kids bolt for home once they've been swooped (x their walking speed)
DAD_RAGE_THRESHOLD = 4  # kids knocked out (roughly) before a dad turns up
DAD_RAGE_DECAY = 1 / 30  # rage points forgiven per second
DAD_RAGE_BRAT = 0.3  # a nest-raiding brat only counts this much
DAD_RAGE_MUM = 1.5  # knocking out someone's mum really sets them off

# Mums: come running to a knocked-out kid, or walk along with one. Say "SHOO!"
# and swing a broom at the magpie if it comes close.
MUM_RESCUE_CHANCE = 0.4
MUM_ESCORT_CHANCE = 0.15
MUM_MAX = 2
MUM_COOLDOWN = 12.0  # seconds between mums turning up
MUM_RUN_SPEED = 200
MUM_SHOO_RANGE = 190
MUM_SHOO_COOLDOWN = 1.8
MUM_SWING_TIME = 0.45
MUM_BROOM_REACH = 50  # bristles' distance from her top hand
MUM_WHACK_RADIUS = 34
MUM_WHACK_STUN = 0.5
DAD_MAX = 2
DAD_SHOTS = 3
DAD_AIM_START = 1.7  # seconds of visible aiming before the shot
DAD_AIM_END = 1.05
DAD_LOCK = 0.35  # aim stops tracking this long before firing
DAD_PELLETS = 5
DAD_SPREAD = 0.07
DAD_PELLET_SPEED = 1000
SHOT_STUN_TIME = 1.1
CLIMB_SPEED = {"cat": 38, "goanna": 32}

# Difficulty levels, picked with the slider on the title screen.
# (name, curve scale, head start, attacker speed, time attackers need at the nest)
# The season's difficulty d (0 -> 1, below) is multiplied by the scale plus
# the head start, capped at 1: easier levels never reach the full late-season
# onslaught, harder ones get there sooner. MEDIUM is the original game.
DIFFICULTIES = [
    ("CHILL", 0.5, 0.0, 0.8, 1.6),
    ("EASY", 0.7, 0.0, 0.88, 1.3),
    ("MEDIUM", 1.0, 0.0, 1.0, 1.0),
    ("HARD", 1.25, 0.1, 1.1, 0.85),
    ("FERAL", 1.6, 0.2, 1.2, 0.7),
]
DEFAULT_DIFFICULTY = 2  # MEDIUM

# Difficulty scaling (difficulty d runs 0 -> 1 over the season)
SPEED_SCALE_MAX = 0.6  # 1.0x -> 1.6x
ATTACK_TIME_SCALE_START = 1.8  # time needed at the nest: generous early...
ATTACK_TIME_SCALE_END = 0.8  # ...ruthless late
HP_PLUS_ONE_AT = 0.5
HP_PLUS_TWO_AT = 0.85
SPAWN_INTERVAL_START = 4.6
SPAWN_INTERVAL_END = 0.95
MAX_ACTIVE_START = 3
MAX_ACTIVE_END = 13
KO_RECOVER_START = 3.0
KO_RECOVER_END = 1.1
RETURN_CHANCE_START = 0.25
RETURN_CHANCE_END = 0.8
RETURN_DELAY_START = 12.0
RETURN_DELAY_END = 3.5
DUCK_CHANCE_MAX = 0.5
DUCK_FROM = 0.3
THROW_INTERVAL_START = 4.5
THROW_INTERVAL_END = 1.6
THROW_LEAD_MAX = 1.0  # fraction of magpie velocity the kid leads by

# Phase boundaries (seconds into the season)
PHASES = [
    (0, "EARLY SEASON"),
    (90, "BUILDING"),
    (210, "PEAK SEASON"),
    (360, "LATE SEASON"),
    (510, "FINAL PUSH"),
]

# Juice
SHAKE_BIG = 7.0
SHAKE_SMALL = 3.0
HITPAUSE_BIG = 3  # frames
COMIC_TEXT_TIME = 0.65
