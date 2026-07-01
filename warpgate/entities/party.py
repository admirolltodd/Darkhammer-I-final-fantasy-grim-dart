from constants import *

class Party:
    def __init__(self):
        self.members   = []
        self.inventory = {}   # item_id -> count
        self.gelt      = 200
        self.corruption= 0
        self.morale    = START_MORALE
        self.flags     = {}
        self.location  = "UNDERHIVE DELTA"
        self.world_x   = 5
        self.world_y   = 5
        self.playtime  = 0
        self.facing    = "down"
        self.moving    = False

    def add_member(self, character):
        if len(self.members) < MAX_PARTY:
            self.members.append(character)

    @property
    def alive_members(self):
        return [m for m in self.members if m.alive]

    @property
    def all_alive(self):
        return all(m.alive for m in self.members)

    @property
    def any_alive(self):
        return any(m.alive for m in self.members)

    def add_item(self, item_id, count=1):
        self.inventory[item_id] = min(MAX_ITEMS, self.inventory.get(item_id, 0) + count)

    def remove_item(self, item_id, count=1):
        if item_id in self.inventory:
            self.inventory[item_id] -= count
            if self.inventory[item_id] <= 0:
                del self.inventory[item_id]

    def has_item(self, item_id):
        return self.inventory.get(item_id, 0) > 0

    def item_count(self, item_id):
        return self.inventory.get(item_id, 0)

    def add_gelt(self, amount):
        self.gelt += amount

    def spend_gelt(self, amount):
        if self.gelt >= amount:
            self.gelt -= amount
            return True
        return False

    def adjust_corruption(self, delta):
        self.corruption = max(0, min(MAX_CORRUPTION, self.corruption + delta))

    def adjust_morale(self, delta):
        self.morale = max(0, min(MAX_MORALE, self.morale + delta))

    def has_commissar(self):
        return any(m.class_id == CLASS_COMMISSAR and m.alive for m in self.members)

    def has_sister(self):
        return any(m.class_id == CLASS_SISTER and m.alive for m in self.members)

    def has_tech_priest(self):
        return any(m.class_id == CLASS_TECH_PRIEST and m.alive for m in self.members)

    def morale_str_mod(self):
        if self.morale <= 0:
            return 0.75
        elif self.morale >= MAX_MORALE:
            return 1.15
        return 1.0

    def morale_def_mod(self):
        return self.morale_str_mod()

    def rest_at_shrine(self):
        for m in self.members:
            m.heal(m.max_hp)
            m.clear_status()
            m.faith_pts = m.faith_max
        self.morale = min(MAX_MORALE, self.morale + 2)

    def full_rest(self, cost=0):
        if cost > 0 and not self.spend_gelt(cost):
            return False
        for m in self.members:
            m.heal(m.max_hp // 2)
            m.warp = m.warp_max_total
        return True

    def set_flag(self, flag, value=True):
        self.flags[flag] = value

    def get_flag(self, flag):
        return self.flags.get(flag, False)

    def summary(self):
        return [{"name": m.name, "class": m.class_name, "level": m.level} for m in self.members]

    def to_dict(self):
        return {
            "members": [m.to_dict() for m in self.members],
            "inventory": self.inventory,
            "gelt": self.gelt,
            "corruption": self.corruption,
            "morale": self.morale,
            "flags": self.flags,
            "location": self.location,
            "world_x": self.world_x,
            "world_y": self.world_y,
            "playtime": self.playtime,
            "party_summary": self.summary(),
        }

    @classmethod
    def from_dict(cls, d, item_db):
        from entities.character import Character
        p = cls()
        for cd in d.get("members", []):
            p.members.append(Character.from_dict(cd, item_db))
        p.inventory = d.get("inventory", {})
        p.gelt      = d.get("gelt", 200)
        p.corruption= d.get("corruption", 0)
        p.morale    = d.get("morale", START_MORALE)
        p.flags     = d.get("flags", {})
        p.location  = d.get("location", "UNDERHIVE DELTA")
        p.world_x   = d.get("world_x", 5)
        p.world_y   = d.get("world_y", 5)
        p.playtime  = d.get("playtime", 0)
        return p
