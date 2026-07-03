import random
from constants import *
from entities.enemy import Enemy
from data import loader

class BattleResult:
    VICTORY   = "VICTORY"
    DEFEAT    = "DEFEAT"
    FLED      = "FLED"
    TERRIFIED = "TERRIFIED"

class Battle:
    def __init__(self, party, enemy_list, audio=None):
        self.party    = party
        self.enemies  = enemy_list
        self.audio    = audio
        self.log      = []
        self.state    = "PLAYER_MENU"
        self.result   = None
        self.turn_num = 0
        self.turn_order = []
        self.current_actor_idx = 0
        self.current_char_idx = 0
        self.pending_actions  = {}
        self.vortex_turns     = 0
        self.vortex_damage    = 0
        self.party_buffs      = {}   # member_name -> {buff: (val, turns)}
        self.xp_gained  = 0
        self.gelt_gained= 0
        self.items_gained = []
        self.levelups   = []   # (member, old_stats, new_stats) recorded on victory
        self.terrified  = False
        self.last_psyker_power = None
        self.sister_miraculous_used = False
        self.commissar_retreat_block = False

        self._build_turn_order()

    def _build_turn_order(self):
        actors = []
        for c in self.party.alive_members:
            roll = c.agi_total + random.randint(1, 8)
            actors.append(("party", c, roll))
        for e in self.enemies:
            if e.alive:
                roll = e.agi + random.randint(1, 8)
                actors.append(("enemy", e, roll))
        actors.sort(key=lambda x: -x[2])
        self.turn_order = actors
        self.current_actor_idx = 0

    def _log(self, msg):
        self.log.append(msg.upper())
        if len(self.log) > 100:
            self.log = self.log[-100:]

    def alive_enemies(self):
        return [e for e in self.enemies if e.alive]

    def alive_party(self):
        return self.party.alive_members

    # ── Player action resolution ───────────────────────────────────────────────

    def do_attack(self, attacker, target):
        hit_roll = random.randint(1, 100)
        if hit_roll > attacker.hit_total:
            self._log(f"{attacker.name} FIRES — GRAZED! MISS!")
            if self.audio:
                self.audio.play_sfx("miss")
            return

        base = attacker.str_total * self.party.morale_str_mod()
        # Weapon multipliers
        eq = attacker.equipment.get(SLOT_MAIN)
        mult = 1.0
        if eq:
            if eq.get("two_handed"):
                mult = 1.1
            # Overheat check
            if eq.get("overheat_chance") and random.random() < eq["overheat_chance"]:
                self._log(f"{attacker.name}'S PLASMA GUN OVERHEATS! TAKES {eq['overheat_dmg']} DAMAGE!")
                attacker.hp = max(0, attacker.hp - eq["overheat_dmg"])
                if attacker.hp == 0:
                    attacker.alive = False
        dmg = max(1, int(base * mult) + random.randint(1, 6))

        # Critical
        crit = False
        if random.randint(1, 100) <= 5:
            dmg *= 2
            crit = True

        # Relic: Oath of Moment
        relic = attacker.equipment.get(SLOT_RELIC)
        if relic and relic.get("str_vs_boss") and target.boss:
            dmg += relic["str_vs_boss"]

        # Orky Relic confusion
        if relic and relic.get("confuse_enemy_chance"):
            if random.random() < relic["confuse_enemy_chance"]:
                self._log(f"ENEMIES ARE CONFUSED — THEY FIGHT EACH OTHER!")
                for e in self.alive_enemies():
                    if e != target:
                        dmg_c = max(1, int(e.str * 0.3))
                        e.take_damage(dmg_c, ignore_def=True)

        dmg_type = (eq.get("dmg_type", DMG_PHYSICAL) if eq else DMG_PHYSICAL)

        actual, negated = target.take_damage(dmg, dmg_type=dmg_type)
        if negated:
            self._log(f"{target.name} IRON HALO NEGATES THE BLOW!")
            return

        crit_str = " CRITICAL!" if crit else ""
        self._log(f"{attacker.name} ENGAGES {target.name}! -{actual}HP{crit_str}")
        if self.audio:
            self.audio.play_sfx("crit" if crit else "hit")

        # Status on hit
        if eq and eq.get("status_on_hit") and eq.get("status_chance"):
            if random.random() < eq["status_chance"]:
                s_id = eq["status_on_hit"]
                if target.apply_status(s_id):
                    self._log(f"{target.name} SUFFERS {STATUS_NAMES[s_id]}!")
                    if self.audio:
                        self.audio.play_sfx("status")

        if not target.alive:
            self._log(f"{target.name} HAS BEEN SLAIN! FOR THE EMPEROR!")
            if self.audio:
                self.audio.play_sfx("death")
            self._on_enemy_death(target)

    def do_use_power(self, caster, power_data, targets):
        import assets.data.config.spells_data as sd
        sp = power_data
        effect = sp.get("effect")
        res    = sp.get("resource", RES_NONE)
        cost   = sp.get("cost", 0)

        # Deduct resource
        if res == RES_WARP:
            caster.warp -= cost
            # Perils of the Warp
            peril = self._check_perils(caster, sp)
            if peril:
                return  # Perils cancelled the action
        elif res == RES_FAITH:
            if sp.get("spend_all"):
                cost = caster.faith_pts
                caster.faith_pts = 0
            else:
                caster.faith_pts -= cost

        self.last_psyker_power = sp["id"]

        # Execute effect
        if effect == "damage":
            val = sp.get("value", 30)
            dmg_type = sp.get("dmg_type", DMG_WARP)
            ignore_def = sp.get("ignore_def", False)
            for t in targets:
                actual = t.take_damage(val + random.randint(-5, 10), ignore_def=ignore_def, dmg_type=dmg_type)
                if isinstance(actual, tuple):
                    actual = actual[0]
                chaos_bonus = sp.get("chaos_double") and t.sprite_type in ("daemon", "heavy_astartes", "sorcerer", "boss_daemon")
                if chaos_bonus:
                    bonus = t.take_damage(val, ignore_def=True, dmg_type=dmg_type)
                    self._log(f"HOLY POWER BURNS THE UNCLEAN! DOUBLE DAMAGE!")
                self._log(f"{caster.name} UNLEASHES {sp['name']}! {t.name} TAKES {actual}HP!")
                if not t.alive:
                    self._on_enemy_death(t)

        elif effect == "drain":
            for t in targets:
                dmg = t.take_damage(sp.get("value", 40), dmg_type=DMG_WARP)
                if isinstance(dmg, tuple):
                    dmg = dmg[0]
                restore = dmg // 2
                caster.heal(restore)
                self._log(f"{caster.name} LEACHES LIFE FROM {t.name}! -{dmg}HP / +{restore}HP!")
                if not t.alive:
                    self._on_enemy_death(t)

        elif effect == "damage_status":
            val = sp.get("value", 30)
            status = sp.get("status")
            sc = sp.get("status_chance", 0.5)
            dmg_type = sp.get("dmg_type", DMG_WARP)
            for t in targets:
                actual = t.take_damage(val + random.randint(-5, 10), dmg_type=dmg_type)
                if isinstance(actual, tuple):
                    actual = actual[0]
                self._log(f"{caster.name}: {sp['name']}! {t.name} TAKES {actual}HP!")
                if status and random.random() < sc:
                    if t.apply_status(status):
                        self._log(f"{t.name} SUFFERS {STATUS_NAMES[status]}!")
                if not t.alive:
                    self._on_enemy_death(t)

        elif effect == "inflict_status":
            status = sp["status"]
            turns = sp.get("status_turns", 2)
            for t in targets:
                if hasattr(t, "apply_status"):
                    if t.apply_status(status, turns):
                        self._log(f"{caster.name}: {sp['name']}! {t.name} IS {STATUS_NAMES[status]}!")
                    else:
                        self._log(f"{t.name} RESISTS!")

        elif effect == "heal_faith":
            mult = sp.get("multiplier", 4)
            val  = caster.faith_total * mult
            for t in targets:
                t.heal(int(val))
                self._log(f"{caster.name}: {sp['name']}! {t.name} RESTORED {int(val)}HP!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "heal_faith_all":
            mult = sp.get("multiplier", 2)
            val  = caster.faith_total * mult
            for t in targets:
                t.heal(int(val))
            self._log(f"{caster.name}: {sp['name']}! PARTY RESTORED {int(val)}HP!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "tech_heal":
            val = 20 + caster.level * 5
            for t in targets:
                t.heal(val)
                self._log(f"{caster.name} REPAIRS {t.name}! +{val}HP!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "full_heal":
            for t in targets:
                t.heal(t.max_hp)
                t.alive = True
                self._log(f"{caster.name}: {sp['name']}! {t.name} FULLY RESTORED!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "full_heal_cleanse":
            for t in targets:
                t.heal(t.max_hp)
                t.alive = True
                t.clear_status()
            self._log(f"{caster.name}: THE EMPEROR PROTECTS! PARTY FULLY RESTORED AND CLEANSED!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "revive":
            val = sp.get("value", 0.5)
            for t in targets:
                if not t.alive:
                    t.hp = max(1, int(t.max_hp * val))
                    t.alive = True
                    self._log(f"{t.name} IS RESTORED TO {t.hp}HP! THE EMPEROR'S WILL IS NOT YET DONE!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "cure_status":
            for t in targets:
                t.clear_status()
                self._log(f"{t.name}'S AFFLICTION IS PURGED!")

        elif effect == "cure_specific":
            cures = sp.get("cures", [])
            for t in targets:
                if t.status in cures:
                    t.clear_status()
                    self._log(f"{t.name}'S AFFLICTION IS CAUTERIZED AWAY!")

        elif effect == "cure_all_status":
            for t in targets:
                t.clear_status()
            self._log(f"ALL AFFLICTIONS PURGED FROM PARTY!")

        elif effect == "damage_reduction":
            val   = sp.get("value", 0.5)
            turns = sp.get("turns", 2)
            for t in targets:
                name = getattr(t, "name", "unknown")
                self._ensure_party_buff(name)
                self.party_buffs[name]["dmg_reduce"] = (val, turns)
            self._log(f"{caster.name}: {sp['name']}! PARTY SHIELDS RAISED!")

        elif effect == "phys_immune":
            turns = sp.get("turns", 2)
            for t in targets:
                self._ensure_party_buff(t.name)
                self.party_buffs[t.name]["phys_immune"] = (True, turns)
            self._log(f"{caster.name}: IRON ARM! {targets[0].name} SHIELDED!")

        elif effect == "strip_def":
            turns = sp.get("turns", 3)
            for t in targets:
                t.buffs["def_stripped"] = (t.defense, turns)
                t.defense = 0
            self._log(f"{caster.name}: THE FLESH IS WEAK! {targets[0].name} DEFENCE STRIPPED!")

        elif effect == "pct_damage":
            pct = sp.get("value", 0.3)
            for t in targets:
                dmg = max(1, int(t.hp * pct))
                t.hp = max(1, t.hp - dmg)
                self._log(f"{caster.name}: PSYCHIC SHRIEK! {t.name} LOSES {dmg}HP!")

        elif effect == "mass_flee":
            self._log(f"{caster.name}: TERRIFY! ALL ENEMIES FLEE IN TERROR!")
            self.terrified = True
            self.result = BattleResult.TERRIFIED

        elif effect == "mass_kill":
            self._log(f"{caster.name}: EXTERMINATUS! PURGE THEM ALL!")
            self.party.adjust_corruption(4)
            self._log("SUCH POWER HAS A PRICE. CORRUPTION +4.")
            for t in targets:
                val = sp.get("value", 999)
                if t.boss:
                    t.take_damage(val, ignore_def=True)
                    self._log(f"{t.name} TAKES {val} DAMAGE!")
                else:
                    t.hp = 0
                    t.alive = False
                    self._log(f"{t.name} IS VAPORIZED!")
                if not t.alive:
                    self._on_enemy_death(t)

        elif effect == "mind_war":
            self.party.adjust_corruption(2)
            for t in targets:
                self_dmg = max(1, int(caster.max_hp * 0.25))
                caster.hp = max(0, caster.hp - self_dmg)
                if t.boss:
                    t.take_damage(200, ignore_def=True)
                    self._log(f"MIND WAR! {t.name} AND {caster.name} BOTH SUFFER! {caster.name} LOSES {self_dmg}HP!")
                else:
                    t.hp = 0
                    t.alive = False
                    self._log(f"MIND WAR DESTROYS {t.name}! {caster.name} LOSES {self_dmg}HP FROM BACKLASH!")
                    self._on_enemy_death(t)

        elif effect == "persistent_damage":
            self.vortex_turns  = sp.get("turns", 3)
            self.vortex_damage = sp.get("value", 40)
            self._log(f"{caster.name}: VORTEX! A WARP RIFT TEARS REALITY!")

        elif effect == "buff_hp":
            val   = sp.get("value", 0.4)
            turns = sp.get("turns", 3)
            for t in targets:
                bonus = int(t.max_hp * val)
                self._ensure_party_buff(t.name)
                self.party_buffs[t.name]["hp_boost"] = (bonus, turns)
                t.heal(bonus)
            self._log(f"{caster.name}: ENDURANCE! {targets[0].name} BOLSTERED!")

        elif effect == "double_act":
            turns = sp.get("turns", 3)
            for t in targets:
                self._ensure_party_buff(t.name)
                self.party_buffs[t.name]["double_act"] = (True, turns)
            self._log(f"{caster.name}: WARP SPEED! {targets[0].name} ACTS AT IMPOSSIBLE SPEED!")

        elif effect == "buff_agi":
            val   = sp.get("value", 1.0)
            turns = sp.get("turns", 3)
            for t in targets:
                self._ensure_party_buff(t.name)
                self.party_buffs[t.name]["agi_boost"] = (val, turns)
            self._log(f"{caster.name}: INSPIRING! {targets[0].name} SPEED SURGES!")

        elif effect == "buff_def":
            val   = sp.get("value", 0.3)
            turns = sp.get("turns", 3)
            for t in targets:
                self._ensure_party_buff(t.name)
                self.party_buffs[t.name]["def_boost"] = (val, turns)
            self._log(f"{caster.name}: PROTECTION GRANTED TO {targets[0].name}!")

        elif effect == "debuff_str":
            val   = sp.get("value", 0.3)
            turns = sp.get("turns", 3)
            for t in targets:
                t.debuffs["str_reduce"] = (val, turns)
            self._log(f"{caster.name}: INQUISITORIAL AUTHORITY! ENEMIES COWED!")

        elif effect == "confuse_enemy":
            turns = sp.get("turns", 2)
            for t in targets:
                t.compelled = True  # reuse compel flag as confuse
                t.status = STATUS_WARP_MAD
                t.status_turns = turns
            self._log(f"{caster.name}: HALLUCINATION! {targets[0].name} ATTACKS ITS OWN!")

        elif effect == "scan":
            for t in targets:
                t.scanned = True
            self._log(f"{caster.name} INTERROGATES {targets[0].name}: HP {targets[0].hp}/{targets[0].max_hp} | STR {targets[0].str} DEF {targets[0].defense}")

        elif effect == "compel":
            turns = sp.get("turns", 3)
            for t in targets:
                t.compelled = True
                self._ensure_party_buff(t.name)
            self._log(f"{caster.name}: COMPEL! {targets[0].name} NOW SERVES THE IMPERIUM!")

        elif effect == "purge":
            for t in targets:
                if hasattr(t, "corruption"):
                    t.corruption = max(0, t.corruption - 5)
                    self._log(f"{caster.name} PURGES CORRUPTION FROM {t.name}!")
                else:
                    dmg = 60 + random.randint(0, 20)
                    t.take_damage(dmg, ignore_def=True)
                    self._log(f"{caster.name}: PURGE THE HERETIC! {t.name} TAKES {dmg}HP!")
                    if not t.alive:
                        self._on_enemy_death(t)

        elif effect == "cleanse_all":
            for t in targets:
                t.clear_status()
            self._log(f"{caster.name}: IRON DISCIPLINE! ALL AFFLICTIONS PURGED!")

        elif effect == "death_or_glory":
            dmg_each = [max(1, int(t.max_hp * 0.15)) for t in targets]
            for t, d in zip(targets, dmg_each):
                t.hp = max(0, t.hp - d)
                self._ensure_party_buff(t.name)
                self.party_buffs[t.name]["str_boost"] = (0.5, 1)
            self._log(f"{caster.name}: DEATH OR GLORY! PARTY SURGES AT GREAT COST!")

        elif effect == "summary_execution":
            for t in targets:
                if hasattr(t, "corruption"):
                    if t.status == STATUS_ROUT:
                        t.clear_status()
                        t.heal(t.max_hp // 2)
                        self._log(f"{caster.name} EXECUTES COWARDICE FROM {t.name}! RESTORED TO DUTY!")
                    else:
                        self._log(f"{caster.name}'S BOLT PISTOL FINDS NO COWARDS HERE.")
                else:
                    if random.random() < 0.30:
                        t.hp = 0
                        t.alive = False
                        self._log(f"{caster.name}: SUMMARY EXECUTION! {t.name} IS ENDED!")
                        self._on_enemy_death(t)
                    else:
                        self._log(f"EXECUTION FAILS TO FIND THE MARK!")

        elif effect == "random_buff":
            buff_choice = random.randint(0, 5)
            for t in targets:
                self._ensure_party_buff(t.name)
                if buff_choice == 0:
                    self.party_buffs[t.name]["str_boost"] = (0.2, 3)
                elif buff_choice == 1:
                    self.party_buffs[t.name]["def_boost"] = (0.2, 3)
                elif buff_choice == 2:
                    self.party_buffs[t.name]["agi_boost"] = (0.2, 3)
                elif buff_choice == 3:
                    t.heal(20)
                elif buff_choice == 4:
                    t.restore_warp(3)
                elif buff_choice == 5:
                    self.party_buffs[t.name]["dmg_reduce"] = (0.2, 3)
            self._log(f"{caster.name}: CANTICLES! THE OMNISSIAH BLESSES THE PARTY!")

        elif effect == "martyrdom":
            total = cost  # already captured before setting to 0
            heal_per = total * 50
            for t in targets:
                t.heal(heal_per)
            self._log(f"{caster.name}: MARTYRDOM! PARTY RESTORED {heal_per}HP!")

        elif effect == "multi_hit":
            hits = random.randint(*sp.get("hits", [2, 4]))
            for _ in range(hits):
                self.do_attack(caster, random.choice(self.alive_enemies()) if self.alive_enemies() else targets[0])

        elif effect == "heavy_attack":
            mult = sp.get("multiplier", 2.0)
            old_str = caster.base_str
            caster.base_str = int(caster.base_str * mult)
            self.do_attack(caster, targets[0])
            caster.base_str = old_str

        elif effect == "tech_heal":
            val = 20 + caster.level * 5
            for t in targets:
                t.heal(val)
            self._log(f"{caster.name} REPAIRS {targets[0].name}! +{val}HP!")

        elif effect == "glitch":
            for t in targets:
                t.glitch_skip = True
            self._log(f"{caster.name}: BINARIC OVERRIDE! {targets[0].name} SUFFERS GLITCH!")

        elif effect == "immune_status":
            turns = sp.get("turns", 3)
            immune = sp.get("immune_to", [])
            for t in targets:
                self._ensure_party_buff(t.name)
                self.party_buffs[t.name]["status_immune"] = (immune, turns)
            self._log(f"{caster.name}: MENTAL FORTITUDE! PARTY MINDS SHIELDED!")

        elif effect == "status_immune":
            turns = sp.get("turns", 3)
            for t in targets:
                self._ensure_party_buff(t.name)
                self.party_buffs[t.name]["full_status_immune"] = (True, turns)
            self._log(f"{caster.name}: DIVINE PROTECTION! {targets[0].name} CANNOT BE AFFLICTED!")

        elif effect == "strip_and_damage":
            for t in targets:
                old_def = t.defense
                t.defense = 0
                dmg = sp.get("value", 120)
                actual = t.take_damage(dmg, ignore_def=True, dmg_type=sp.get("dmg_type", DMG_FIRE))
                t.defense = old_def
                self._log(f"{caster.name}: PURGATION! ALL DEFENCES STRIPPED! {t.name} TAKES {dmg}HP!")
                if not t.alive:
                    self._on_enemy_death(t)

    def _ensure_party_buff(self, name):
        if name not in self.party_buffs:
            self.party_buffs[name] = {}

    def _check_perils(self, caster, spell):
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)
        if roll1 + roll2 == 2:
            self.party.adjust_corruption(3)
            self._log("THE WARP LEAVES ITS MARK. CORRUPTION +3.")
            peril = random.randint(0, 3)
            if peril == 0:
                dmg = max(1, caster.max_hp // 4)
                caster.hp = max(0, caster.hp - dmg)
                self._log(f"PERILS OF THE WARP! DAEMON CLAWS RAKE THROUGH THE VEIL! {caster.name} TAKES {dmg}HP!")
                if self.audio:
                    self.audio.play_sfx("perils")
            elif peril == 1:
                for m in self.alive_party():
                    m.apply_status(STATUS_WARP_MAD, 2)
                self._log(f"PERILS! WARP STATIC OVERWHELMS THE PARTY!")
                if self.audio:
                    self.audio.play_sfx("perils")
            elif peril == 2:
                self._log(f"PERILS! DAEMONIC POSSESSION AMPLIFIES {caster.name}'S POWER!")
                return False  # doubled power, execute normally
            elif peril == 3:
                self._log(f"PERILS! A DAEMON MANIFESTS!")
                # Spawn a random daemon
            return peril not in (2,)
        return False

    def do_use_item(self, user, item_data, targets):
        effect = item_data.get("effect")
        val    = item_data.get("value", 0)
        self.party.remove_item(item_data["id"])

        if effect == "heal":
            for t in targets:
                t.heal(val)
                self._log(f"{user.name} USES {item_data['name']}! {t.name} +{val}HP!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "heal_all":
            for m in self.alive_party():
                m.heal(val)
            self._log(f"{user.name} USES {item_data['name']}! PARTY +{val}HP!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "full_heal":
            for t in targets:
                t.heal(t.max_hp)
                self._log(f"{user.name} USES {item_data['name']}! {t.name} FULLY RESTORED!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "revive":
            for t in targets:
                if not t.alive:
                    t.hp = max(1, int(t.max_hp * val))
                    t.alive = True
                    self._log(f"{t.name} REVIVED WITH {t.hp}HP! THE EMPEROR WILLS IT!")
            if self.audio:
                self.audio.play_sfx("heal")

        elif effect == "cure_status":
            for t in targets:
                t.clear_status(item_data.get("value"))
                self._log(f"{t.name}'S AFFLICTION PURGED!")

        elif effect == "cure_all_status":
            for t in targets:
                t.clear_status()
            self._log(f"ALL AFFLICTIONS PURGED!")

        elif effect == "damage_all":
            for e in self.alive_enemies():
                actual = e.take_damage(val, ignore_def=True)
                if not e.alive:
                    self._on_enemy_death(e)
            self._log(f"{user.name} HURLS {item_data['name']}! ALL ENEMIES TAKE {val}HP!")
            if self.audio:
                self.audio.play_sfx("hit")

        elif effect == "damage_one_ignore_def":
            for t in targets:
                actual = t.take_damage(val, ignore_def=True)
                self._log(f"{user.name} USES {item_data['name']}! {t.name} TAKES {val}HP!")
                if not t.alive:
                    self._on_enemy_death(t)

        elif effect == "restore_resource":
            res_type = item_data.get("resource")
            for t in targets:
                if res_type == "warp":
                    t.restore_warp(val)
                    self._log(f"{t.name} WARP CHARGES RESTORED +{val}!")
                    self.party.adjust_corruption(1)
                    self._log("RAW WARP DUST STAINS THE SOUL. CORRUPTION +1.")
                elif res_type == "faith":
                    t.restore_faith(val)
                    self._log(f"{t.name} ACTS OF FAITH RESTORED +{val}!")

    def do_flee(self, party):
        alive_e = self.alive_enemies()
        avg_party_agi = sum(c.agi_total for c in self.alive_party()) / max(1, len(self.alive_party()))
        avg_enemy_agi = sum(e.agi for e in alive_e) / max(1, len(alive_e))
        chance = (avg_party_agi / max(1, avg_enemy_agi)) * 0.5

        if self.party.has_commissar() and self.party.morale < 3:
            self.commissar_retreat_block = True
            self._log(f"THE COMMISSAR FORBIDS RETREAT! THERE IS ONLY FORWARD!")
            return False

        if random.random() < chance:
            self._log(f"THE WARBAND WITHDRAWS! TACTICAL RETREAT SUCCESSFUL!")
            self.result = BattleResult.FLED
            return True
        else:
            self._log(f"RETREAT FAILS! ENEMIES CAPITALISE!")
            # All enemies attack the flee-er
            flee_target = self.alive_party()[0]
            for e in alive_e:
                action = {"type": "attack", "target": flee_target}
                self._execute_enemy_action(e, action)
            return False

    def _on_enemy_death(self, enemy):
        self.xp_gained   += enemy.xp
        self.gelt_gained += enemy.gelt
        item_db = loader.items()
        drops = enemy.roll_drops(item_db)
        self.items_gained.extend(drops)
        self.party.adjust_morale(1)
        # Check for splits
        if enemy.splits_on_death:
            from entities.enemy import Enemy
            edata = loader.enemies()
            if enemy.splits_on_death in edata:
                for _ in range(2):
                    e = Enemy(dict(edata[enemy.splits_on_death], id=enemy.splits_on_death))
                    e.alive = True
                    self.enemies.append(e)
                self._log(f"THE PINK HORROR SPLITS INTO TWO BLUE HORRORS!")
                self._build_turn_order()

    def _execute_enemy_action(self, enemy, action):
        if not enemy.alive:
            return
        atype = action.get("type")
        if atype == "skip":
            self._log(f"{enemy.name} IS INCAPACITATED!")
            return
        if atype == "taunt":
            self._log(f"{enemy.name} POSTURES MENACINGLY!")
            return
        if atype == "boss_ability":
            self._execute_boss_ability(enemy, action["ability"])
            return
        if atype == "attack":
            target = action.get("target")
            if target is None or not target.alive:
                alive = self.alive_party()
                if not alive:
                    return
                target = random.choice(alive)

            hit = random.randint(1, 100) <= 80
            if not hit:
                self._log(f"{enemy.name} {enemy.get_attack_verb()} {target.name} — MISS!")
                return

            str_mult = action.get("str_mult", 1.0)
            base_dmg = int(enemy.str * str_mult)
            if "str_reduce" in enemy.debuffs:
                reduce, _ = enemy.debuffs["str_reduce"]
                base_dmg = int(base_dmg * (1 - reduce))
            dmg = max(1, base_dmg - (target.def_total // 2) + random.randint(1, 6))

            # Party buff: damage reduction
            pb = self.party_buffs.get(target.name, {})
            if "dmg_reduce" in pb:
                val, turns = pb["dmg_reduce"]
                dmg = int(dmg * (1 - val))
            if "phys_immune" in pb:
                self._log(f"{target.name}'S IRON ARM DEFLECTS THE BLOW!")
                return

            # Sister Miraculous Intervention check
            if dmg >= target.hp and not self.sister_miraculous_used:
                sister = next((m for m in self.alive_party() if m.class_id == CLASS_SISTER), None)
                if sister:
                    chance = sister.faith_total / 100.0
                    if sister.promoted or random.random() < chance:
                        self.sister_miraculous_used = True
                        target.hp = 1
                        target.alive = True
                        self._log(f"MIRACULOUS INTERVENTION! THE EMPEROR'S WILL IS NOT YET DONE! {target.name} LIVES!")
                        if self.audio:
                            self.audio.play_sfx("heal")
                        return

            actual, negated = target.take_damage(dmg)
            if negated:
                self._log(f"{target.name}'S IRON HALO NEGATES {enemy.name}'S ATTACK!")
                return

            self._log(f"{enemy.name} {enemy.get_attack_verb()} {target.name}! -{actual}HP!")
            if self.audio:
                self.audio.play_sfx("hit")

            if not target.alive:
                self._log(f"{target.name} HAS FALLEN! NO...")
                self.party.adjust_morale(-2)
                if self.audio:
                    self.audio.play_sfx("death")

            # Status infliction
            status = action.get("status")
            if status is not None:
                pb_immune = pb.get("full_status_immune")
                if not pb_immune:
                    if target.apply_status(status):
                        self._log(f"{target.name} SUFFERS {STATUS_NAMES[status]}!")

    def _execute_boss_ability(self, enemy, ability):
        alive = self.alive_party()
        if not alive:
            return

        def hit_all(mult, cry):
            self._log(cry)
            for t in alive:
                dmg = max(1, int(enemy.str * mult) + random.randint(5, 15))
                actual, negated = t.take_damage(dmg)
                if negated:
                    self._log(f"{t.name}'S IRON HALO HOLDS!")
                    continue
                self._log(f"{t.name} TAKES {actual}HP!")
                if not t.alive:
                    self._log(f"{t.name} HAS FALLEN!")
                    self.party.adjust_morale(-2)

        if ability == "waaagh_charge":
            hit_all(1.2, f"{enemy.name} WAAAGH!-CHARGES THE ENTIRE WARBAND!")

        elif ability == "waaagh_prime":
            enemy.str = int(enemy.str * 1.1)
            hit_all(1.4, f"{enemy.name} BELLOWS DA WAAAGH! PRIME! THE FORTRESS SHAKES!")

        elif ability == "stampede":
            hit_all(1.4, f"{enemy.name} STAMPEDES THROUGH THE WARBAND!")

        elif ability == "unstoppable_waaagh":
            t = random.choice(alive)
            dmg = max(1, int(enemy.str * 2.2) + random.randint(10, 25))
            actual, negated = t.take_damage(dmg)
            if negated:
                self._log(f"UNSTOPPABLE WAAAGH! — BUT {t.name}'S IRON HALO HOLDS!")
            else:
                self._log(f"UNSTOPPABLE WAAAGH! {enemy.name} OBLITERATES {t.name} FOR {actual}HP!")
                if not t.alive:
                    self._log(f"{t.name} HAS FALLEN!")
                    self.party.adjust_morale(-2)

        elif ability == "ead_butt":
            t = random.choice(alive)
            if t.apply_status(STATUS_CATATONIC, 2):
                self._log(f"{enemy.name} 'EAD-BUTTS {t.name}! STUNNED!")
            else:
                self._log(f"{enemy.name} 'EAD-BUTTS {t.name} — BUT {t.name} SHRUGS IT OFF!")

        elif ability == "call_da_boyz":
            if self.party.get_flag(FLAG_ROK_CLEAR):
                self._log(f"{enemy.name} CALLS FOR DA BOYZ... DA BEACON IS DEAD. NO ONE ANSWERS.")
            elif len(self.alive_enemies()) >= 5:
                self._log(f"{enemy.name} CALLS FOR DA BOYZ — THE ROOM IS ALREADY FULL OF ORKS!")
            else:
                from entities.enemy import Enemy
                edata = loader.enemies()
                if "ork_boy_slugga" in edata:
                    for _ in range(2):
                        self.enemies.append(Enemy(dict(edata["ork_boy_slugga"], id="ork_boy_slugga")))
                    self._log(f"{enemy.name} CALLS DA BOYZ! TWO SLUGGA BOYZ CRASH THROUGH THE WALL!")
                    self._build_turn_order()

        elif ability == "painboy_fix":
            heal = max(50, enemy.max_hp // 4)
            enemy.hp = min(enemy.max_hp, enemy.hp + heal)
            enemy.status = STATUS_NONE
            self._log(f"{enemy.name} JABS HIMSELF WITH A MYSTERY SYRINGE! HEALED {heal}HP!")

        elif ability == "squig_injection":
            t = random.choice(alive)
            dmg = max(1, int(enemy.str * 0.8))
            actual, _ = t.take_damage(dmg)
            self._log(f"{enemy.name} INJECTS {t.name} WITH SQUIG EXTRACT! -{actual}HP!")
            if t.alive and t.apply_status(STATUS_PLAGUE, 3):
                self._log(f"{t.name} SUFFERS {STATUS_NAMES[STATUS_PLAGUE]}!")

        elif ability == "go_fasta":
            self._log(f"{enemy.name} SHOUTS 'GO FASTA!' AND STRIKES TWICE!")
            for _ in range(2):
                targets = self.alive_party()
                if not targets:
                    break
                self._execute_enemy_action(enemy, {"type": "attack", "target": random.choice(targets)})

        elif ability == "gorks_favor" or ability == "gork_morka_blessing":
            heal = max(100, enemy.max_hp // 5)
            enemy.hp = min(enemy.max_hp, enemy.hp + heal)
            enemy.str += 3
            self._log(f"GORK AND MORK SMILE UPON {enemy.name}! HEALED {heal}HP! HIS RAGE GROWS!")

        elif ability == "iron_hide":
            enemy.defense += 8
            self._log(f"{enemy.name}'S MEGA-ARMOUR PLATES SLAM SHUT! IRON HIDE!")

        elif ability == "shake_off":
            enemy.status = STATUS_NONE
            enemy.status_turns = 0
            enemy.debuffs = {}
            self._log(f"{enemy.name} SHAKES OFF EVERY AFFLICTION WITH A ROAR!")

        elif ability == "phase2_transition":
            self._log(f"{enemy.name}'S MEGA-ARMOUR CRACKS... BUT DA WAAAGH! BURNS BRIGHTER!")

    def tick_vortex(self):
        if self.vortex_turns > 0:
            for e in self.alive_enemies():
                actual = e.take_damage(self.vortex_damage, ignore_def=True)
                self._log(f"THE VORTEX TEARS AT {e.name}! -{actual}HP!")
                if not e.alive:
                    self._on_enemy_death(e)
            self.vortex_turns -= 1

    def tick_buff_timers(self):
        for name in list(self.party_buffs.keys()):
            buf = self.party_buffs[name]
            to_del = []
            for k, (v, t) in buf.items():
                new_t = t - 1
                if new_t <= 0:
                    to_del.append(k)
                else:
                    buf[k] = (v, new_t)
            for k in to_del:
                del buf[k]

    def tick_enemy_debuffs(self):
        for e in self.alive_enemies():
            to_del = []
            for k, (v, t) in e.debuffs.items():
                new_t = t - 1
                if new_t <= 0:
                    to_del.append(k)
                    if k == "def_stripped" and "def_stripped" in e.buffs:
                        e.defense = e.buffs["def_stripped"][0]
                        del e.buffs["def_stripped"]
                else:
                    e.debuffs[k] = (v, new_t)
            for k in to_del:
                if k in e.debuffs:
                    del e.debuffs[k]

    def end_of_round(self):
        # Status ticks
        for m in self.alive_party():
            msgs = m.tick_status()
            for msg in msgs:
                self._log(msg)
        for e in self.alive_enemies():
            msgs = e.tick_status()
            for msg in msgs:
                self._log(msg)

        # Corruption effects
        if self.party.corruption >= 25:
            for m in self.alive_party():
                if random.random() < 0.1:
                    status = random.choice([STATUS_WARP_MAD, STATUS_ROUT, STATUS_PSY_STATIC])
                    if m.apply_status(status, 1):
                        self._log(f"CORRUPTION OVERWHELMS {m.name}! {STATUS_NAMES[status]}!")

        self.tick_vortex()
        self.tick_buff_timers()
        self.tick_enemy_debuffs()
        self.turn_num += 1
        self._build_turn_order()

    def check_end(self):
        if self.result:
            return self.result
        if not self.alive_party():
            self.result = BattleResult.DEFEAT
        elif not self.alive_enemies():
            self.result = BattleResult.VICTORY
            self._distribute_rewards()
        return self.result

    def _distribute_rewards(self):
        self.levelups = []
        for m in self.alive_party():
            old = {"HP": m.max_hp, "STR": m.base_str, "DEF": m.base_def,
                   "AGI": m.base_agi, "FAITH": m.base_faith, "PSY": m.base_psy}
            if m.gain_xp(self.xp_gained):
                new = {"HP": m.max_hp, "STR": m.base_str, "DEF": m.base_def,
                       "AGI": m.base_agi, "FAITH": m.base_faith, "PSY": m.base_psy}
                self.levelups.append((m, old, new))
        self.party.add_gelt(self.gelt_gained)
        for item in self.items_gained:
            self.party.add_item(item["id"])
        # Morale boost on victory
        self.party.adjust_morale(1)
