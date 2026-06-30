import random
from world.tile import World
from constants import *

# Named locations: (x, y, tile_id, name, type)
LOCATIONS = [
    (5,  5,  T_TOWN,    "UNDERHIVE DELTA",    "town",    "underhive"),
    (15, 8,  T_DUNGEON, "UNDERHIVE VAULTS",   "dungeon", "dungeon1"),
    (22, 12, T_TOWN,    "HIVE SPIRE OMEGA",   "town",    "spire"),
    (30, 18, T_DUNGEON, "TYRANID BURROWS",    "dungeon", "dungeon2"),
    (38, 10, T_DUNGEON, "THE IRON KEEP",      "dungeon", "dungeon3"),
    (45, 25, T_DUNGEON, "THE VOID SANCTUM",   "dungeon", "dungeon_void"),
    (50, 50, T_DUNGEON, "CITADEL OF SILENCE", "dungeon", "dungeon_final"),
    (10, 20, T_SHRINE,  "SHRINE OF SAINT LUCIUS", "shrine", None),
    (28, 28, T_SHRINE,  "RUINED SHRINE",      "shrine",  None),
]

def build_world():
    w = World(WORLD_W, WORLD_H)

    # Flood fill base terrain
    for y in range(WORLD_H):
        for x in range(WORLD_W):
            # Toxic seas on edges and certain areas
            if x < 2 or x >= WORLD_W - 2 or y < 2 or y >= WORLD_H - 2:
                w.set_tile(x, y, T_TOXIC_SEA)
            elif 18 <= x <= 24 and 20 <= y <= 30:
                # Plaguefields
                if random.random() < 0.1:
                    w.set_tile(x, y, T_RUBBLE)
                else:
                    w.set_tile(x, y, T_ASH)
            elif x > 40 or y > 40:
                # Deep wasteland
                if random.random() < 0.2:
                    w.set_tile(x, y, T_RUBBLE)
                else:
                    w.set_tile(x, y, T_WASTELAND)
            else:
                if random.random() < 0.15:
                    w.set_tile(x, y, T_ASH)
                elif random.random() < 0.05:
                    w.set_tile(x, y, T_RUBBLE)
                else:
                    w.set_tile(x, y, T_WASTELAND)

    # Roads
    _draw_road(w, 5, 5, 22, 12)
    _draw_road(w, 22, 12, 38, 10)
    _draw_road(w, 5, 5, 15, 8)
    _draw_road(w, 22, 12, 30, 18)
    _draw_road(w, 30, 18, 45, 25)
    _draw_road(w, 45, 25, 50, 50)

    # Place locations
    for lx, ly, tid, name, ltype, lid in LOCATIONS:
        w.set_tile(lx, ly, tid)
        # Clear adjacent tiles
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if w.get_tile(lx+dx, ly+dy) in (T_RUBBLE,):
                    w.set_tile(lx+dx, ly+dy, T_WASTELAND)

    # Toxic sea river
    for x in range(12, 20):
        w.set_tile(x, 15, T_TOXIC_SEA)
    for x in range(12, 14):
        w.set_tile(x, 14, T_BRIDGE)
        w.set_tile(x, 16, T_BRIDGE)

    return w, LOCATIONS

def _draw_road(w, x1, y1, x2, y2):
    x, y = x1, y1
    while x != x2 or y != y2:
        t = w.get_tile(x, y)
        if t not in (T_TOWN, T_DUNGEON, T_SHRINE, T_TOXIC_SEA):
            w.set_tile(x, y, T_ROAD)
        if x < x2:
            x += 1
        elif x > x2:
            x -= 1
        elif y < y2:
            y += 1
        elif y > y2:
            y -= 1
