import pygame

# ── Screen ──────────────────────────────────────────────────────────────────
INTERNAL_W, INTERNAL_H = 256, 224
SCALE = 3
SCREEN_W, SCREEN_H = INTERNAL_W * SCALE, INTERNAL_H * SCALE
FPS = 60
TILE = 32

# ── Palette ──────────────────────────────────────────────────────────────────
C_BLACK      = (13,   2,   8)
C_DARK_GREY  = (30,  25,  32)
C_MID_GREY   = (70,  65,  75)
C_LIGHT_GREY = (130, 120, 135)
C_WHITE      = (220, 210, 225)
C_RED        = (139,   0,   0)
C_DARK_RED   = ( 80,   0,   0)
C_BRIGHT_RED = (220,  20,  20)
C_GOLD       = (184, 134,  11)
C_DARK_GOLD  = (100,  75,   5)
C_YELLOW     = (220, 200,  50)
C_GREEN      = ( 30, 100,  30)
C_DARK_GREEN = ( 10,  55,  10)
C_BLUE       = ( 20,  40, 100)
C_PURPLE     = ( 60,  10,  80)
C_WARP       = (150,  30, 180)
C_CHAOS      = (180,  10,  10)
C_NURGLE     = ( 60,  90,  10)
C_TZEENTCH   = ( 30,  80, 160)
C_STEEL      = ( 80,  85,  95)
C_RUST       = (100,  50,  20)
C_BONE       = (180, 165, 130)
C_BLOOD      = (100,   0,  10)

# ── UI Colours ────────────────────────────────────────────────────────────────
UI_BG        = C_BLACK
UI_BORDER    = C_GOLD
UI_TEXT      = C_WHITE
UI_HIGHLIGHT = C_GOLD
UI_SHADOW    = C_DARK_GREY
UI_HP_GOOD   = C_GREEN
UI_HP_MID    = C_YELLOW
UI_HP_LOW    = C_BRIGHT_RED
UI_MP_COLOR  = C_WARP
UI_CORRUPT   = C_CHAOS

# ── Font ─────────────────────────────────────────────────────────────────────
FONT_SIZE = 8
TEXT_SPEED = 30   # ms per character

# ── Game constants ────────────────────────────────────────────────────────────
MAX_PARTY    = 4
MAX_ITEMS    = 99
MAX_LEVEL    = 30
BASE_XP      = 100
MAX_CORRUPTION = 100
MAX_MORALE   = 10
START_MORALE = 5

# ── Map ───────────────────────────────────────────────────────────────────────
WORLD_W = 64   # tiles wide
WORLD_H = 64   # tiles tall

# Tile type IDs
T_WASTELAND  = 0
T_ASH        = 1
T_RUBBLE     = 2
T_ROAD       = 3
T_TOXIC_SEA  = 4
T_RUIN_FLOOR = 5
T_DUNGEON    = 6
T_TOWN       = 7
T_WALL       = 8
T_DOOR       = 9
T_CHEST      = 10
T_SHRINE     = 11
T_BRIDGE     = 12
T_GRASS      = 13
T_WATER      = 14
T_ROCK       = 15
T_CEMENT     = 16
T_STAIRS     = 17

IMPASSABLE_TILES = {T_TOXIC_SEA, T_RUBBLE, T_WALL, T_WATER, T_ROCK}

ENCOUNTER_RATES = {
    T_WASTELAND: 12,
    T_ASH:       16,
    T_ROAD:       0,
    T_RUIN_FLOOR: 4,
    T_DUNGEON:    4,
    T_GRASS:      8,
    T_CEMENT:     6,
}

# ── Directions ────────────────────────────────────────────────────────────────
DIR_UP    = (0, -1)
DIR_DOWN  = (0,  1)
DIR_LEFT  = (-1, 0)
DIR_RIGHT = (1,  0)

# ── Status effects ────────────────────────────────────────────────────────────
STATUS_NONE        = 0
STATUS_PLAGUE      = 1   # Poison
STATUS_PSY_STATIC  = 2   # Blind
STATUS_CATATONIC   = 3   # Sleep
STATUS_SYNLOCK     = 4   # Paralysis
STATUS_WARP_MAD    = 5   # Confusion
STATUS_BLOOD_RAGE  = 6   # Berserk
STATUS_VAPORIZED   = 7   # Instant kill
STATUS_CRYSTAL     = 8   # Petrify
STATUS_VOX_JAMMED  = 9   # Silence
STATUS_ROUT        = 10  # Panic

STATUS_NAMES = {
    STATUS_PLAGUE:     "PLAGUE-TOUCHED",
    STATUS_PSY_STATIC: "PSYCHIC STATIC",
    STATUS_CATATONIC:  "CATATONIC SHOCK",
    STATUS_SYNLOCK:    "SYNAPTIC LOCK",
    STATUS_WARP_MAD:   "WARP MADNESS",
    STATUS_BLOOD_RAGE: "BLOOD RAGE",
    STATUS_VAPORIZED:  "VAPORIZED",
    STATUS_CRYSTAL:    "CRYSTALLIZED",
    STATUS_VOX_JAMMED: "VOX-JAMMED",
    STATUS_ROUT:       "ROUT",
}

STATUS_COLORS = {
    STATUS_PLAGUE:     C_NURGLE,
    STATUS_PSY_STATIC: C_TZEENTCH,
    STATUS_CATATONIC:  C_BLUE,
    STATUS_SYNLOCK:    C_MID_GREY,
    STATUS_WARP_MAD:   C_WARP,
    STATUS_BLOOD_RAGE: C_BRIGHT_RED,
    STATUS_VAPORIZED:  C_YELLOW,
    STATUS_CRYSTAL:    C_LIGHT_GREY,
    STATUS_VOX_JAMMED: C_STEEL,
    STATUS_ROUT:       C_DARK_RED,
}

# ── Class IDs ─────────────────────────────────────────────────────────────────
CLASS_ASTARTES     = 0
CLASS_INQUISITOR   = 1
CLASS_PSYKER       = 2
CLASS_SISTER       = 3
CLASS_TECH_PRIEST  = 4
CLASS_COMMISSAR    = 5

CLASS_NAMES = {
    CLASS_ASTARTES:    "ASTARTES",
    CLASS_INQUISITOR:  "INQUISITOR",
    CLASS_PSYKER:      "PSYKER",
    CLASS_SISTER:      "SISTER",
    CLASS_TECH_PRIEST: "TECH-PRIEST",
    CLASS_COMMISSAR:   "COMMISSAR",
}

CLASS_PROMOTED_NAMES = {
    CLASS_ASTARTES:    "CHAPTER CHAMPION",
    CLASS_INQUISITOR:  "LORD INQUISITOR",
    CLASS_PSYKER:      "PRIMARIS PSYKER",
    CLASS_SISTER:      "CANONESS",
    CLASS_TECH_PRIEST: "MAGOS DOMINUS",
    CLASS_COMMISSAR:   "LORD COMMISSAR",
}

PROMOTION_LEVEL = 12

# ── Ability resource types ────────────────────────────────────────────────────
RES_NONE       = 0
RES_WARP       = 1   # Psyker
RES_FAITH      = 2   # Sister
RES_COOLDOWN   = 3   # Passive/limited use

# ── Equip slots ───────────────────────────────────────────────────────────────
SLOT_HELM      = "HELM"
SLOT_BODY      = "BODY"
SLOT_MAIN      = "MAIN"
SLOT_OFF       = "OFF"
SLOT_RELIC     = "RELIC"
ALL_SLOTS      = [SLOT_HELM, SLOT_BODY, SLOT_MAIN, SLOT_OFF, SLOT_RELIC]

# ── Item types ────────────────────────────────────────────────────────────────
ITEM_CONSUMABLE = "CONSUMABLE"
ITEM_WEAPON     = "WEAPON"
ITEM_HELM       = "HELM"
ITEM_BODY       = "BODY"
ITEM_OFF        = "OFF"
ITEM_RELIC      = "RELIC"
ITEM_KEY        = "KEY"

# ── Weapon damage types ───────────────────────────────────────────────────────
DMG_PHYSICAL = "PHYSICAL"
DMG_FIRE     = "FIRE"
DMG_HOLY     = "HOLY"
DMG_WARP     = "WARP"
DMG_SONIC    = "SONIC"

# ── Enemy AI types ────────────────────────────────────────────────────────────
AI_AGGRESSIVE = "AGGRESSIVE"
AI_CUNNING    = "CUNNING"
AI_RANDOM     = "RANDOM"
AI_TACTICIAN  = "TACTICIAN"
AI_BERSERK    = "BERSERK"

# ── Zone encounter tables ─────────────────────────────────────────────────────
ZONE_ASH_WASTES    = "ash_wastes"
ZONE_ENCAMPMENT    = "encampment"
ZONE_FUNGAL_CAVES  = "fungal_caves"
ZONE_MANUFACTORUM  = "manufactorum"
ZONE_IRON_FORTRESS = "iron_fortress"
ZONE_ROK           = "rok"

# ── Story flags ───────────────────────────────────────────────────────────────
FLAG_INTRO_DONE         = "intro_done"
FLAG_ENCAMPMENT_CLEAR   = "encampment_clear"
FLAG_CAVES_CLEAR        = "caves_clear"
FLAG_MANUFACTORUM_CLEAR = "manufactorum_clear"
FLAG_MIDPOINT_SEEN      = "midpoint_seen"
FLAG_ROK_CLEAR          = "rok_clear"
FLAG_FINAL_DONE         = "final_done"
FLAG_GHAZ_SPEECH        = "ghaz_speech_seen"
FLAG_REFUGEE_REWARD     = "refugee_reward"
