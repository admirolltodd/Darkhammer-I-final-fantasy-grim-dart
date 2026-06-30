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
    "underhive": {
        "name": "UNDERHIVE DELTA",
        "width": 24, "height": 24,
        "buildings": [
            (2,  2,  8, 6, "ARMORY"),
            (12, 2,  8, 6, "APOTHECARION"),
            (2,  12, 8, 6, "ARBITES PRECINCT"),
            (12, 12, 8, 6, "IMPERIAL SHRINE"),
            (6,  18, 10, 4, "UNDERHIVE MARKET"),
        ],
        "shop_id": "underhive_armory",
        "npcs": [
            NPC("TROOPER", 4, 8, (100,80,60),
                ["WE'VE BEEN HOLDING THIS SECTOR FOR FORTY DAYS. FORTY DAYS AND NO REINFORCEMENTS.",
                 "THE ARBITES SAYS HELP IS COMING. TROOPER SAYS THE ARBITES LIES. I BELIEVE THE TROOPER."],
                "TR"),
            NPC("ARBITRATOR", 3, 14, (60,60,80),
                ["THE GOVERNOR HAS BEEN... QUIET. TOO QUIET. I DON'T LIKE QUIET. NOT DOWN HERE.",
                 "FIND WHAT'S IN THE VAULTS. COME BACK ALIVE. IN THAT ORDER OF PRIORITY."],
                "AR"),
            NPC("REFUGEE", 8, 20, (80,70,60),
                ["THEY CAME FROM THE VAULTS LAST NIGHT. THE THINGS WITH TOO MANY TEETH.",
                 "MY FAMILY WAS BELOW. MY FAMILY IS BELOW STILL. PLEASE. DO NOT ASK ME MORE."],
                "RF"),
            NPC("TECH-ADEPT", 15, 5, (60,100,80),
                ["THE MACHINE SPIRITS IN SECTORS FOUR THROUGH NINE ARE SCREAMING. NOT MALFUNCTIONING. SCREAMING.",
                 "THE OMNISSIAH WEEPS FOR WHAT HAS BEEN DONE TO HIS CHILDREN HERE."],
                "TC"),
            NPC("APOTHECARY", 14, 8, (120,120,150),
                ["I CAN HEAL YOUR WOUNDS. I CANNOT HEAL WHAT DROVE YOU TO EARN THEM.",
                 "REST HERE. THE EMPEROR'S SHRINES STILL FUNCTION IN THIS QUARTER. FOR NOW."],
                "AP"),
        ],
        "has_shrine": True,
        "shrine_pos": (15, 14),
        "entry_pos": (12, 22),
    },
    "spire": {
        "name": "HIVE SPIRE OMEGA",
        "width": 28, "height": 28,
        "buildings": [
            (2,  2,  8, 6, "FORGE OF THE OMNISSIAH"),
            (14, 2,  10, 6, "INQUISITORIAL SAFEHOUSE"),
            (2,  12, 8,  6, "NOBLE QUARTER MEDICAE"),
            (14, 12, 10, 6, "ASTROPATHIC CHOIR"),
            (4,  20, 18, 6, "THE BLACK MARKET"),
        ],
        "shop_id": "spire_forge",
        "npcs": [
            NPC("LORD PETROV", 4, 8, (140,120,80),
                ["RIOTERS? IN MY SPIRE? PREPOSTEROUS. THE LOWER DECKS ARE ALWAYS RESTLESS.",
                 "WHATEVER IS HAPPENING DOWN THERE IS NO CONCERN OF THE NOBLE HOUSES. WE ARE SEALED IN.",
                 "WE ARE PERFECTLY SAFE. THE SEALS WILL HOLD. THEY ALWAYS HOLD."],
                "LP"),
            NPC("ACOLYTE MIRA", 16, 5, (80,80,120),
                ["MY INQUISITOR DIED THREE MONTHS AGO. I HAVE BEEN WAITING FOR A REPLACEMENT.",
                 "THE GOVERNOR IS COMPROMISED. I HAVE EVIDENCE. YOU WILL FIND IT IN THE IRON KEEP.",
                 "BRING THE SEAL. EXPOSE HIM. THE INQUISITION WILL COME. EVENTUALLY."],
                "AM"),
            NPC("DYING ASTROPATH", 16, 14, (100,80,140),
                ["I HAVE SEEN... IN THE WARP... A FIGURE ON A GOLDEN THRONE...",
                 "THE DAEMON PRINCE WAS A MAN ONCE. A HERO. LORD GENERAL XERATHUL. THE WAR OF MORTIS.",
                 "HE BARGAINED. FOR SURVIVAL. FOR THE SECTOR. A LIE HE TOLD HIMSELF FOR TWO CENTURIES.",
                 "FAITH-BASED POWERS WILL NOT WOUND HIM IN HIS FINAL FORM. THE WARP HAS MADE HIM HOLY."],
                "DA"),
            NPC("BLACK MARKETEER", 4, 22, (60,60,60),
                ["I ASK NO QUESTIONS. I SELL WHAT CANNOT BE SOLD. PAY WHAT CANNOT BE PRICED.",
                 "THE INQUISITION KNOWS ABOUT MY OPERATION. WE HAVE AN ARRANGEMENT.",
                 "...THE ARRANGEMENT IS THAT THEY DON'T COME HERE AND I DON'T ASK WHAT THEY DO EITHER."],
                "BM"),
        ],
        "has_shrine": True,
        "shrine_pos": (20, 20),
        "entry_pos": (14, 26),
    },
}

SHOPS = {
    "underhive_armory": {
        "name": "ARMORY OF THE WANING LIGHT",
        "items": ["stimm_injector", "sacred_ungent", "antitox_shot", "frag_grenade",
                  "autogun_reconditioned", "laspistol_kantrael", "lasgun_kantrael",
                  "chainsword", "bolt_pistol_mkiii", "flak_armour", "purity_seal",
                  "warp_dust", "incense_of_faith"],
    },
    "spire_forge": {
        "name": "FORGE OF THE OMNISSIAH",
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
