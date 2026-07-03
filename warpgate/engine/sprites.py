import os
import pygame

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "data")

# Font paths consumed by renderer.py
PIXEL_FONT_PATH  = os.path.join(ASSET_DIR, "vendors", "Press_Start_2P", "PressStart2P-Regular.ttf")
TITLE_FONT_PATH  = os.path.join(ASSET_DIR, "vendors", "duvall", "DuvallSmallCaps Bold.ttf")
HEADER_FONT_PATH = os.path.join(ASSET_DIR, "vendors", "duvall", "DuvallSmallCaps.ttf")


def _load(name):
    path = os.path.join(ASSET_DIR, name)
    try:
        img = pygame.image.load(path)
        return img.convert_alpha() if pygame.display.get_surface() else img
    except (pygame.error, FileNotFoundError):
        return None


class SpriteAssets:
    """Lazily-built registry of art assets.  Every lookup degrades to None so
    the renderer keeps its procedural drawing as the universal fallback."""

    _instance = None

    def __init__(self):
        self._sheets       = {}
        self._world_tiles_spec = None
        self._tile_cache   = {}
        self._char_cache   = {}
        self._monster_map  = None
        self._boss_map     = None
        self._portrait_map = None
        self._gui_bg       = {}

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SpriteAssets()
        return cls._instance

    def _sheet(self, name):
        if name not in self._sheets:
            self._sheets[name] = _load(name)
        return self._sheets[name]

    def _crop(self, name, x, y, src_w, src_h, dest_w, dest_h=None):
        sheet = self._sheet(name)
        if sheet is None:
            return None
        dest_h = dest_h or dest_w
        try:
            crop = sheet.subsurface((x, y, src_w, src_h)).copy()
        except ValueError:
            return None
        if crop.get_size() != (dest_w, dest_h):
            crop = pygame.transform.scale(crop, (dest_w, dest_h))
        return crop

    # ── World / dungeon / town terrain — 32 px LPC sheets ────────────────────
    def world_tile(self, tile_id, dest=32):
        if self._world_tiles_spec is None:
            self._world_tiles_spec = {
                # (sheet, src_x, src_y, src_w, src_h)
                "WASTELAND":  ("terrain/dirt.png",               0, 160, 32, 32),
                "ASH":        ("terrain/dirt.png",              32, 160, 32, 32),
                "RUIN_FLOOR": ("terrain/dirt.png",              64, 160, 32, 32),
                "RUBBLE":     ("environments/castlefloors.png", 192, 224, 32, 32),
                "ROAD":       ("environments/castlewalls.png",    0, 192, 32, 32),
                "TOXIC_SEA":  ("terrain/lava.png",               0, 160, 32, 32),
                "DUNGEON":    ("environments/dungeon.png",        0,   0, 32, 32),
                "WALL":       ("environments/dungeon.png",        0,   0, 32, 32),
                "TOWN":       ("environments/castlefloors.png",  64, 192, 32, 32),
                "BRIDGE":     ("terrain/bridges.png",            32,   0, 32, 32),
                "SHRINE":     ("environments/castlefloors.png",   0,   0, 32, 32),
                "DOOR":       ("environments/dungeon.png",        0, 128, 32, 32),
                "CHEST":      ("decorations/chests.png",          0,   0, 32, 32),
                # New terrain types
                "GRASS":      ("terrain/grass.png",               0,   0, 32, 32),
                "WATER":      ("terrain/water.png",               0,   0, 32, 32),
                "ROCK":       ("terrain/rock.png",                0,   0, 32, 32),
                "CEMENT":     ("terrain/cement.png",              0,   0, 32, 32),
                "STAIRS":     ("terrain/stairs.png",              0,   0, 32, 32),
            }
        spec = self._world_tiles_spec.get(tile_id)
        if not spec:
            return None
        sname, x, y, sw, sh = spec
        key = (sname, x, y, dest)
        if key not in self._tile_cache:
            self._tile_cache[key] = self._crop(sname, x, y, sw, sh, dest)
        return self._tile_cache[key]

    # ── dungeon_tiles.png — 16×16 tiles, 1px margin → 17px stride ───────────
    # Tile layout (col, row):
    #   Row 0 col 0-3  → floor variants
    #   Row 1          → wall variants
    #   Row 2 col 0    → closed door, col 1 → open door
    #   Row 3 col 0    → chest closed, col 1 → stairs down
    DTILE_FLOOR_COL, DTILE_FLOOR_ROW = 0, 0
    DTILE_WALL_COL,  DTILE_WALL_ROW  = 0, 1
    DTILE_DOOR_COL,  DTILE_DOOR_ROW  = 0, 2
    DTILE_CHEST_COL, DTILE_CHEST_ROW = 0, 3
    DTILE_STAIR_COL, DTILE_STAIR_ROW = 1, 3

    def dungeon_tile(self, col, row, dest=32):
        name = "environments/dungeon_tiles.png"
        x, y = col * 17, row * 17
        key = ("dt", col, row, dest)
        if key not in self._tile_cache:
            self._tile_cache[key] = self._crop(name, x, y, 16, 16, dest)
        return self._tile_cache[key]

    # ── SpaceBlocks.png — 16×16 tiles, 1px margin → 17px stride ─────────────
    # Sci-fi tileset used for Iron Fortress zone dungeon.
    SBLOCK_FLOOR_COL, SBLOCK_FLOOR_ROW = 0, 0
    SBLOCK_WALL_COL,  SBLOCK_WALL_ROW  = 1, 0
    SBLOCK_DOOR_COL,  SBLOCK_DOOR_ROW  = 2, 0

    def space_block_tile(self, col, row, dest=32):
        name = "environments/SpaceBlocks.png"
        x, y = col * 17, row * 17
        key = ("sb", col, row, dest)
        if key not in self._tile_cache:
            self._tile_cache[key] = self._crop(name, x, y, 16, 16, dest)
        return self._tile_cache[key]

    # ── Panel background textures (paper / wood) ──────────────────────────────
    def gui_bg_patch(self, style="paper", w=128, h=64):
        key = (style, w, h)
        if key in self._gui_bg:
            return self._gui_bg[key]
        fname = "ui/paper background.png" if style == "paper" else "ui/wood background.png"
        sheet = self._sheet(fname)
        if sheet is None:
            self._gui_bg[key] = None
            return None
        sw, sh = sheet.get_size()
        surf = pygame.Surface((w, h))
        for ty in range(0, h, max(1, sh)):
            for tx in range(0, w, max(1, sw)):
                surf.blit(sheet, (tx, ty))
        dark = pygame.Surface((w, h))
        dark.fill((0, 0, 0))
        dark.set_alpha(130)
        surf.blit(dark, (0, 0))
        self._gui_bg[key] = surf
        return surf

    # ── Animated walk-cycle sprite ────────────────────────────────────────────
    # male_walkcycle.png: 576×256, 9 cols × 4 rows of 64×64 frames
    # Rows: 0=up  1=left  2=down  3=right
    # Col 0 = idle frame; cols 1-8 = walk animation
    def walk_frame(self, sheet_name="characters/player_animations/male_walkcycle.png",
                   facing="down", anim_tick=0, dest=32, moving=True):
        DIRECTION_ROW = {"up": 0, "left": 1, "down": 2, "right": 3}
        row = DIRECTION_ROW.get(facing, 2)
        frame_col = ((anim_tick // 8) % 8 + 1) if moving else 0
        key = (sheet_name, row, frame_col, dest)
        if key not in self._char_cache:
            sheet = self._sheet(sheet_name)
            frame = None
            if sheet is not None:
                try:
                    frame = sheet.subsurface((frame_col * 64, row * 64, 64, 64)).copy()
                    if dest != 64:
                        frame = pygame.transform.scale(frame, (dest, dest))
                except ValueError:
                    frame = None
            self._char_cache[key] = frame
        return self._char_cache[key]

    # Backward-compat static idle frame
    def character_frame(self, sheet_name="characters/npcs/soldier.png", dest=32):
        key = (sheet_name, dest)
        if key not in self._char_cache:
            sheet = self._sheet(sheet_name)
            frame = None
            if sheet is not None:
                try:
                    frame = sheet.subsurface((0, 128, 64, 64)).copy()
                    if dest != 64:
                        frame = pygame.transform.scale(frame, (dest, dest))
                except ValueError:
                    frame = None
            self._char_cache[key] = frame
        return self._char_cache[key]

    # ── NPC portraits for dialogue boxes ─────────────────────────────────────
    def npc_portrait(self, portrait_id, dest=40):
        if self._portrait_map is None:
            self._portrait_map = {
                "princess":   "characters/npcs/princess.png",
                "victoria":   "characters/npcs/victoria.png",
                "space_merc": "characters/npcs/space_merc.png",
                "soldier":    "characters/npcs/soldier.png",
                "npc":        "characters/npcs/soldier_altcolor.png",
            }
        fname = self._portrait_map.get(portrait_id)
        if not fname:
            fname = self._portrait_map.get("npc")
        if not fname:
            return None
        key = ("portrait", fname, dest)
        if key not in self._char_cache:
            sheet = self._sheet(fname)
            frame = None
            if sheet is not None:
                _sw, sh = sheet.get_size()
                # LPC idle facing-down row is at y=128 for 256-tall sheets
                fy = 128 if sh >= 192 else 0
                try:
                    frame = sheet.subsurface((0, fy, 64, 64)).copy()
                    if dest != 64:
                        frame = pygame.transform.scale(frame, (dest, dest))
                except ValueError:
                    frame = None
            self._char_cache[key] = frame
        return self._char_cache[key]

    # ── Monster sprites (non-boss) ────────────────────────────────────────────
    # Values: (filename, crop_rect | None)
    # None crop → auto top-left min(w,h,64) square
    def monster_sprite(self, sprite_type, dest=32):
        if "boss" in sprite_type:
            return None
        if self._monster_map is None:
            # Ork types → DCSS orc sprites (32×32 individual PNGs)
            self._monster_map = {
                "small_ork":     ("vendors/dcss/monster/hobgoblin_new.png",    (0, 0, 32, 32)),
                "ork_mek":       ("vendors/dcss/monster/orc_high_priest_new.png", (0, 0, 32, 32)),
                "ork_mounted":   ("vendors/dcss/monster/orc_warrior_new.png",  (0, 0, 32, 32)),
                "ork_mega":      ("vendors/dcss/monster/orc_knight_new.png",   (0, 0, 32, 32)),
                "ork_psyker":    ("vendors/dcss/monster/orc_sorcerer_new.png", (0, 0, 32, 32)),
                "ork_heavy":     ("vendors/dcss/monster/orc_warrior_new.png",  (0, 0, 32, 32)),
                "ork_walker":    ("vendors/dcss/monster/abomination_large.png",(0, 0, 32, 32)),
                "ork_flying":    ("vendors/dcss/monster/giant_bat.png",        (0, 0, 32, 32)),
                "ork":           ("vendors/dcss/monster/orc_new.png",          (0, 0, 32, 32)),
                # Beasts
                "beast_large":   ("vendors/dcss/monster/troll.png",            (0, 0, 32, 32)),
                "beast":         ("vendors/dcss/monster/giant_scorpion.png",   (0, 0, 32, 32)),
                # Chaos / daemon types → DCSS demon sprites
                "chaos_spawn":   ("vendors/dcss/monster/chaos_spawn.png",      (0, 0, 32, 32)),
                "warp_spawn":    ("vendors/dcss/monster/chaos_spawn.png",      (0, 0, 32, 32)),
                "daemon_swarm":  ("vendors/dcss/monster/imp.png",              (0, 0, 32, 32)),
                "warp_bat":      ("vendors/dcss/monster/giant_bat.png",        (0, 0, 32, 32)),
                "warp_ghost":    ("vendors/dcss/monster/imp.png",              (0, 0, 32, 32)),
                "nurgle_spawn":  ("vendors/dcss/monster/putrid.png",           (0, 0, 32, 32)),
                "plague_slime":  ("vendors/dcss/monster/giant_slug.png",       (0, 0, 32, 32)),
                "nurgle_plant":  ("vendors/dcss/monster/beast.png",            (0, 0, 32, 32)),
                "daemon_flora":  ("vendors/dcss/monster/beast.png",            (0, 0, 32, 32)),
                "daemon_wyrm":   ("vendors/dcss/monster/green_death.png",      (0, 0, 32, 32)),
                "warp_herald":   ("vendors/dcss/monster/cacodemon.png",        (0, 0, 32, 32)),
                "plague_herald": ("vendors/dcss/monster/putrid.png",           (0, 0, 32, 32)),
            }
        fname = None
        crop  = None
        for key, val in self._monster_map.items():
            if key in sprite_type:
                fname, crop = val
                break
        if not fname:
            return None
        cache_key = (fname, str(crop), dest)
        if cache_key not in self._char_cache:
            sheet = self._sheet(fname)
            frame = None
            if sheet is not None:
                if crop:
                    cx, cy, cw, ch = crop
                    try:
                        frame = sheet.subsurface((cx, cy, cw, ch)).copy()
                        frame = pygame.transform.scale(frame, (dest, dest))
                    except ValueError:
                        frame = None
                else:
                    w, h = sheet.get_size()
                    size = min(w, h, 64)
                    try:
                        frame = sheet.subsurface((0, 0, size, size)).copy()
                        if dest != size:
                            frame = pygame.transform.scale(frame, (dest, dest))
                    except ValueError:
                        frame = None
            self._char_cache[cache_key] = frame
        return self._char_cache[cache_key]

    # ── Kenney roguelike-caves-dungeons tileset ──────────────────────────────
    # roguelikeDungeon_transparent.png: 29 cols × 18 rows, 16px tiles, 1px gap
    # (stride = 17px; first tile at x=0, y=0)
    KCAVE_FLOOR_COL, KCAVE_FLOOR_ROW = 7,  0   # cave stone floor
    KCAVE_WALL_COL,  KCAVE_WALL_ROW  = 0,  2   # dark stone wall
    KCAVE_DOOR_COL,  KCAVE_DOOR_ROW  = 16, 6   # wooden door
    KCAVE_STAIR_COL, KCAVE_STAIR_ROW = 20, 3   # stairs

    def kenney_cave_tile(self, col, row, dest=32):
        name = "vendors/kenney_roguelike_caves/roguelikeDungeon_transparent.png"
        x, y = col * 17, row * 17
        key  = ("kcave", col, row, dest)
        if key not in self._tile_cache:
            self._tile_cache[key] = self._crop(name, x, y, 16, 16, dest)
        return self._tile_cache[key]

    # ── Kenney tiny-dungeon tileset ───────────────────────────────────────────
    # tilemap_packed.png: 12 cols × 11 rows, 16px tiles, no gap
    KTINY_FLOOR_COL, KTINY_FLOOR_ROW = 0, 3    # dungeon floor
    KTINY_WALL_COL,  KTINY_WALL_ROW  = 0, 0    # solid wall
    KTINY_DOOR_COL,  KTINY_DOOR_ROW  = 4, 1    # door

    def kenney_tiny_tile(self, col, row, dest=32):
        name = "vendors/kenney_tiny_dungeon/tilemap_packed.png"
        x, y = col * 16, row * 16
        key  = ("ktiny", col, row, dest)
        if key not in self._tile_cache:
            self._tile_cache[key] = self._crop(name, x, y, 16, 16, dest)
        return self._tile_cache[key]

    # ── Battle backdrop ───────────────────────────────────────────────────────
    def battle_backdrop(self, zone="ash_wastes", dest_w=256, dest_h=160):
        key = ("backdrop", zone, dest_w, dest_h)
        if key in self._gui_bg:
            return self._gui_bg[key]
        # City zones get the ruined city background; all others get the sky layer
        if zone in ("iron_fortress", "manufactorum", "encampment"):
            fname = "environments/city_backdrop/City Background.png"
        else:
            fname = "environments/city_backdrop/Sky.png"
        sheet = self._sheet(fname)
        surf  = None
        if sheet is not None:
            sw, sh = sheet.get_size()
            # Crop centre of the source to maintain aspect
            scale = max(dest_w / sw, dest_h / sh)
            cw = int(dest_w / scale)
            ch = int(dest_h / scale)
            cx = max(0, (sw - cw) // 2)
            cy = max(0, (sh - ch) // 2)
            try:
                crop = sheet.subsurface((cx, cy, min(cw, sw), min(ch, sh))).copy()
                surf = pygame.transform.scale(crop, (dest_w, dest_h))
            except (ValueError, pygame.error):
                surf = None
        self._gui_bg[key] = surf
        return surf

    # ── Boss sprites (explicit path — bypasses the boss guard above) ──────────
    def boss_sprite(self, sprite_type, dest=48):
        if self._boss_map is None:
            self._boss_map = {
                # DCSS-based bosses
                "boss_ork":           ("vendors/dcss/monster/orc_warlord.png",  (0, 0, 32, 32)),
                "boss_ghazghkull_p2": ("vendors/dcss/monster/fiend.png",        (0, 0, 32, 32)),
                "boss_ghazghkull":    ("vendors/dcss/monster/executioner.png",  (0, 0, 32, 32)),
                "boss_squiggoth":     ("vendors/dcss/monster/troll.png",        (0, 0, 32, 32)),
                "boss_dok":           ("vendors/dcss/monster/putrid.png",       (0, 0, 32, 32)),
                # Original hand-drawn bosses kept for any future chaos enemies
                "boss_plague": ("enemies/PlaugeKing.png", None),
                "boss_herald": ("enemies/pumpking.png",   (0, 0, 46, 46)),
                "boss_wyrm":   ("enemies/DAGRONS5.png",   (0, 0, 80, 80)),
            }
        fname = None
        crop  = None
        for key, val in self._boss_map.items():
            if key in sprite_type:
                fname, crop = val
                break
        if not fname:
            return None
        cache_key = ("boss", fname, str(crop), dest)
        if cache_key not in self._char_cache:
            sheet = self._sheet(fname)
            frame = None
            if sheet is not None:
                if crop:
                    cx, cy, cw, ch = crop
                    try:
                        frame = sheet.subsurface((cx, cy, cw, ch)).copy()
                        frame = pygame.transform.scale(frame, (dest, dest))
                    except ValueError:
                        frame = None
                else:
                    w, h = sheet.get_size()
                    try:
                        frame = sheet.subsurface((0, 0, w, h)).copy()
                        frame = pygame.transform.scale(frame, (dest, dest))
                    except ValueError:
                        frame = None
            self._char_cache[cache_key] = frame
        return self._char_cache[cache_key]
