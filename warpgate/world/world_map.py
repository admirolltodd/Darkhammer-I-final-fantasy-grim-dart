import random
from world.tile import World
from constants import *

# Named locations on Armageddon: (x, y, tile_id, name, type, id)
LOCATIONS = [
    (5,  5,  T_TOWN,    "HIVE TEMPESTORA",            "town",    "tempestora"),
    (15, 8,  T_DUNGEON, "ORK ENCAMPMENT ALPHA",       "dungeon", "dungeon1"),
    (22, 12, T_TOWN,    "HIVE INFERNUS",              "town",    "infernus"),
    (30, 18, T_DUNGEON, "FUNGAL CAVES",               "dungeon", "dungeon2"),
    (38, 10, T_DUNGEON, "CAPTURED MANUFACTORUM",      "dungeon", "dungeon3"),
    (45, 25, T_DUNGEON, "ORK ROK CRASHSITE",          "dungeon", "dungeon_void"),
    (50, 50, T_DUNGEON, "GHAZGHKULL'S IRON FORTRESS", "dungeon", "dungeon_final"),
    (10, 20, T_SHRINE,  "SHRINE OF THE ARCHANGEL",    "shrine",  None),
    (28, 28, T_SHRINE,  "STEEL LEGION MEMORIAL",      "shrine",  None),
]

def build_world():
    w = World(WORLD_W, WORLD_H)

    # Flood fill base terrain — Armageddon's volcanic ash wastes
    for y in range(WORLD_H):
        for x in range(WORLD_W):
            if x < 2 or x >= WORLD_W - 2 or y < 2 or y >= WORLD_H - 2:
                w.set_tile(x, y, T_TOXIC_SEA)
            elif 18 <= x <= 24 and 20 <= y <= 30:
                # Fungal cave region — ash and rubble
                if random.random() < 0.15:
                    w.set_tile(x, y, T_RUBBLE)
                else:
                    w.set_tile(x, y, T_ASH)
            elif x > 40 or y > 40:
                # Deep ash wastes toward Iron Fortress
                if random.random() < 0.25:
                    w.set_tile(x, y, T_RUBBLE)
                else:
                    w.set_tile(x, y, T_ASH)
            else:
                if random.random() < 0.20:
                    w.set_tile(x, y, T_ASH)
                elif random.random() < 0.08:
                    w.set_tile(x, y, T_RUBBLE)
                else:
                    w.set_tile(x, y, T_WASTELAND)

    # Roads between hive cities and key locations
    _draw_road(w, 5, 5, 22, 12)      # Tempestora to Infernus
    _draw_road(w, 5, 5, 15, 8)       # Tempestora to Encampment Alpha
    _draw_road(w, 22, 12, 30, 18)    # Infernus to Fungal Caves
    _draw_road(w, 22, 12, 38, 10)    # Infernus to Manufactorum
    _draw_road(w, 38, 10, 45, 25)    # Manufactorum to Rok Crashsite
    _draw_road(w, 45, 25, 50, 50)    # Rok to Iron Fortress

    # Place named locations
    for lx, ly, tid, name, ltype, lid in LOCATIONS:
        w.set_tile(lx, ly, tid)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if w.get_tile(lx+dx, ly+dy) in (T_RUBBLE,):
                    w.set_tile(lx+dx, ly+dy, T_WASTELAND)

    # Volcanic river — impassable lava flows, bridged at crossing points
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
