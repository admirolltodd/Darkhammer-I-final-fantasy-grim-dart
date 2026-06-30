import random
from world.tile import World
from constants import *

DUNGEON_CONFIGS = {
    "dungeon1": {
        "name": "UNDERHIVE VAULTS",
        "floors": 3,
        "width": 32, "height": 32,
        "zone": ZONE_UNDERHIVE,
        "enemy_scale": 1.0,
        "key_item": "underhive_keycard",
        "boss": None,
        "intro_text": "THE VAULTS GROAN WITH THE WEIGHT OF RUIN. HERETICS LURK IN EVERY SHADOW.",
    },
    "dungeon2": {
        "name": "TYRANID BURROWS",
        "floors": 5,
        "width": 40, "height": 40,
        "zone": ZONE_BURROW,
        "enemy_scale": 1.5,
        "key_item": "synapse_disruptor",
        "boss": "broodlord_gnawfang",
        "dark_floors": [3, 4, 5],
        "intro_text": "THE TUNNELS PULSE. THE WALLS BREATHE. YOU ARE INSIDE SOMETHING ALIVE.",
    },
    "dungeon3": {
        "name": "THE IRON KEEP",
        "floors": 6,
        "width": 40, "height": 40,
        "zone": ZONE_IRON_KEEP,
        "enemy_scale": 2.0,
        "key_item": "governors_seal",
        "boss": "lord_malachar",
        "intro_text": "ONCE THIS WAS SACRED. NOW ONLY CORRUPTION REMAINS. AND SOMETHING WORSE.",
    },
    "dungeon_void": {
        "name": "THE VOID SANCTUM",
        "floors": 4,
        "width": 30, "height": 30,
        "zone": ZONE_VOID,
        "enemy_scale": 2.5,
        "key_item": None,
        "boss": "autarch_sylandris",
        "intro_text": "ALIEN GEOMETRY. IMPOSSIBLE ANGLES. THE ELDAR DEAD WATCH FROM EVERY CORNER.",
    },
    "dungeon_final": {
        "name": "CITADEL OF SILENCE",
        "floors": 7,
        "width": 48, "height": 48,
        "zone": ZONE_CITADEL,
        "enemy_scale": 3.0,
        "key_item": None,
        "boss": "daemon_prince_xerathul_p1",
        "intro_text": "THIS IS THE END. THE WARP BLEEDS THROUGH EVERY STONE. THE DAEMON PRINCE AWAITS.",
    },
}

class DungeonFloor(World):
    def __init__(self, dungeon_id, floor_num, config):
        super().__init__(config["width"], config["height"])
        self.name     = config["name"]
        self.floor    = floor_num
        self.zone     = config["zone"]
        self.scale    = config.get("enemy_scale", 1.0)
        self.is_dark  = floor_num in config.get("dark_floors", [])
        self.chests   = []
        self.doors    = []
        self.shrines  = []
        self.entrance = (2, 2)
        self.exit_pos = None
        self._generate()

    def _generate(self):
        # Fill with walls
        for y in range(self.height):
            for x in range(self.width):
                self.set_tile(x, y, T_WALL)

        # Carve rooms
        rooms = []
        for _ in range(12):
            rx = random.randint(2, self.width - 10)
            ry = random.randint(2, self.height - 10)
            rw = random.randint(4, 9)
            rh = random.randint(4, 9)
            for y in range(ry, min(ry + rh, self.height - 1)):
                for x in range(rx, min(rx + rw, self.width - 1)):
                    self.set_tile(x, y, T_RUIN_FLOOR)
            rooms.append((rx + rw//2, ry + rh//2, rw, rh))

        # Connect rooms with corridors
        random.shuffle(rooms)
        for i in range(len(rooms) - 1):
            self._carve_corridor(rooms[i][0], rooms[i][1], rooms[i+1][0], rooms[i+1][1])

        if not rooms:
            return

        # Entrance (top-left room)
        self.entrance = (rooms[0][0], rooms[0][1])
        self.set_tile(*self.entrance, T_RUIN_FLOOR)

        # Exit (bottom-right room or door)
        exit_room = rooms[-1]
        ex, ey = exit_room[0], exit_room[1]
        self.exit_pos = (ex, ey + 1)
        self.set_tile(ex, ey + 1, T_DOOR)
        self.doors.append((ex, ey + 1, "exit"))

        # Place chests
        for room in rooms[1:-1]:
            if random.random() < 0.5:
                cx = room[0] + random.randint(-1, 1)
                cy = room[1] + random.randint(-1, 1)
                if self.get_tile(cx, cy) == T_RUIN_FLOOR:
                    self.set_tile(cx, cy, T_CHEST)
                    self.chests.append((cx, cy, False))

        # Place shrine (relay point) mid-floor
        if len(rooms) > 3:
            mid = rooms[len(rooms) // 2]
            self.set_tile(mid[0], mid[1], T_SHRINE)
            self.shrines.append((mid[0], mid[1]))

    def _carve_corridor(self, x1, y1, x2, y2):
        x, y = x1, y1
        while x != x2:
            self.set_tile(x, y, T_RUIN_FLOOR)
            x += 1 if x2 > x else -1
        while y != y2:
            self.set_tile(x, y, T_RUIN_FLOOR)
            y += 1 if y2 > y else -1

    def open_chest(self, x, y):
        for i, (cx, cy, opened) in enumerate(self.chests):
            if cx == x and cy == y and not opened:
                self.chests[i] = (cx, cy, True)
                self.set_tile(x, y, T_RUIN_FLOOR)
                return True
        return False
