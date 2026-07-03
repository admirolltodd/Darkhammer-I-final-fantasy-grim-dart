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


def _make_noise(w, h, cell, rng):
    """Smooth value noise: random lattice + smoothstep bilinear interpolation."""
    gw, gh = w // cell + 3, h // cell + 3
    grid = [[rng.random() for _ in range(gw)] for _ in range(gh)]

    def sample(x, y):
        fx, fy = x / cell, y / cell
        x0, y0 = int(fx), int(fy)
        tx, ty = fx - x0, fy - y0
        tx = tx * tx * (3 - 2 * tx)
        ty = ty * ty * (3 - 2 * ty)
        a = grid[y0][x0] * (1 - tx) + grid[y0][x0 + 1] * tx
        b = grid[y0 + 1][x0] * (1 - tx) + grid[y0 + 1][x0 + 1] * tx
        return a * (1 - ty) + b * ty

    return sample


def build_world():
    w = World(WORLD_W, WORLD_H)
    rng = random.Random()

    # Two noise fields: elevation shapes ridges and toxic pools,
    # detail scatters surface variety inside each biome.
    elev   = _make_noise(WORLD_W, WORLD_H, 9, rng)
    detail = _make_noise(WORLD_W, WORLD_H, 4, rng)

    for y in range(WORLD_H):
        for x in range(WORLD_W):
            # Toxic sea rim around the map edge, wider where elevation dips
            edge = min(x, y, WORLD_W - 1 - x, WORLD_H - 1 - y)
            e = elev(x, y)
            d = detail(x, y)

            if edge < 2 or (edge < 5 and e < 0.30):
                w.set_tile(x, y, T_TOXIC_SEA)
                continue

            # Rocky ridge lines from high elevation — natural barriers
            if e > 0.82:
                w.set_tile(x, y, T_ROCK)
                continue
            if e > 0.74:
                w.set_tile(x, y, T_RUBBLE)
                continue
            # Inland toxic pools in deep basins
            if e < 0.14:
                w.set_tile(x, y, T_TOXIC_SEA)
                continue

            if 18 <= x <= 24 and 20 <= y <= 30:
                # Fungal cave region — strange growth creeping over the ash
                if d > 0.60:
                    w.set_tile(x, y, T_GRASS)
                elif d < 0.25:
                    w.set_tile(x, y, T_RUBBLE)
                else:
                    w.set_tile(x, y, T_ASH)
            elif x > 40 or y > 40:
                # Deep wastes toward the Iron Fortress — shattered, industrial
                if d > 0.72:
                    w.set_tile(x, y, T_CEMENT)
                elif d < 0.22:
                    w.set_tile(x, y, T_RUBBLE)
                elif e > 0.60:
                    w.set_tile(x, y, T_ROCK)
                else:
                    w.set_tile(x, y, T_ASH)
            else:
                # Central ash wastes — banded by elevation
                if e > 0.55:
                    w.set_tile(x, y, T_WASTELAND)
                elif d > 0.80:
                    w.set_tile(x, y, T_RUBBLE)
                else:
                    w.set_tile(x, y, T_ASH)

    # Roads between hive cities and key locations
    _draw_road(w, 5, 5, 22, 12)      # Tempestora to Infernus
    _draw_road(w, 5, 5, 15, 8)       # Tempestora to Encampment Alpha
    _draw_road(w, 22, 12, 30, 18)    # Infernus to Fungal Caves
    _draw_road(w, 22, 12, 38, 10)    # Infernus to Manufactorum
    _draw_road(w, 38, 10, 45, 25)    # Manufactorum to Rok Crashsite
    _draw_road(w, 45, 25, 50, 50)    # Rok to Iron Fortress

    # Place named locations, clear blockers from their doorsteps
    for lx, ly, tid, name, ltype, lid in LOCATIONS:
        w.set_tile(lx, ly, tid)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if w.get_tile(lx + dx, ly + dy) in (T_RUBBLE, T_ROCK, T_TOXIC_SEA, T_WATER):
                    w.set_tile(lx + dx, ly + dy, T_WASTELAND)

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
        if t == T_TOXIC_SEA:
            # Roads bridge toxic pools so key routes always stay passable
            w.set_tile(x, y, T_BRIDGE)
        elif t not in (T_TOWN, T_DUNGEON, T_SHRINE):
            w.set_tile(x, y, T_ROAD)
        if x < x2:
            x += 1
        elif x > x2:
            x -= 1
        elif y < y2:
            y += 1
        elif y > y2:
            y -= 1
