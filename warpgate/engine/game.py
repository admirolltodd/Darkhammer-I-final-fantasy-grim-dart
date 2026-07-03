import pygame
import random
import time
from constants import *
from engine.renderer    import Renderer
from engine.input_handler import InputHandler
from engine.audio_manager import AudioManager
from engine import save_manager
from entities.character import Character
from entities.party     import Party
from entities.enemy     import Enemy
from combat.battle      import Battle, BattleResult
from world.world_map    import build_world, LOCATIONS
from world.dungeon      import DungeonFloor, DUNGEON_CONFIGS
from world.town         import Town, SHOPS
from data               import loader

CLASS_SELECT_DEFS = {
    CLASS_ASTARTES: {
        "name": "ASTARTES",
        "short_desc": "TANK / DAMAGE",
        "lore": "THE EMPEROR'S FINEST. GENE-SEED WARRIORS\nBORN TO FIGHT AND DIE IN HIS NAME.",
    },
    CLASS_INQUISITOR: {
        "name": "INQUISITOR",
        "short_desc": "HYBRID / VERSATILE",
        "lore": "THEY ANSWER TO NO ONE BUT THE EMPEROR.\nHERESTY IS EVERYWHERE. THEY KNOW THIS.",
    },
    CLASS_PSYKER: {
        "name": "PSYKER",
        "short_desc": "MAGE / WARP",
        "lore": "THEY TOUCH THE WARP AND DRAG POWER BACK.\nUSUALLY WITHOUT BEING CONSUMED.",
    },
    CLASS_SISTER: {
        "name": "SISTER OF BATTLE",
        "short_desc": "HEALER / FAITH",
        "lore": "ARMOURED IN CERAMITE AND FAITH.\nTHE EMPEROR PROTECTS. STATISTICALLY.",
    },
    CLASS_TECH_PRIEST: {
        "name": "TECH-PRIEST",
        "short_desc": "UTILITY / REPAIR",
        "lore": "FLESH REPLACED WITH METAL UNTIL\nTHEY ARE UNSURE WHICH PARTS ARE THEM.",
    },
    CLASS_COMMISSAR: {
        "name": "COMMISSAR",
        "short_desc": "MORALE / SUPPORT",
        "lore": "THEY INSPIRE TROOPS. BY SHOOTING\nCOWARDS. IT WORKS. MOSTLY.",
    },
}

STATE_TITLE        = "TITLE"
STATE_CLASS_SELECT = "CLASS_SELECT"
STATE_WORLD        = "WORLD"
STATE_TOWN         = "TOWN"
STATE_DUNGEON      = "DUNGEON"
STATE_BATTLE       = "BATTLE"
STATE_MENU         = "MENU"
STATE_DIALOGUE     = "DIALOGUE"
STATE_SAVE         = "SAVE"
STATE_LOAD         = "LOAD"
STATE_STATUS       = "STATUS"
STATE_SHOP         = "SHOP"
STATE_INVENTORY    = "INVENTORY"
STATE_LEVEL_UP     = "LEVEL_UP"
STATE_GAME_OVER    = "GAME_OVER"
STATE_VICTORY      = "VICTORY"
STATE_ENDING       = "ENDING"
STATE_BATTLE_FADE  = "BATTLE_FADE"

MAIN_MENU_OPTIONS = ["BATTLE RECORDS", "WAR GEAR", "PSYKER RITES", "SUPPLIES", "SAVE", "ABANDON HOPE"]
# Menu options fit the 64px columns of the battle command bar (max 7 chars)
BATTLE_MENU_TOP   = ["ENGAGE", "RITES", "GEAR", "RETREAT"]

class Game:
    def __init__(self, screen):
        self.screen   = screen
        self.renderer = Renderer()
        self.input    = InputHandler()
        self.audio    = AudioManager()
        self.clock    = pygame.time.Clock()

        self.state    = STATE_TITLE
        self.prev_state = None
        self.party    = None
        self.world    = None
        self.locations= []
        self.current_town    = None
        self.current_dungeon = None
        self.current_dungeon_id = None

        self.battle   = None
        self.battle_result_shown = False

        self.item_db  = loader.items()
        self.enemy_db = loader.enemies()

        self.tick     = 0
        self.blink    = False
        self.blink_timer = 0

        # Class selection state
        self.cs_cursor    = 0
        self.cs_slot      = 0
        self.cs_selections= [None] * MAX_PARTY
        self.cs_names     = ["URIEL", "HAVELOCK", "ZARAPHEL", "GAUNT"]

        # Menu state
        self.menu_selected = 0
        self.menu_sub_open = False
        self.menu_sub_items= []
        self.menu_sub_sel  = 0

        # Battle UI state
        self.battle_menu = {
            "options": BATTLE_MENU_TOP,
            "selected": 0,
            "sub": False,
            "sub_options": [],
            "sub_selected": 0,
        }
        self.battle_phase = "select_char"
        self.battle_char_idx = 0
        self.battle_target_enemies = []
        self.battle_target_allies  = []
        self.battle_selected_power = None
        self.battle_selected_item  = None
        self.battle_waiting_enemy  = False
        self.battle_enemy_delay    = 0
        self.battle_action_queue   = []
        self.battle_pending_action = None   # deferred action awaiting target pick
        self.pending_battle        = None   # battle deferred until dialogue closes
        self.fade_tick             = 0      # battle intro transition timer
        self.fade_battle           = None   # (enemies, is_boss, boss_id, zone)
        self.fade_base_state       = None   # scene rendered under the fade
        self.damage_floats         = []
        self.float_timer           = 0
        self.levelup_queue         = []
        self.levelup_old_stats     = {}
        self.levelup_new_stats     = {}

        # Dialogue state
        self.dialogue_pages  = []
        self.dialogue_page   = 0
        self.dialogue_npc    = ""
        self.dialogue_port   = "??"
        self.dialogue_return = None

        # Story state
        self.story_sequence  = []
        self.story_page      = 0
        self.story_return    = None

        # Ending state
        self.ending_choice = None
        self.ending_tick   = 0
        self.ending_shown  = False
        self.ending_cursor = 0

        # Shop state
        self.shop_items    = []
        self.shop_selected = 0
        self.shop_id       = None

        # Inventory state
        self.inv_selected  = 0

        # Status screen
        self.status_char_idx = 0

        # Save screen
        self.save_slots    = [None, None, None]
        self.save_selected = 0

        # Level-up display
        self.levelup_char  = None
        self.levelup_tick  = 0

        # Encounter step counter
        self.steps_since_encounter = 0

        self.session_start = time.time()

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self):
        self.audio.play_music("title")
        while True:
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit()
                    return
            self.input.update(events)
            self.tick += 1
            self.blink_timer += 1
            if self.blink_timer >= 30:
                self.blink = not self.blink
                self.blink_timer = 0

            if self.party:
                self.party.playtime = int(time.time() - self.session_start)

            self._update()
            self._render()
            self.clock.tick(FPS)

    def _update(self):
        # Reset per-frame movement flag so walk animation idles when standing still
        if self.party:
            self.party.moving = False
        s = self.state
        if s == STATE_TITLE:        self._update_title()
        elif s == STATE_CLASS_SELECT: self._update_class_select()
        elif s == STATE_WORLD:      self._update_world()
        elif s == STATE_TOWN:       self._update_town()
        elif s == STATE_DUNGEON:    self._update_dungeon()
        elif s == STATE_BATTLE:     self._update_battle()
        elif s == STATE_MENU:       self._update_menu()
        elif s == STATE_DIALOGUE:   self._update_dialogue()
        elif s == STATE_SAVE:       self._update_save()
        elif s == STATE_LOAD:       self._update_load()
        elif s == STATE_STATUS:     self._update_status()
        elif s == STATE_SHOP:       self._update_shop()
        elif s == STATE_INVENTORY:  self._update_inventory()
        elif s == STATE_LEVEL_UP:   self._update_levelup()
        elif s == STATE_GAME_OVER:  self._update_gameover()
        elif s == STATE_VICTORY:    self._update_victory()
        elif s == STATE_ENDING:     self._update_ending()
        elif s == STATE_BATTLE_FADE: self._update_battle_fade()

    def _render(self):
        s = self.state
        if s == STATE_TITLE:
            self.renderer.render_title(self.blink, self.tick)
        elif s == STATE_CLASS_SELECT:
            self.renderer.render_class_select(CLASS_SELECT_DEFS, self.cs_selections,
                                               self.cs_slot, self.cs_cursor, self.tick)
        elif s == STATE_WORLD:
            self.renderer.render_world_map(self.world, self.party, self.tick)
            if self.state == STATE_DIALOGUE:
                self.renderer.render_dialogue(self.dialogue_npc, self.dialogue_port,
                                              self.dialogue_pages[self.dialogue_page],
                                              self.dialogue_page, len(self.dialogue_pages), self.blink)
        elif s == STATE_TOWN:
            self.renderer.render_town(self.current_town, self.party, self.tick)
            if self.dialogue_pages:
                self.renderer.render_dialogue(self.dialogue_npc, self.dialogue_port,
                                              self.dialogue_pages[self.dialogue_page],
                                              self.dialogue_page, len(self.dialogue_pages), self.blink)
        elif s == STATE_DUNGEON:
            self.renderer.render_dungeon(self.current_dungeon, self.party, self.tick)
        elif s == STATE_BATTLE:
            self.renderer.render_battle(self.battle, self.battle_menu, self.tick, self.damage_floats)
            if self.state == STATE_VICTORY:
                self.renderer.render_victory_screen(self.tick, self.battle.xp_gained,
                                                     self.battle.gelt_gained, self.battle.items_gained)
        elif s == STATE_MENU:
            if self.prev_state == STATE_WORLD:
                self.renderer.render_world_map(self.world, self.party, self.tick)
            elif self.prev_state == STATE_DUNGEON:
                self.renderer.render_dungeon(self.current_dungeon, self.party, self.tick)
            elif self.prev_state == STATE_TOWN:
                self.renderer.render_town(self.current_town, self.party, self.tick)
            self.renderer.render_main_menu(MAIN_MENU_OPTIONS, self.menu_selected, self.party)
        elif s == STATE_STATUS:
            self.renderer.render_status_screen(self.party.members[self.status_char_idx], 0)
        elif s == STATE_SHOP:
            items = [self.item_db[iid] for iid in self.shop_items if iid in self.item_db]
            self.renderer.render_shop(items, self.shop_selected, self.party)
        elif s == STATE_INVENTORY:
            self.renderer.render_inventory(list(self.party.inventory.items()),
                                           self.inv_selected, self.party, self.item_db)
        elif s == STATE_SAVE or s == STATE_LOAD:
            self._refresh_save_slots()
            mode = "SAVE" if s == STATE_SAVE else "LOAD"
            slot_info = []
            for si in self.save_slots:
                if si is None:
                    slot_info.append(None)
                else:
                    slot_info.append({
                        "location": si.get("location", "?"),
                        "corruption": si.get("corruption", 0),
                        "playtime": si.get("playtime", 0),
                        "party": si.get("party_summary", []),
                    })
            self.renderer.render_save_screen(slot_info, self.save_selected, mode)
        elif s == STATE_DIALOGUE:
            if self.prev_state in (STATE_WORLD, STATE_DUNGEON, STATE_TOWN):
                if self.prev_state == STATE_WORLD:
                    self.renderer.render_world_map(self.world, self.party, self.tick)
                elif self.prev_state == STATE_DUNGEON:
                    self.renderer.render_dungeon(self.current_dungeon, self.party, self.tick)
                elif self.prev_state == STATE_TOWN:
                    self.renderer.render_town(self.current_town, self.party, self.tick)
            self.renderer.render_dialogue(self.dialogue_npc, self.dialogue_port,
                                          self.dialogue_pages[self.dialogue_page],
                                          self.dialogue_page, len(self.dialogue_pages), self.blink)
        elif s == STATE_LEVEL_UP:
            self.renderer.render_level_up(self.levelup_char, self.levelup_old_stats, self.levelup_new_stats)
        elif s == STATE_GAME_OVER:
            self.renderer.render_game_over(self.tick)
        elif s == STATE_VICTORY:
            self.renderer.render_victory_screen(self.tick,
                                                 self.battle.xp_gained if self.battle else 0,
                                                 self.battle.gelt_gained if self.battle else 0,
                                                 self.battle.items_gained if self.battle else [])
        elif s == STATE_ENDING:
            rok = self.party.get_flag(FLAG_ROK_CLEAR) if self.party else False
            corr = self.party.corruption if self.party else 0
            self.renderer.render_ending(self.ending_choice, self.ending_tick,
                                        self.ending_cursor, rok, corr)
        elif s == STATE_BATTLE_FADE:
            self._render_field_scene(self.fade_base_state)
            self.renderer.render_battle_fade(self.fade_tick)

        self.renderer.present(self.screen)

    # ── State updates ──────────────────────────────────────────────────────────

    def _update_title(self):
        if self.input.pressed("confirm"):
            self.audio.play_sfx("confirm")
            self._goto(STATE_CLASS_SELECT)
        elif self.input.pressed("cancel"):
            # Load menu shortcut
            self._goto(STATE_LOAD)
            self.party = Party()  # dummy for load screen

    def _update_class_select(self):
        class_ids = list(CLASS_SELECT_DEFS.keys())
        if self.input.pressed("down"):
            self.cs_cursor = (self.cs_cursor + 1) % len(class_ids)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("up"):
            self.cs_cursor = (self.cs_cursor - 1) % len(class_ids)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("confirm"):
            self.cs_selections[self.cs_slot] = class_ids[self.cs_cursor]
            self.audio.play_sfx("confirm")
            if self.cs_slot < MAX_PARTY - 1:
                self.cs_slot += 1
            else:
                # Start game
                self._start_game()
        elif self.input.pressed("cancel"):
            if self.cs_slot > 0:
                self.cs_slot -= 1
                self.cs_selections[self.cs_slot] = None
            else:
                self._goto(STATE_TITLE)
                self.audio.play_music("title")

    def _start_game(self):
        self.party = Party()
        for i, cid in enumerate(self.cs_selections):
            if cid is not None:
                name = self.cs_names[i]
                c = Character(name, cid)
                # Give starting equipment
                self._give_starting_gear(c)
                self.party.add_member(c)
        self.party.add_item("stimm_injector", 5)
        self.party.add_item("frag_grenade", 2)
        self.party.add_item("antitox_shot", 2)

        self.world, self.locations = build_world()
        self.party.world_x = 5
        self.party.world_y = 5
        self.session_start = time.time()

        self._show_story_sequence(loader.story()["intro"], STATE_WORLD)
        self.audio.play_music("worldmap")

    def _give_starting_gear(self, char):
        from constants import CLASS_ASTARTES, CLASS_INQUISITOR, CLASS_PSYKER, CLASS_SISTER, CLASS_TECH_PRIEST, CLASS_COMMISSAR
        idb = self.item_db
        if char.class_id == CLASS_ASTARTES:
            char.equip(SLOT_MAIN, idb["bolt_pistol_mkiii"])
            char.equip(SLOT_BODY, idb["carapace_armour"])
        elif char.class_id == CLASS_INQUISITOR:
            char.equip(SLOT_MAIN, idb["bolt_pistol_mkiii"])
            char.equip(SLOT_BODY, idb["flak_armour"])
        elif char.class_id == CLASS_PSYKER:
            char.equip(SLOT_MAIN, idb["force_staff"])
            char.equip(SLOT_BODY, idb["psyker_robes"])
        elif char.class_id == CLASS_SISTER:
            char.equip(SLOT_MAIN, idb["laspistol_kantrael"])
            char.equip(SLOT_BODY, idb["flak_armour"])
        elif char.class_id == CLASS_TECH_PRIEST:
            char.equip(SLOT_MAIN, idb["omnissian_axe"])
            char.equip(SLOT_BODY, idb["mechanicus_robes"])
        elif char.class_id == CLASS_COMMISSAR:
            char.equip(SLOT_MAIN, idb["bolt_pistol_mkiii"])
            char.equip(SLOT_BODY, idb["flak_armour"])

    def _update_world(self):
        moved = False
        dx, dy = 0, 0
        if self.input.pressed("up"):     dy = -1
        elif self.input.pressed("down"): dy =  1
        elif self.input.pressed("left"): dx = -1
        elif self.input.pressed("right"):dx =  1

        if dx or dy:
            if dx ==  1: self.party.facing = "right"
            elif dx == -1: self.party.facing = "left"
            elif dy == -1: self.party.facing = "up"
            else:          self.party.facing = "down"
            nx = self.party.world_x + dx
            ny = self.party.world_y + dy
            if self.world.is_passable(nx, ny):
                self.party.world_x = nx
                self.party.world_y = ny
                self.party.moving = True
                self.world.mark_visited(nx, ny)
                moved = True
                self.steps_since_encounter += 1
                # Check encounter
                rate = self.world.encounter_rate(nx, ny)
                if rate > 0 and random.randint(1, rate) == 1:
                    self._start_encounter(self._get_world_zone(nx, ny))
                    return

        if self.input.pressed("confirm") or self.input.pressed("menu"):
            # Check location interaction
            tile = self.world.get_tile(self.party.world_x, self.party.world_y)
            if tile == T_TOWN:
                self._enter_town()
            elif tile == T_DUNGEON:
                self._enter_dungeon()
            elif tile == T_SHRINE:
                self._world_shrine()
            else:
                self._goto(STATE_MENU)

        if self.input.pressed("cancel"):
            self._goto(STATE_MENU)

        # Update location name
        for lx, ly, tid, name, ltype, lid in self.locations:
            if self.party.world_x == lx and self.party.world_y == ly:
                self.party.location = name
                break
        else:
            self.party.location = "ARMAGEDDON ASH WASTES"

    def _get_world_zone(self, x, y):
        zone_map = {
            "dungeon1": ZONE_ENCAMPMENT,
            "dungeon2": ZONE_FUNGAL_CAVES,
            "dungeon3": ZONE_MANUFACTORUM,
            "dungeon_void": ZONE_ROK,
            "dungeon_final": ZONE_IRON_FORTRESS,
        }
        for lx, ly, tid, name, ltype, lid in self.locations:
            if abs(x - lx) < 4 and abs(y - ly) < 4 and ltype == "dungeon":
                return zone_map.get(lid, ZONE_ASH_WASTES)
        if x > 40 or y > 40:
            return ZONE_IRON_FORTRESS
        if 18 <= x <= 28 and 18 <= y <= 32:
            return ZONE_FUNGAL_CAVES
        return ZONE_ASH_WASTES

    def _enter_town(self):
        tile = self.world.get_tile(self.party.world_x, self.party.world_y)
        # Find town
        for lx, ly, tid, name, ltype, lid in self.locations:
            if self.party.world_x == lx and self.party.world_y == ly and ltype == "town":
                town_id = lid
                self.current_town = Town(town_id)
                self.party.world_x = self.current_town.entry_pos[0]
                self.party.world_y = self.current_town.entry_pos[1]
                self.audio.play_sfx("door")
                self.audio.play_music("town")
                self._goto(STATE_TOWN)
                return

    def _enter_dungeon(self):
        for lx, ly, tid, name, ltype, lid in self.locations:
            if self.party.world_x == lx and self.party.world_y == ly and ltype == "dungeon":
                # Check if accessible
                if lid == "dungeon2" and not self.party.get_flag(FLAG_ENCAMPMENT_CLEAR):
                    self._show_dialogue("ADVANCE DENIED", "WL",
                                        ["THE FUNGAL CAVES ARE IMPASSABLE. CLEAR ORK ENCAMPMENT ALPHA FIRST."],
                                        STATE_WORLD)
                    return
                if lid == "dungeon3" and not self.party.get_flag(FLAG_CAVES_CLEAR):
                    self._show_dialogue("ADVANCE DENIED", "WL",
                                        ["THE MANUFACTORUM IS SWARMING. CLEAR THE FUNGAL CAVES FIRST."],
                                        STATE_WORLD)
                    return
                if lid == "dungeon_final" and not self.party.get_flag(FLAG_MANUFACTORUM_CLEAR):
                    self._show_dialogue("ADVANCE DENIED", "WL",
                                        ["THE IRON FORTRESS IS SEALED. DEFEAT MAD DOK GROTSNIK IN THE MANUFACTORUM FIRST."],
                                        STATE_WORLD)
                    return
                if lid == "dungeon_void" and not self.party.get_flag(FLAG_MANUFACTORUM_CLEAR):
                    self._show_dialogue("SEALED HULK", "WL",
                                        ["THE ROK'S HULL IS SEALED TIGHT. WHATEVER IS INSIDE, IT IS NOT READY TO BE FOUND.",
                                         "GROTSNIK'S RECORDS IN THE MANUFACTORUM MAY EXPLAIN WHAT THIS THING IS FOR."],
                                        STATE_WORLD)
                    return

                self.current_dungeon_id = lid
                cfg = DUNGEON_CONFIGS[lid]
                self.current_dungeon = DungeonFloor(lid, 1, cfg)
                self.party.world_x = self.current_dungeon.entrance[0]
                self.party.world_y = self.current_dungeon.entrance[1]
                self.audio.play_sfx("door")
                self.audio.play_music("dungeon")

                # Show intro text
                self._show_dialogue("INCOMING TRANSMISSION", "SY",
                                     [cfg["intro_text"]], STATE_DUNGEON)
                return

    def _world_shrine(self):
        self._show_dialogue("BATTLEFIELD SHRINE", "SH",
                            ["THE EMPEROR'S PRESENCE IS FELT EVEN HERE, ON ARMAGEDDON. YOUR PARTY IS RESTORED.",
                             "ARMAGEDDON WILL HOLD. IT MUST."],
                            STATE_WORLD)
        self.party.rest_at_shrine()
        self.audio.play_sfx("heal")

    def _update_town(self):
        dx, dy = 0, 0
        if self.input.pressed("up"):     dy = -1
        elif self.input.pressed("down"): dy =  1
        elif self.input.pressed("left"): dx = -1
        elif self.input.pressed("right"):dx =  1

        if dx or dy:
            if dx ==  1: self.party.facing = "right"
            elif dx == -1: self.party.facing = "left"
            elif dy == -1: self.party.facing = "up"
            else:          self.party.facing = "down"
            nx = self.party.world_x + dx
            ny = self.party.world_y + dy
            if self.current_town.is_passable(nx, ny):
                self.party.world_x = nx
                self.party.world_y = ny
                self.party.moving = True

        if self.input.pressed("confirm"):
            # Check NPC
            npc = self.current_town.get_npc_at(self.party.world_x, self.party.world_y)
            if npc:
                pages = npc.dialogue
                # Flag-aware dialogue: first matching flag wins (most recent first)
                for flag, alt_pages in getattr(npc, "flag_dialogue", None) or []:
                    if self.party.get_flag(flag):
                        pages = alt_pages
                        break
                # Refugee quest payoff: family rescued when the caves were cleared
                if (getattr(npc, "quest", None) == "refugee_family"
                        and self.party.get_flag(FLAG_CAVES_CLEAR)
                        and not self.party.get_flag(FLAG_REFUGEE_REWARD)):
                    self.party.set_flag(FLAG_REFUGEE_REWARD)
                    self.party.add_gelt(300)
                    self.party.adjust_morale(2)
                    pages = ["YOU FOUND THEM. THE UNDERTUNNELS — THEY WERE SHELTERING FROM THE SQUIGGOTH.",
                             "MY DAUGHTER IS ALIVE. MY WHOLE FAMILY IS ALIVE.",
                             "TAKE THIS. ALL OUR SAVINGS. IT'S NOTHING NEXT TO WHAT YOU GAVE US.",
                             "(RECEIVED 300 GELT. WARBAND MORALE RISES.)"]
                    self.audio.play_sfx("heal")
                self._show_dialogue(npc.name, npc.portrait, pages, STATE_TOWN)
                return
            # Check door / shrine
            tile = self.current_town.get_tile(self.party.world_x, self.party.world_y)
            if tile == T_SHRINE:
                self.party.rest_at_shrine()
                self._show_dialogue("IMPERIAL SHRINE", "SH",
                                    ["THE EMPEROR SEES YOUR SERVICE ON ARMAGEDDON. PARTY FULLY RESTORED."], STATE_TOWN)
                self.audio.play_sfx("heal")
            elif tile == T_DOOR:
                # Open shop
                shop_id = self.current_town.shop_id
                if shop_id:
                    self._open_shop(shop_id)
            return

        if self.input.pressed("cancel") or self.input.pressed("menu"):
            # Check if at exit (bottom of town)
            if self.party.world_y >= self.current_town.height - 2:
                # Return to world map
                for lx, ly, tid, name, ltype, lid in self.locations:
                    if name == self.current_town.name:
                        self.party.world_x = lx
                        self.party.world_y = ly
                        break
                self.current_town = None
                self.audio.play_music("worldmap")
                self._goto(STATE_WORLD)
            else:
                self._goto(STATE_MENU)

    def _update_dungeon(self):
        dx, dy = 0, 0
        if self.input.pressed("up"):     dy = -1
        elif self.input.pressed("down"): dy =  1
        elif self.input.pressed("left"): dx = -1
        elif self.input.pressed("right"):dx =  1

        if dx or dy:
            if dx ==  1: self.party.facing = "right"
            elif dx == -1: self.party.facing = "left"
            elif dy == -1: self.party.facing = "up"
            else:          self.party.facing = "down"
            nx = self.party.world_x + dx
            ny = self.party.world_y + dy
            if self.current_dungeon.is_passable(nx, ny):
                self.party.world_x = nx
                self.party.world_y = ny
                self.party.moving = True
                self.current_dungeon.mark_visited(nx, ny)

                # Random encounter — roughly one fight per 7 steps
                if random.randint(1, 7) == 1:
                    self._start_encounter(self.current_dungeon.zone, self.current_dungeon.scale)
                    return

                # Check tile
                tile = self.current_dungeon.get_tile(nx, ny)
                if tile == T_CHEST:
                    self._open_chest(nx, ny)
                elif tile == T_SHRINE:
                    self._dungeon_shrine()
                elif tile == T_DOOR:
                    self._dungeon_door(nx, ny)

        if self.input.pressed("cancel") or self.input.pressed("menu"):
            self._goto(STATE_MENU)

    def _dungeon_shrine(self):
        self.party.rest_at_shrine()
        self._show_dialogue("SERVO-SKULL RELAY", "SK",
                            ["RELAY POINT ACTIVE. PROGRESS RECORDED. PARTY RESTORED."],
                            STATE_DUNGEON)
        self.audio.play_sfx("heal")

    def _dungeon_door(self, x, y):
        # Check if this is the exit
        if (x, y) == self.current_dungeon.exit_pos:
            cfg = DUNGEON_CONFIGS[self.current_dungeon_id]
            cur_floor = self.current_dungeon.floor
            total_floors = cfg["floors"]

            if cur_floor < total_floors:
                # Next floor
                self.current_dungeon = DungeonFloor(self.current_dungeon_id, cur_floor + 1, cfg)
                self.party.world_x = self.current_dungeon.entrance[0]
                self.party.world_y = self.current_dungeon.entrance[1]
                self.audio.play_sfx("door")
                self._show_dialogue("DEEPER INTO DARKNESS", "SY",
                                    [f"FLOOR {cur_floor + 1} OF {total_floors}.",
                                     "THERE IS ALWAYS WORSE BELOW."], STATE_DUNGEON)
            else:
                # Boss fight or key item
                boss_id = cfg.get("boss")
                if boss_id and boss_id in self.enemy_db:
                    edata = dict(self.enemy_db[boss_id], id=boss_id)
                    boss = Enemy(edata)
                    self._start_boss_fight(boss, boss_id)
                else:
                    # No boss, collect key item
                    key_id = cfg.get("key_item")
                    if key_id:
                        self.party.add_item(key_id)
                        self._complete_dungeon()

    def _start_boss_fight(self, boss, boss_id):
        # Ghazghkull addresses the warband from his throne before the fight.
        # Battle is deferred until the speech finishes (see _update_dialogue).
        if boss_id == "ghazghkull_p1" and not self.party.get_flag(FLAG_GHAZ_SPEECH):
            self.party.set_flag(FLAG_GHAZ_SPEECH)
            self.pending_battle = ([boss], True, boss_id)
            self._show_story_sequence(loader.story()["before_final_boss"], STATE_DUNGEON)
            return
        self._begin_battle_fade([boss], is_boss=True, boss_id=boss_id)

    def _open_chest(self, x, y):
        if self.current_dungeon.open_chest(x, y):
            # Generate loot
            loot = random.choice([
                ("gelt", random.randint(50, 200)),
                ("item", random.choice(["stimm_injector", "frag_grenade", "sacred_ungent",
                                        "antitox_shot", "warp_dust", "krak_grenade"])),
                ("xp", random.randint(30, 100)),
            ])
            if loot[0] == "gelt":
                self.party.add_gelt(loot[1])
                self._show_dialogue("CHEST", "CH",
                                    [f"FOUND {loot[1]} THRONE GELT IN THE RUINS."], STATE_DUNGEON)
            elif loot[0] == "item":
                iname = self.item_db.get(loot[1], {}).get("name", loot[1])
                self.party.add_item(loot[1])
                self._show_dialogue("CHEST", "CH",
                                    [f"RECOVERED: {iname}."], STATE_DUNGEON)
            elif loot[0] == "xp":
                for m in self.party.alive_members:
                    old = {"HP": m.max_hp, "STR": m.base_str, "DEF": m.base_def,
                           "AGI": m.base_agi, "FAITH": m.base_faith, "PSY": m.base_psy}
                    leveled = m.gain_xp(loot[1])
                    if leveled:
                        new = {"HP": m.max_hp, "STR": m.base_str, "DEF": m.base_def,
                               "AGI": m.base_agi, "FAITH": m.base_faith, "PSY": m.base_psy}
                        self.levelup_queue.append((m, old, new))
                self._show_dialogue("CHEST", "CH",
                                    [f"FOUND A BATTLE-RECORD TOME. PARTY GAINS {loot[1]} XP."], STATE_DUNGEON)
            self.audio.play_sfx("chest")

    def _complete_dungeon(self):
        did = self.current_dungeon_id
        flag_map = {
            "dungeon1": FLAG_ENCAMPMENT_CLEAR,
            "dungeon2": FLAG_CAVES_CLEAR,
            "dungeon3": FLAG_MANUFACTORUM_CLEAR,
            "dungeon_void": FLAG_ROK_CLEAR,
        }
        if did in flag_map:
            self.party.set_flag(flag_map[did])

        key_id = DUNGEON_CONFIGS[did].get("key_item")
        if key_id:
            iname = self.item_db.get(key_id, {}).get("name", key_id)
            self._show_dialogue("MISSION COMPLETE", "SY",
                                [f"RECOVERED: {iname}.", "THE WARBAND WITHDRAWS. FOR NOW."],
                                STATE_WORLD)

        # Return to world
        for lx, ly, tid, name, ltype, lid in self.locations:
            if lid == did:
                self.party.world_x = lx
                self.party.world_y = ly
                break
        self.current_dungeon = None
        self.current_dungeon_id = None
        self.audio.play_music("worldmap")
        self._goto(STATE_WORLD)

    # ── Battle ─────────────────────────────────────────────────────────────────

    def _start_encounter(self, zone, scale=1.0):
        zone_enemies = {
            ZONE_ASH_WASTES:    ["gretchin", "ork_boy_slugga", "ork_boy_shoota",
                                 "stormboy", "warbike_ork", "flash_git", "kommando"],
            ZONE_ENCAMPMENT:    ["ork_boy_slugga", "ork_boy_shoota", "stormboy",
                                 "ork_nob", "weirdboy", "ork_squig"],
            ZONE_FUNGAL_CAVES:  ["weirdboy", "kommando", "ork_squig", "fungus_beast"],
            ZONE_MANUFACTORUM:  ["ork_nob", "ork_meganob", "weirdboy", "big_mek", "deff_dread"],
            ZONE_IRON_FORTRESS: ["ork_meganob", "big_mek", "deff_dread", "flash_git"],
            ZONE_ROK:           ["flash_git", "ork_nob", "ork_meganob", "warbike_ork"],
        }
        pool = zone_enemies.get(zone, ["gretchin"])
        count = random.randint(1, min(4, 1 + len(pool) // 2))
        enemies = []
        for _ in range(count):
            eid = random.choice(pool)
            edata = dict(self.enemy_db[eid], id=eid)
            # Group sizes
            if "group_size" in edata:
                gs = edata["group_size"]
                gcount = random.randint(gs[0], gs[1])
                for _ in range(gcount):
                    enemies.append(Enemy(edata, scale))
                break
            else:
                enemies.append(Enemy(edata, scale))
        self._begin_battle_fade(enemies, zone=zone)

    def _begin_battle_fade(self, enemies, is_boss=False, boss_id=None, zone=None):
        """Flash + iris-wipe transition, then the battle starts."""
        base = self.state if self.state in (STATE_WORLD, STATE_TOWN, STATE_DUNGEON) \
            else (self.prev_state if self.prev_state in (STATE_WORLD, STATE_TOWN, STATE_DUNGEON)
                  else STATE_WORLD)
        self.fade_base_state = base
        self.fade_battle = (enemies, is_boss, boss_id, zone)
        self.fade_tick = 0
        self.audio.play_sfx("perils")
        self._goto(STATE_BATTLE_FADE)

    def _update_battle_fade(self):
        self.fade_tick += 1
        if self.fade_tick >= Renderer.BATTLE_FADE_LEN:
            enemies, is_boss, boss_id, zone = self.fade_battle
            self.fade_battle = None
            self._start_battle(enemies, is_boss=is_boss, boss_id=boss_id, zone=zone)

    def _render_field_scene(self, state):
        if state == STATE_TOWN and self.current_town:
            self.renderer.render_town(self.current_town, self.party, self.tick)
        elif state == STATE_DUNGEON and self.current_dungeon:
            self.renderer.render_dungeon(self.current_dungeon, self.party, self.tick)
        else:
            self.renderer.render_world_map(self.world, self.party, self.tick)

    def _start_battle(self, enemies, is_boss=False, boss_id=None, zone=None):
        self.audio.play_music("boss" if is_boss else "battle")
        self.battle = Battle(self.party, enemies, self.audio)
        if zone is None:
            zone = self.current_dungeon.zone if self.current_dungeon else ZONE_ASH_WASTES
        self.battle.zone = zone
        self.battle_boss_id = boss_id
        self.battle_is_boss = is_boss
        self.battle_phase   = "select_char"
        self.battle_char_idx = self._next_alive_char(-1)
        self.battle_menu["selected"] = 0
        self.battle_menu["sub"] = False
        self.battle_menu["target_mode"] = None
        self.battle_menu["target_idx"] = 0
        self.battle_pending_action = None
        self.battle_waiting_enemy = False
        self.battle_result_shown = False
        self.damage_floats = []
        self._goto(STATE_BATTLE)
        # Post-battle "return to field" logic reads prev_state; make sure it
        # points at the field scene, not the fade interstitial
        if self.prev_state == STATE_BATTLE_FADE:
            self.prev_state = self.fade_base_state or STATE_WORLD

    def _next_alive_char(self, current):
        members = self.party.members
        for i in range(len(members)):
            idx = (current + 1 + i) % len(members)
            if members[idx].alive and members[idx].can_act():
                return idx
        return 0

    def _update_battle(self):
        if self.battle.result:
            self._handle_battle_result()
            return

        alive_e = self.battle.alive_enemies()
        alive_p = self.battle.alive_party()

        if not alive_p:
            self.battle.result = BattleResult.DEFEAT
            return
        if not alive_e:
            self.battle.result = BattleResult.VICTORY
            self.battle._distribute_rewards()
            return

        # Enemy turn
        if self.battle_waiting_enemy:
            self.battle_enemy_delay -= 1
            if self.battle_enemy_delay <= 0:
                self._execute_next_enemy_action()
            return

        # Player menu
        char = self.party.members[self.battle_char_idx]
        if not char.alive or not char.can_act():
            self.battle_char_idx = self._next_alive_char(self.battle_char_idx)
            char = self.party.members[self.battle_char_idx]

        bm = self.battle_menu

        if bm.get("target_mode"):
            self._update_battle_targeting(char)
        elif bm["sub"]:
            self._update_battle_sub_menu(char)
        else:
            self._update_battle_top_menu(char)

        # Check end
        self.battle.check_end()

    def _target_pool(self, mode):
        if mode == "enemy":
            return self.battle.alive_enemies()
        if mode == "fallen":
            return [m for m in self.party.members if not m.alive]
        return self.battle.alive_party()

    def _update_battle_targeting(self, char):
        bm = self.battle_menu
        pool = self._target_pool(bm["target_mode"])
        if not pool:
            bm["target_mode"] = None
            self.battle_pending_action = None
            return
        bm["target_idx"] %= len(pool)
        if self.input.pressed("left") or self.input.pressed("up"):
            bm["target_idx"] = (bm["target_idx"] - 1) % len(pool)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("right") or self.input.pressed("down"):
            bm["target_idx"] = (bm["target_idx"] + 1) % len(pool)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("confirm"):
            target = pool[bm["target_idx"]]
            action = self.battle_pending_action
            bm["target_mode"] = None
            self.battle_pending_action = None
            self.audio.play_sfx("confirm")
            if action is None:
                return
            kind = action[0]
            if kind == "attack":
                self.battle.do_attack(char, target)
            elif kind == "power":
                self.battle.do_use_power(char, action[1], [target])
            elif kind == "item":
                self.battle.do_use_item(char, action[1], [target])
            self._advance_battle_turn()
        elif self.input.pressed("cancel"):
            bm["target_mode"] = None
            self.battle_pending_action = None
            self.audio.play_sfx("cancel")

    def _begin_targeting(self, mode, pending_action):
        bm = self.battle_menu
        bm["sub"] = False
        bm["target_mode"] = mode
        bm["target_idx"] = 0
        self.battle_pending_action = pending_action

    def _update_battle_top_menu(self, char):
        bm = self.battle_menu
        if self.input.pressed("left"):
            bm["selected"] = (bm["selected"] - 1) % len(BATTLE_MENU_TOP)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("right"):
            bm["selected"] = (bm["selected"] + 1) % len(BATTLE_MENU_TOP)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("confirm"):
            sel = bm["selected"]
            self.audio.play_sfx("confirm")
            if sel == 0:  # ENGAGE
                if self.battle.alive_enemies():
                    self._begin_targeting("enemy", ("attack",))
            elif sel == 1:  # RITES
                if char.status == STATUS_VOX_JAMMED:
                    self.battle.log.append(f"{char.name} IS VOX-JAMMED! CANNOT USE RITES!")
                    return
                powers = [self.item_db.get(pid, None) or self._get_power(pid) for pid in char.known_powers]
                powers = [p for p in powers if p]
                bm["sub"] = True
                bm["sub_options"] = [f"{p['name']} ({p.get('cost',0)}{self._res_symbol(p.get('resource',0))})"
                                     for p in powers]
                bm["sub_selected"] = 0
                self.battle_menu["sub_data"] = powers
            elif sel == 2:  # WAR GEAR
                items = [(iid, self.item_db[iid]) for iid in self.party.inventory
                         if iid in self.item_db and self.item_db[iid].get("type") == ITEM_CONSUMABLE]
                if not items:
                    self.battle.log.append("NO CONSUMABLES AVAILABLE!")
                    return
                bm["sub"] = True
                bm["sub_options"] = [f"{d['name']} x{self.party.inventory[iid]}" for iid, d in items]
                bm["sub_selected"] = 0
                bm["sub_data"] = items
            elif sel == 3:  # FLEE
                fled = self.battle.do_flee(self.party)

    def _update_battle_sub_menu(self, char):
        bm = self.battle_menu
        sub_data = bm.get("sub_data", [])
        if self.input.pressed("up"):
            bm["sub_selected"] = (bm["sub_selected"] - 1) % max(1, len(sub_data))
            self.audio.play_sfx("cursor")
        elif self.input.pressed("down"):
            bm["sub_selected"] = (bm["sub_selected"] + 1) % max(1, len(sub_data))
            self.audio.play_sfx("cursor")
        elif self.input.pressed("confirm"):
            sel_idx = bm["sub_selected"]
            if bm["selected"] == 1:  # Power
                if sel_idx < len(sub_data):
                    power = sub_data[sel_idx]
                    res = power.get("resource", RES_NONE)
                    cost = power.get("cost", 0)
                    if res == RES_WARP and char.warp < cost:
                        self.battle.log.append("INSUFFICIENT WARP CHARGES!")
                        return
                    if res == RES_FAITH and char.faith_pts < cost:
                        self.battle.log.append("INSUFFICIENT ACTS OF FAITH!")
                        return
                    ttype = power.get("target", "one_enemy")
                    if ttype in ("one_enemy", "one_enemy_or_ally"):
                        self._begin_targeting("enemy", ("power", power))
                    elif ttype in ("one_ally", "one_any"):
                        self._begin_targeting("ally", ("power", power))
                    elif ttype == "one_fallen":
                        if any(not m.alive for m in self.party.members):
                            self._begin_targeting("fallen", ("power", power))
                        else:
                            self.battle.log.append("NO FALLEN TO RESTORE!")
                    else:
                        # Multi-target — no pick needed
                        targets = self._get_power_targets(power, char)
                        self.battle.do_use_power(char, power, targets)
                        bm["sub"] = False
                        self._advance_battle_turn()
            elif bm["selected"] == 2:  # Item
                if sel_idx < len(sub_data):
                    item_id, item = sub_data[sel_idx]
                    ttype = item.get("target", "one_ally")
                    if "fallen" in ttype:
                        if any(not m.alive for m in self.party.members):
                            self._begin_targeting("fallen", ("item", item))
                        else:
                            self.battle.log.append("NO FALLEN TO REVIVE!")
                    elif "all" in ttype:
                        if "ally" in ttype:
                            targets = self.battle.alive_party()
                        else:
                            targets = self.battle.alive_enemies()
                        self.battle.do_use_item(char, item, targets)
                        bm["sub"] = False
                        self._advance_battle_turn()
                    elif "ally" in ttype:
                        self._begin_targeting("ally", ("item", item))
                    else:
                        self._begin_targeting("enemy", ("item", item))
        elif self.input.pressed("cancel"):
            bm["sub"] = False

    def _get_power(self, power_id):
        import assets.data.config.spells_data as sd
        return sd.SPELLS.get(power_id)

    def _res_symbol(self, res):
        if res == RES_WARP: return "WC"
        if res == RES_FAITH: return "AoF"
        return ""

    def _get_power_targets(self, power, caster):
        target_type = power.get("target", "one_enemy")
        alive_e = self.battle.alive_enemies()
        alive_p = self.battle.alive_party()
        fallen  = [m for m in self.party.members if not m.alive]

        if target_type == "one_enemy":
            return [alive_e[0]] if alive_e else []
        elif target_type == "all_enemies":
            return alive_e
        elif target_type == "one_ally":
            return [alive_p[0]] if alive_p else []
        elif target_type == "all_allies":
            return alive_p
        elif target_type == "one_fallen":
            return [fallen[0]] if fallen else []
        elif target_type == "one_any":
            return [alive_p[0]] if alive_p else []
        elif target_type == "one_enemy_or_ally":
            return [alive_e[0]] if alive_e else []
        return []

    def _advance_battle_turn(self):
        self.audio.play_sfx("cursor")
        # Check for level-ups queued
        for m in self.party.members:
            pass  # Handled on reward

        # Trigger enemy turns
        self.battle_waiting_enemy = True
        self.battle_enemy_delay   = 30
        self.battle_action_queue  = []
        for enemy in self.battle.alive_enemies():
            action = enemy.decide_action(
                self.battle.alive_party(),
                self.battle.alive_enemies(),
                self.battle.turn_num,
            )
            self.battle_action_queue.append((enemy, action))
        self.battle.end_of_round()

    def _execute_next_enemy_action(self):
        if self.battle_action_queue:
            enemy, action = self.battle_action_queue.pop(0)
            if enemy.alive:
                self.battle._execute_enemy_action(enemy, action)
            self.battle_enemy_delay = 20
        else:
            self.battle_waiting_enemy = False
            self.battle_char_idx = self._next_alive_char(-1)
            self.battle_menu["selected"] = 0
            self.battle_menu["sub"] = False

    def _handle_battle_result(self):
        if self.battle.result == BattleResult.DEFEAT:
            if not self.battle_result_shown:
                self.battle_result_shown = True
                self.audio.play_music("gameover")
                self._goto(STATE_GAME_OVER)
                self.tick = 0
        elif self.battle.result in (BattleResult.VICTORY, BattleResult.TERRIFIED):
            if not self.battle_result_shown:
                self.battle_result_shown = True
                self.audio.play_sfx("fanfare")
                # Check for boss post-fight
                if self.battle_is_boss:
                    self._handle_boss_victory()
                else:
                    # Show victory, then check level-ups
                    self._check_levelups_after_battle()
                    self._goto(STATE_VICTORY)
                    self.tick = 0
        elif self.battle.result == BattleResult.FLED:
            self.audio.play_music("worldmap" if self.prev_state == STATE_WORLD else "dungeon")
            self._goto(self.prev_state or STATE_WORLD)
            self.battle = None

    def _handle_boss_victory(self):
        boss_id = self.battle_boss_id
        story = loader.story()
        if boss_id == "ork_warboss_gorkamorka":
            self.party.set_flag(FLAG_ENCAMPMENT_CLEAR)
            if "gorkamorka_banner" in self.item_db:
                self.party.add_item("gorkamorka_banner")
            self._complete_dungeon()
            self._show_story_sequence(story.get("encampment_cleared", []), STATE_WORLD)
        elif boss_id == "squiggoth_great":
            self.party.set_flag(FLAG_CAVES_CLEAR)
            if "great_squiggoth_tusk" in self.item_db:
                self.party.add_item("great_squiggoth_tusk")
            self._complete_dungeon()
            self._show_story_sequence(story.get("caves_cleared", []), STATE_WORLD)
        elif boss_id == "mad_dok":
            self.party.set_flag(FLAG_MANUFACTORUM_CLEAR)
            if "grotnik_tools" in self.item_db:
                self.party.add_item("grotnik_tools")
            self._complete_dungeon()
            if not self.party.get_flag(FLAG_MIDPOINT_SEEN):
                self.party.set_flag(FLAG_MIDPOINT_SEEN)
                self._show_story_sequence(story["midpoint"], STATE_WORLD)
        elif boss_id == "ghazghkull_p1":
            # Phase 2 transition — WAAAGH! reaches full intensity
            if "ghazghkull_p2" in self.enemy_db:
                edata = dict(self.enemy_db["ghazghkull_p2"], id="ghazghkull_p2")
                self._begin_battle_fade([Enemy(edata)], is_boss=True, boss_id="ghazghkull_p2")
            else:
                self.party.set_flag(FLAG_FINAL_DONE)
                self._show_story_sequence(story["ending_choice"], STATE_ENDING)
        elif boss_id == "ghazghkull_p2":
            self.party.set_flag(FLAG_FINAL_DONE)
            if "ghazghkull_banner" in self.item_db:
                self.party.add_item("ghazghkull_banner")
            self._show_story_sequence(story["ending_choice"], STATE_ENDING)
        elif boss_id == "warboss_skullkrumpa":
            self.party.set_flag(FLAG_ROK_CLEAR)
            if "skullkrumpa_klaw" in self.item_db:
                self.party.add_item("skullkrumpa_klaw")
            self._complete_dungeon()
            self._show_story_sequence(story.get("rok_cleared", []), STATE_WORLD)
        else:
            self._check_levelups_after_battle()
            self._goto(STATE_VICTORY)
            self.tick = 0

    def _check_levelups_after_battle(self):
        self.levelup_queue = list(getattr(self.battle, "levelups", []))

    # ── Menu ───────────────────────────────────────────────────────────────────

    def _update_menu(self):
        if self.input.pressed("up"):
            self.menu_selected = (self.menu_selected - 1) % len(MAIN_MENU_OPTIONS)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("down"):
            self.menu_selected = (self.menu_selected + 1) % len(MAIN_MENU_OPTIONS)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("confirm"):
            sel = MAIN_MENU_OPTIONS[self.menu_selected]
            self.audio.play_sfx("confirm")
            if sel == "BATTLE RECORDS":
                self.status_char_idx = 0
                self._goto(STATE_STATUS)
            elif sel == "WAR GEAR":
                self._goto(STATE_INVENTORY)
                self.inv_selected = 0
            elif sel == "SUPPLIES":
                self._goto(STATE_INVENTORY)
                self.inv_selected = 0
            elif sel == "SAVE":
                self._goto(STATE_SAVE)
                self.save_selected = 0
            elif sel == "ABANDON HOPE":
                pygame.quit()
                raise SystemExit
        elif self.input.pressed("cancel"):
            self._goto(self.prev_state or STATE_WORLD)

    def _update_status(self):
        if self.input.pressed("left"):
            self.status_char_idx = (self.status_char_idx - 1) % len(self.party.members)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("right"):
            self.status_char_idx = (self.status_char_idx + 1) % len(self.party.members)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("cancel"):
            self._goto(STATE_MENU)

    def _update_inventory(self):
        items = list(self.party.inventory.items())
        if not items:
            if self.input.pressed("cancel"):
                self._goto(STATE_MENU)
            return
        if self.input.pressed("up"):
            self.inv_selected = (self.inv_selected - 1) % len(items)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("down"):
            self.inv_selected = (self.inv_selected + 1) % len(items)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("cancel"):
            self._goto(STATE_MENU)

    def _update_shop(self):
        items = [self.item_db.get(iid) for iid in self.shop_items if iid in self.item_db]
        items = [i for i in items if i]
        if not items:
            if self.input.pressed("cancel"):
                self._goto(STATE_TOWN)
            return
        if self.input.pressed("up"):
            self.shop_selected = (self.shop_selected - 1) % len(items)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("down"):
            self.shop_selected = (self.shop_selected + 1) % len(items)
            self.audio.play_sfx("cursor")
        elif self.input.pressed("confirm"):
            item = items[self.shop_selected]
            cost = item.get("cost", 0)
            if self.party.spend_gelt(cost):
                self.party.add_item(item["id"])
                self.battle and None  # placeholder
                self.audio.play_sfx("confirm")
            else:
                self.audio.play_sfx("cancel")
        elif self.input.pressed("cancel"):
            self._goto(STATE_TOWN)

    def _update_save(self):
        if self.input.pressed("up"):
            self.save_selected = (self.save_selected - 1) % 3
            self.audio.play_sfx("cursor")
        elif self.input.pressed("down"):
            self.save_selected = (self.save_selected + 1) % 3
            self.audio.play_sfx("cursor")
        elif self.input.pressed("confirm"):
            data = self.party.to_dict()
            save_manager.save(self.save_selected, data)
            self.audio.play_sfx("confirm")
            self._show_dialogue("EMPEROR'S LEDGER", "EL",
                                ["YOUR DEEDS ARE RECORDED. SERVE ON, WARRIOR."],
                                STATE_MENU)
        elif self.input.pressed("cancel"):
            self._goto(STATE_MENU)

    def _update_load(self):
        self._refresh_save_slots()
        if self.input.pressed("up"):
            self.save_selected = (self.save_selected - 1) % 3
            self.audio.play_sfx("cursor")
        elif self.input.pressed("down"):
            self.save_selected = (self.save_selected + 1) % 3
            self.audio.play_sfx("cursor")
        elif self.input.pressed("confirm"):
            data = self.save_slots[self.save_selected]
            if data:
                self.party = Party.from_dict(data, self.item_db)
                # Resume the playtime clock from the saved value
                self.session_start = time.time() - self.party.playtime
                self.world, self.locations = build_world()
                self._goto(STATE_WORLD)
                self.audio.play_music("worldmap")
        elif self.input.pressed("cancel"):
            self._goto(STATE_TITLE)

    def _update_dialogue(self):
        if self.input.pressed("confirm") or self.input.pressed("cancel"):
            self.audio.play_sfx("cursor")
            if self.dialogue_page < len(self.dialogue_pages) - 1:
                self.dialogue_page += 1
            else:
                self.dialogue_pages = []
                ret = self.dialogue_return
                self.dialogue_return = None
                if ret:
                    self._goto(ret)
                else:
                    self._goto(self.prev_state or STATE_WORLD)
                # Check if story should continue
                if self.story_sequence and self.story_page < len(self.story_sequence) - 1:
                    self.story_page += 1
                    self._show_dialogue("TRANSMISSION", "TX",
                                        [self.story_sequence[self.story_page]], self.story_return)
                    return
                self.story_sequence = []
                # A battle deferred behind this dialogue (boss speeches) starts now
                if self.pending_battle:
                    enemies, is_boss, boss_id = self.pending_battle
                    self.pending_battle = None
                    self._begin_battle_fade(enemies, is_boss=is_boss, boss_id=boss_id)

    def _update_gameover(self):
        if self.tick > 180 and self.input.pressed("confirm"):
            self._goto(STATE_TITLE)
            self.audio.play_music("title")

    def _update_victory(self):
        if self.tick > 60 and self.input.pressed("confirm"):
            # Check levelup queue
            if self.levelup_queue:
                char, old, new = self.levelup_queue.pop(0)
                self.levelup_char = char
                self.levelup_old_stats = old
                self.levelup_new_stats = new
                self._goto(STATE_LEVEL_UP)
                self.audio.play_sfx("levelup")
            else:
                # Return to previous state
                self.audio.play_music("worldmap" if self.prev_state == STATE_WORLD else "dungeon")
                prev = self.prev_state or STATE_WORLD
                if prev == STATE_BATTLE:
                    prev = STATE_WORLD
                self._goto(prev)
                self.battle = None

    def _update_levelup(self):
        self.levelup_tick += 1
        if self.input.pressed("confirm") and self.levelup_tick > 30:
            self.levelup_tick = 0
            if self.levelup_queue:
                char, old, new = self.levelup_queue.pop(0)
                self.levelup_char = char
                self.levelup_old_stats = old
                self.levelup_new_stats = new
            else:
                prev = self.prev_state or STATE_WORLD
                if prev == STATE_LEVEL_UP:
                    prev = STATE_WORLD
                self._goto(prev)

    def _update_ending(self):
        self.ending_tick += 1

        if self.ending_choice is None:
            # Choice screen: execute Ghazghkull or leave him to Armageddon's defenders
            if self.input.pressed("up") or self.input.pressed("down"):
                self.ending_cursor = 1 - self.ending_cursor
                self.audio.play_sfx("cursor")
            elif self.input.pressed("confirm") and self.ending_tick > 30:
                self.ending_choice = "execution" if self.ending_cursor == 0 else "mercy"
                self.ending_tick = 0
                self.audio.play_sfx("confirm")
            return

        # Epilogue rolling — return to title once done
        if self.ending_tick > 700 and self.input.pressed("confirm"):
            self._goto(STATE_TITLE)
            self.audio.play_music("title")
            self.party = None
            self.ending_choice = None
            self.ending_cursor = 0
            self.ending_tick = 0

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _goto(self, new_state):
        self.prev_state = self.state
        self.state = new_state

    def _show_dialogue(self, npc_name, portrait, pages, return_state):
        self.dialogue_npc   = npc_name
        self.dialogue_port  = portrait
        self.dialogue_pages = pages
        self.dialogue_page  = 0
        self.dialogue_return = return_state
        self._goto(STATE_DIALOGUE)

    def _show_story_sequence(self, lines, return_state):
        if not lines:
            self._goto(return_state)
            return
        self.story_sequence = lines
        self.story_page     = 0
        self.story_return   = return_state
        self._show_dialogue("TRANSMISSION", "TX", [lines[0]], return_state)

    def _open_shop(self, shop_id):
        from world.town import SHOPS
        shop = SHOPS.get(shop_id)
        if not shop:
            return
        self.shop_id    = shop_id
        self.shop_items = shop["items"]
        self.shop_selected = 0
        self._goto(STATE_SHOP)

    def _refresh_save_slots(self):
        for i in range(3):
            self.save_slots[i] = save_manager.load(i)
