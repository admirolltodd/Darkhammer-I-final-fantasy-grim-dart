import random
from constants import *

class Enemy:
    def __init__(self, enemy_data, scale=1.0):
        d = enemy_data
        self.id       = d.get("id", "unknown")
        self.name     = d["name"]
        self.max_hp   = random.randint(d["hp_min"], d["hp_max"])
        self.hp       = self.max_hp
        self.str      = int(d["str"] * scale)
        self.defense  = int(d["def"] * scale)
        self.agi      = d["agi"]
        self.xp       = d["xp"]
        self.gelt     = random.randint(int(d["gelt"] * 0.8), int(d["gelt"] * 1.2))
        self.ai       = d.get("ai", AI_AGGRESSIVE)
        self.attacks  = d.get("attacks", ["strikes"])
        self.status_inflict = d.get("status_inflict", [])
        self.status_chance  = d.get("status_chance", 0)
        self.drops    = d.get("drops", [])
        self.color    = tuple(d.get("color", [150, 50, 50]))
        self.sprite_type = d.get("sprite_type", "humanoid")
        self.boss     = d.get("boss", False)
        self.boss_abilities = d.get("boss_abilities", [])
        self.immune   = set(d.get("immune", []))
        self.reanimation_chance = d.get("reanimation_chance", 0)
        self.always_berserk = d.get("always_berserk", False)
        self.berserk_threshold = d.get("berserk_threshold", 0.0)
        self.healed_by_holy = d.get("healed_by_holy", False)
        self.holy_resist    = d.get("holy_resist", False)
        self.casts_abilities = d.get("casts_abilities", False)
        self.splits_on_death = d.get("splits_on_death", None)
        self.synapse = d.get("synapse", False)

        self.alive    = True
        self.status   = STATUS_NONE
        self.status_turns = 0
        self.reanimated = False
        self.glitch_skip = False
        self.compelled = False
        self.berserk_active = self.always_berserk
        self.buffs    = {}
        self.debuffs  = {}
        self._boss_ability_cooldowns = {ab: 0 for ab in self.boss_abilities}

        # Scan data (revealed by Inquisitor ability)
        self.scanned = False

    def take_damage(self, amount, ignore_def=False, dmg_type=DMG_PHYSICAL):
        if dmg_type == DMG_HOLY and self.healed_by_holy:
            self.hp = min(self.max_hp, self.hp + amount)
            return -amount, False  # negative = healed
        if dmg_type == DMG_HOLY and self.holy_resist:
            # Gork and Mork shield their prophet — faith barely bites
            amount = max(1, amount // 4)

        if not ignore_def:
            reduction = self.defense // 2
            amount = max(1, amount - reduction)

        # Damage reduction buff
        if "dmg_reduce" in self.buffs:
            amount = int(amount * (1 - self.buffs["dmg_reduce"][0]))

        self.hp = max(0, self.hp - amount)

        if self.hp <= 0:
            # Reanimation protocols
            if self.reanimation_chance > 0 and not self.reanimated:
                if random.random() < self.reanimation_chance:
                    self.reanimated = True
                    self.hp = max(1, int(self.max_hp * 0.2))
                    return amount, False
            self.alive = False
        return amount, False

    def get_attack_verb(self):
        return random.choice(self.attacks)

    def decide_action(self, party_alive, enemies_alive, turn_num):
        ai = self.ai
        if self.always_berserk or (self.berserk_threshold > 0 and self.hp / self.max_hp < self.berserk_threshold):
            self.berserk_active = True

        if self.status in (STATUS_SYNLOCK, STATUS_CATATONIC):
            return {"type": "skip"}
        if self.status == STATUS_WARP_MAD:
            # Attack random target including allies
            target = random.choice(enemies_alive + party_alive) if enemies_alive else random.choice(party_alive)
            return {"type": "attack", "target": target}

        if self.berserk_active:
            target = random.choice(party_alive)
            return {"type": "attack", "target": target, "str_mult": 1.5}

        # Boss abilities — recovery abilities gated behind low HP / afflictions,
        # everything else joins the pool. ~45% chance per turn to use one.
        if self.boss and self.boss_abilities:
            for ab in list(self._boss_ability_cooldowns.keys()):
                if self._boss_ability_cooldowns[ab] > 0:
                    self._boss_ability_cooldowns[ab] -= 1
            RECOVERY = {"painboy_fix", "gorks_favor", "gork_morka_blessing"}
            usable = []
            for ab in self.boss_abilities:
                if ab == "phase2_transition" or self._boss_ability_cooldowns.get(ab, 0) > 0:
                    continue
                if ab in RECOVERY:
                    if self.hp < self.max_hp * 0.5:
                        usable.append(ab)
                elif ab == "shake_off":
                    if self.status != STATUS_NONE or self.debuffs:
                        usable.append(ab)
                else:
                    usable.append(ab)
            if usable and turn_num > 0 and random.random() < 0.45:
                ab = random.choice(usable)
                self._boss_ability_cooldowns[ab] = 3
                return {"type": "boss_ability", "ability": ab}

        # Normal AI
        if ai == AI_AGGRESSIVE:
            target = max(party_alive, key=lambda c: c.hp)
        elif ai == AI_CUNNING:
            target = min(party_alive, key=lambda c: c.hp)
        elif ai == AI_RANDOM:
            target = random.choice(party_alive)
        elif ai == AI_TACTICIAN:
            # Every third round: a coordinated strike at the weakest link
            target = min(party_alive, key=lambda c: c.hp)
            if turn_num % 3 == 0:
                return {"type": "attack", "target": target, "str_mult": 1.3}
        else:
            target = random.choice(party_alive)

        # Status infliction on hit
        status = None
        if self.status_inflict and random.random() < self.status_chance:
            status = random.choice(self.status_inflict)

        return {"type": "attack", "target": target, "status": status}

    def apply_status(self, status_id, turns=3):
        if status_id in self.immune:
            return False
        self.status = status_id
        self.status_turns = turns
        return True

    def tick_status(self):
        msgs = []
        if self.status == STATUS_PLAGUE:
            dmg = max(1, self.max_hp // 10)
            self.hp = max(0, self.hp - dmg)
            if self.hp == 0:
                self.alive = False
            msgs.append(f"{self.name} WRITHES FROM PLAGUE-TOUCH!")
        if self.status_turns > 0:
            self.status_turns -= 1
            if self.status_turns == 0:
                self.status = STATUS_NONE
        return msgs

    def roll_drops(self, item_db):
        dropped = []
        for item_id, chance in self.drops:
            if random.random() < chance and item_id in item_db:
                dropped.append(item_db[item_id])
        return dropped
