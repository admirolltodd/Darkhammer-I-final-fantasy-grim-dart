import random
from constants import *

BASE_STATS = {
    CLASS_ASTARTES:    {"hp":45,"str":18,"def":16,"agi":6, "faith":5, "psy":2,  "hit":84,"eva":5, "mrst":8},
    CLASS_INQUISITOR:  {"hp":32,"str":12,"def":10,"agi":10,"faith":14,"psy":10, "hit":84,"eva":10,"mrst":12},
    CLASS_PSYKER:      {"hp":22,"str":6, "def":6, "agi":12,"faith":8, "psy":20, "hit":84,"eva":12,"mrst":6},
    CLASS_SISTER:      {"hp":30,"str":10,"def":12,"agi":9, "faith":20,"psy":6,  "hit":84,"eva":9, "mrst":14},
    CLASS_TECH_PRIEST: {"hp":28,"str":9, "def":14,"agi":7, "faith":6, "psy":4,  "hit":84,"eva":7, "mrst":8},
    CLASS_COMMISSAR:   {"hp":35,"str":14,"def":11,"agi":11,"faith":12,"psy":3,  "hit":84,"eva":11,"mrst":16},
}

GROWTH = {
    CLASS_ASTARTES:    {"hp":12,"str":4,"def":3,"agi":1,"faith":1,"psy":0},
    CLASS_INQUISITOR:  {"hp":8, "str":3,"def":2,"agi":2,"faith":3,"psy":2},
    CLASS_PSYKER:      {"hp":5, "str":1,"def":1,"agi":2,"faith":2,"psy":5},
    CLASS_SISTER:      {"hp":7, "str":2,"def":3,"agi":2,"faith":5,"psy":1},
    CLASS_TECH_PRIEST: {"hp":6, "str":2,"def":3,"agi":1,"faith":1,"psy":0},
    CLASS_COMMISSAR:   {"hp":9, "str":3,"def":2,"agi":2,"faith":3,"psy":0},
}

XP_TABLE = [0] + [int(BASE_XP * (1.8 ** i)) for i in range(MAX_LEVEL)]

WARP_MAX_BASE = {
    CLASS_PSYKER: 10, CLASS_INQUISITOR: 4,
    CLASS_ASTARTES: 0, CLASS_SISTER: 0,
    CLASS_TECH_PRIEST: 0, CLASS_COMMISSAR: 0,
}
FAITH_MAX_BASE = {
    CLASS_SISTER: 10, CLASS_COMMISSAR: 4,
    CLASS_ASTARTES: 0, CLASS_INQUISITOR: 0,
    CLASS_TECH_PRIEST: 0, CLASS_PSYKER: 0,
}

class Character:
    def __init__(self, name, class_id):
        self.name = name[:8].upper()
        self.class_id = class_id
        self.level = 1
        self.xp = 0
        self.promoted = False

        b = BASE_STATS[class_id]
        self.max_hp    = b["hp"]
        self.hp        = self.max_hp
        self.base_str  = b["str"]
        self.base_def  = b["def"]
        self.base_agi  = b["agi"]
        self.base_faith= b["faith"]
        self.base_psy  = b["psy"]
        self.base_hit  = b["hit"]
        self.base_eva  = b["eva"]
        self.base_mrst = b["mrst"]

        self.warp_max  = WARP_MAX_BASE.get(class_id, 0)
        self.warp      = self.warp_max
        self.faith_max = FAITH_MAX_BASE.get(class_id, 0)
        self.faith_pts = self.faith_max

        self.equipment = {s: None for s in ALL_SLOTS}
        self.status    = STATUS_NONE
        self.status_turns = 0
        self.alive     = True
        self.corruption= 0

        self.known_powers = []
        self._init_powers()

        self._iron_halo_used = False
        self._gene_seed_used = False
        self._rosette_used   = False
        self._miraculous_trigger = False

    def _init_powers(self):
        from assets.data import spells_data
        for sp in spells_data.STARTING_POWERS.get(self.class_id, []):
            self.known_powers.append(sp)

    @property
    def class_name(self):
        if self.promoted:
            return CLASS_PROMOTED_NAMES[self.class_id]
        return CLASS_NAMES[self.class_id]

    @property
    def str_total(self):
        b = self.base_str
        for slot in ALL_SLOTS:
            eq = self.equipment[slot]
            if eq:
                b += eq.get("str_bonus", 0)
        return b

    @property
    def def_total(self):
        b = self.base_def
        for slot in ALL_SLOTS:
            eq = self.equipment[slot]
            if eq:
                b += eq.get("def_bonus", 0)
        return b

    @property
    def agi_total(self):
        b = self.base_agi
        for slot in ALL_SLOTS:
            eq = self.equipment[slot]
            if eq:
                b += eq.get("agi_bonus", 0)
        return b

    @property
    def faith_total(self):
        b = self.base_faith
        for slot in ALL_SLOTS:
            eq = self.equipment[slot]
            if eq:
                b += eq.get("faith_bonus", 0)
        return b

    @property
    def psy_total(self):
        b = self.base_psy
        for slot in ALL_SLOTS:
            eq = self.equipment[slot]
            if eq:
                b += eq.get("psy_bonus", 0)
        return b

    @property
    def hit_total(self):
        b = self.base_hit
        for slot in ALL_SLOTS:
            eq = self.equipment[slot]
            if eq:
                b += eq.get("hit_bonus", 0)
        if self.status == STATUS_PSY_STATIC:
            b = 25
        return min(b, 99)

    @property
    def eva_total(self):
        b = self.base_eva
        for slot in ALL_SLOTS:
            eq = self.equipment[slot]
            if eq:
                b += eq.get("eva_bonus", 0)
        return min(b, 75)

    @property
    def warp_max_total(self):
        b = self.warp_max
        for slot in ALL_SLOTS:
            eq = self.equipment[slot]
            if eq:
                b += eq.get("warp_max_bonus", 0)
        return b

    def can_act(self):
        return self.alive and self.status not in (STATUS_CATATONIC, STATUS_SYNLOCK, STATUS_CRYSTAL, STATUS_VAPORIZED)

    def take_damage(self, amount, ignore_def=False, dmg_type=DMG_PHYSICAL):
        if not ignore_def:
            reduction = self.def_total // 2
            amount = max(1, amount - reduction)
        # Iron Halo check
        eq = self.equipment.get(SLOT_RELIC)
        if eq and eq.get("negate_chance") and not self._iron_halo_used:
            if random.random() < eq["negate_chance"]:
                self._iron_halo_used = True
                return 0, True  # negated
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            # Gene-seed check
            eq_relic = self.equipment.get(SLOT_RELIC)
            if eq_relic and eq_relic.get("survive_lethal") and not self._gene_seed_used:
                self._gene_seed_used = True
                self.hp = 1
            else:
                self.alive = False
        return amount, False

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
        if self.hp > 0:
            self.alive = True

    def restore_warp(self, amount):
        self.warp = min(self.warp_max_total, self.warp + amount)

    def restore_faith(self, amount):
        self.faith_pts = min(self.faith_max, self.faith_pts + amount)

    def apply_status(self, status_id, turns=3):
        if status_id in (self.status,):
            return False
        self.status = status_id
        self.status_turns = turns
        return True

    def clear_status(self, status_id=None):
        if status_id is None or self.status == status_id:
            self.status = STATUS_NONE
            self.status_turns = 0

    def tick_status(self):
        msgs = []
        if self.status == STATUS_PLAGUE:
            dmg = max(1, self.max_hp // 10)
            self.hp = max(0, self.hp - dmg)
            if self.hp == 0:
                self.alive = False
            msgs.append(f"{self.name} WRITHES FROM PLAGUE-TOUCH! -{dmg}HP")
        if self.status_turns > 0:
            self.status_turns -= 1
            if self.status_turns == 0 and self.status not in (STATUS_PLAGUE, STATUS_BLOOD_RAGE):
                self.status = STATUS_NONE
        return msgs

    def gain_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.level < MAX_LEVEL and self.xp >= XP_TABLE[self.level + 1]:
            self.level += 1
            leveled = True
            self._level_up_stats()
            if self.level == PROMOTION_LEVEL and not self.promoted:
                self.promoted = True
        return leveled

    def _level_up_stats(self):
        g = GROWTH[self.class_id]
        self.max_hp     += g["hp"] + random.randint(0, 2)
        self.hp          = self.max_hp
        self.base_str   += g["str"]
        self.base_def   += g["def"]
        self.base_agi   += g["agi"]
        self.base_faith += g["faith"]
        self.base_psy   += g["psy"]
        if self.class_id in (CLASS_PSYKER, CLASS_INQUISITOR):
            self.warp_max += 1
            self.warp = self.warp_max
        if self.class_id in (CLASS_SISTER, CLASS_COMMISSAR):
            self.faith_max += 1
            self.faith_pts = self.faith_max
        # Learn new powers at level thresholds
        self._check_power_unlock()

    def _check_power_unlock(self):
        from assets.data import spells_data
        unlocks = spells_data.LEVEL_UNLOCKS.get(self.class_id, {})
        for lvl, power_id in unlocks.items():
            if self.level >= lvl and power_id not in self.known_powers:
                self.known_powers.append(power_id)

    def equip(self, slot, item_data):
        self.equipment[slot] = item_data

    def unequip(self, slot):
        old = self.equipment[slot]
        self.equipment[slot] = None
        return old

    def can_equip(self, item_data):
        allowed = item_data.get("classes", "all")
        if allowed == "all":
            return True
        return self.class_name in allowed

    def to_dict(self):
        return {
            "name": self.name,
            "class_id": self.class_id,
            "level": self.level,
            "xp": self.xp,
            "promoted": self.promoted,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "base_str": self.base_str,
            "base_def": self.base_def,
            "base_agi": self.base_agi,
            "base_faith": self.base_faith,
            "base_psy": self.base_psy,
            "base_hit": self.base_hit,
            "base_eva": self.base_eva,
            "base_mrst": self.base_mrst,
            "warp_max": self.warp_max,
            "warp": self.warp,
            "faith_max": self.faith_max,
            "faith_pts": self.faith_pts,
            "equipment": {s: (v.get("id") if v else None) for s, v in self.equipment.items()},
            "known_powers": self.known_powers,
            "corruption": self.corruption,
        }

    @classmethod
    def from_dict(cls, d, item_db):
        c = cls(d["name"], d["class_id"])
        c.level = d["level"]
        c.xp = d["xp"]
        c.promoted = d["promoted"]
        c.max_hp = d["max_hp"]
        c.hp = d["hp"]
        c.base_str = d["base_str"]
        c.base_def = d["base_def"]
        c.base_agi = d["base_agi"]
        c.base_faith = d["base_faith"]
        c.base_psy = d["base_psy"]
        c.base_hit = d["base_hit"]
        c.base_eva = d["base_eva"]
        c.base_mrst = d["base_mrst"]
        c.warp_max = d["warp_max"]
        c.warp = d["warp"]
        c.faith_max = d["faith_max"]
        c.faith_pts = d["faith_pts"]
        c.known_powers = d["known_powers"]
        c.corruption = d["corruption"]
        for slot, item_id in d["equipment"].items():
            if item_id and item_id in item_db:
                c.equipment[slot] = item_db[item_id]
        return c
