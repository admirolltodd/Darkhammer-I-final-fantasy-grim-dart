import random
from world.tile import World
from constants import *

class NPC:
    def __init__(self, name, x, y, color, dialogue, portrait="NP"):
        self.name     = name
        self.x        = x
        self.y        = y
        self.color    = color
        self.dialogue = dialogue  # list of strings (pages)
        self.portrait = portrait

TOWNS = {
    "tempestora": {
        "name": "HIVE TEMPESTORA",
        "width": 24, "height": 24,
        "buildings": [
            (2,  2,  8, 6, "STEEL LEGION ARMORY"),
            (12, 2,  8, 6, "MEDICAE STATION"),
            (2,  12, 8, 6, "COMMISSARIAT OFFICES"),
            (12, 12, 8, 6, "SHRINE OF THE EMPEROR"),
            (6,  18, 10, 4, "UNDERHIVE MARKET"),
        ],
        "shop_id": "tempestora_armory",
        "npcs": [
            NPC("STEEL LEGIONNAIRE", 4, 8, (100, 90, 70),
                ["WE'VE HELD THIS SECTOR FOR SIXTY DAYS. SIXTY DAYS WITH NO REINFORCEMENTS.",
                 "THE COMMISSAR SAYS YARRICK HIMSELF KNOWS OUR SITUATION. KNOWING AIN'T HELPING."],
                "SL"),
            NPC("COMMISSAR ADJUTANT", 3, 14, (60, 60, 80),
                ["COMMISSAR YARRICK'S ORDERS: HOLD HIVE TEMPESTORA AT ALL COSTS.",
                 "FIND WHAT'S IN THAT ENCAMPMENT. KILL IT. COME BACK. IN THAT ORDER."],
                "CA"),
            NPC("REFUGEE", 8, 20, (80, 70, 60),
                ["THE ORKS CAME THROUGH OUR SECTOR LAST NIGHT. THE THINGS WITH TOO MANY TEETHS.",
                 "MY FAMILY WAS IN THE LOWER DECKS. THEY'RE STILL THERE. PLEASE."],
                "RF"),
            NPC("TECH-ADEPT", 15, 5, (60, 100, 80),
                ["THE MANUFACTORUM MACHINE SPIRITS ARE SILENT. THAT IS WRONG. THEY SHOULD SCREAM.",
                 "THE ORKS HAVE DONE SOMETHING TERRIBLE TO THE FORGE-DISTRICT. THE OMNISSIAH WEEPS."],
                "TC"),
            NPC("FIELD APOTHECARY", 14, 8, (120, 120, 150),
                ["I CAN PATCH YOUR WOUNDS. I CANNOT PATCH THE WAAAGH!",
                 "REST HERE. THE SHRINE STILL FUNCTIONS. FOR NOW. EMPEROR WILLING."],
                "AP"),
        ],
        "has_shrine": True,
        "shrine_pos": (15, 14),
        "entry_pos": (12, 22),
    },
    "infernus": {
        "name": "HIVE INFERNUS",
        "width": 28, "height": 28,
        "buildings": [
            (2,  2,  8, 6, "MECHANICUS FORGE-SHRINE"),
            (14, 2,  10, 6, "INQUISITORIAL FIELD STATION"),
            (2,  12, 8,  6, "NOBLE QUARTER MEDICAE"),
            (14, 12, 10, 6, "ASTROPATHIC RELAY"),
            (4,  20, 18, 6, "RECLAIMED MANUFACTORY MARKET"),
        ],
        "shop_id": "infernus_forge",
        "npcs": [
            NPC("HIVE LORD STAVROS", 4, 8, (140, 120, 80),
                ["RIOTERS IN MY HIVE? THE LOWER DECKS ARE ALWAYS RESTLESS. THIS IS NOTHING NEW.",
                 "WHATEVER IS HAPPENING IN THE ASH WASTES IS NO CONCERN OF THE NOBLE HOUSES.",
                 "THE SEALS WILL HOLD. THE ORKS CANNOT BREACH HIVE INFERNUS. I AM CERTAIN."],
                "HL"),
            NPC("INQUISITORIAL ACOLYTE", 16, 5, (80, 80, 120),
                ["MY INQUISITOR WAS KILLED AT THE MANUFACTORUM BREACH. I HAVE BEEN WAITING.",
                 "GROTSNIK'S FORCES HOLD THE MANUFACTORUM. SOMETHING LARGE IS BEING BUILT THERE.",
                 "GET IN. FIND OUT WHAT IT IS. THE INQUISITION WILL WANT TO KNOW."],
                "IA"),
            NPC("DYING ASTROPATH", 16, 14, (100, 80, 140),
                ["I HAVE SEEN... IN THE WARP... THE GREAT GREEN TIDE...",
                 "GHAZGHKULL IS MORE THAN A WARLORD. HE IS A PROPHET OF THEIR GODS.",
                 "GORK AND MORK STRENGTHEN HIM. FAITH-BASED POWERS MAY NOT WOUND HIM IN HIS FINAL FORM.",
                 "THE IRON FORTRESS IS REAL. IT MOVES. IT BREATHES WITH WAAAGH! ENERGY."],
                "DA"),
            NPC("RECLAIMED TRADE FACTOR", 4, 22, (60, 60, 60),
                ["I ASK NO QUESTIONS ABOUT THE ORK WEAPONS YOU ARE CARRYING.",
                 "I SELL WHAT CANNOT BE SOLD THROUGH NORMAL CHANNELS. PAY. TAKE. GO.",
                 "ALSO: THE FUNGAL CAVES HAVE SOMETHING WORSE THAN GROTS IN THEM. YOU WILL SEE."],
                "TF"),
        ],
        "has_shrine": True,
        "shrine_pos": (20, 20),
        "entry_pos": (14, 26),
    },
}

SHOPS = {
    "tempestora_armory": {
        "name": "STEEL LEGION ARMORY",
        "items": ["stimm_injector", "sacred_ungent", "antitox_shot", "frag_grenade",
                  "autogun_reconditioned", "laspistol_kantrael", "lasgun_kantrael",
                  "chainsword", "bolt_pistol_mkiii", "flak_armour", "purity_seal",
                  "warp_dust", "incense_of_faith"],
    },
    "infernus_forge": {
        "name": "FORGE-SHRINE OF THE OMNISSIAH",
        "items": ["sacred_ungent", "combat_stims", "full_medicae", "purification_rite",
                  "gene_seed_vial", "krak_grenade",
                  "boltgun_godwyn", "plasma_gun_ryza", "melta_gun",
                  "power_sword_blessed", "power_fist", "thunder_hammer",
                  "force_staff", "eviscerator", "omnissian_axe",
                  "carapace_armour", "power_armour_corvus", "power_armour_aquila",
                  "terminator_armour", "sororitas_power_armour", "inquisitorial_storm_coat",
                  "psyker_robes", "mechanicus_robes",
                  "iron_halo", "servo_skull_targeting", "servo_skull_warding",
                  "oath_of_moment", "cogitator_implant", "null_rod",
                  "warp_dust", "incense_of_faith"],
    },
}

class Town(World):
    def __init__(self, town_id):
        cfg = TOWNS[town_id]
        super().__init__(cfg["width"], cfg["height"])
        self.name       = cfg["name"]
        self.shop_id    = cfg.get("shop_id")
        self.entry_pos  = cfg.get("entry_pos", (cfg["width"]//2, cfg["height"]-2))
        self.has_shrine = cfg.get("has_shrine", False)
        self.shrine_pos = cfg.get("shrine_pos")
        self.npcs       = cfg.get("npcs", [])
        self._build(cfg)

    def _build(self, cfg):
        # Floor
        for y in range(self.height):
            for x in range(self.width):
                self.set_tile(x, y, T_RUIN_FLOOR)
        # Walls around edges
        for x in range(self.width):
            self.set_tile(x, 0, T_WALL)
            self.set_tile(x, self.height - 1, T_WALL)
        for y in range(self.height):
            self.set_tile(0, y, T_WALL)
            self.set_tile(self.width - 1, y, T_WALL)
        # Road strip
        for x in range(1, self.width - 1):
            self.set_tile(x, self.height - 2, T_ROAD)

        # Buildings
        for bx, by, bw, bh, bname in cfg.get("buildings", []):
            for y in range(by, by + bh):
                for x in range(bx, bx + bw):
                    self.set_tile(x, y, T_WALL)
            # Door in center bottom of building
            door_x = bx + bw // 2
            self.set_tile(door_x, by + bh - 1, T_DOOR)

        # Shrine
        if self.shrine_pos:
            self.set_tile(*self.shrine_pos, T_SHRINE)

    def get_npc_at(self, x, y):
        for npc in self.npcs:
            if npc.x == x and npc.y == y:
                return npc
        return None

    def get_building_at(self, x, y):
        return None  # handled by door tiles in main game

    def is_shop_door(self, x, y):
        return self.get_tile(x, y) == T_DOOR
