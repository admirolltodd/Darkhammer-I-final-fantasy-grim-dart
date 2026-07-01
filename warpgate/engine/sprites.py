import os
import pygame

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "data")


def _load(name):
    path = os.path.join(ASSET_DIR, name)
    try:
        img = pygame.image.load(path)
        return img.convert_alpha() if pygame.display.get_surface() else img
    except (pygame.error, FileNotFoundError):
        return None


class SpriteAssets:
    """Lazily-built registry of optional art assets (LPC tiles/characters,
    Kenney sheet). Every lookup degrades to None on failure or missing file,
    so the renderer can keep its procedural drawing as the universal fallback."""

    _instance = None

    def __init__(self):
        self._sheets = {}
        self._world_tiles_spec = None
        self._tile_cache = {}
        self._char_cache = {}
        self._monster_map = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SpriteAssets()
        return cls._instance

    def _sheet(self, name):
        if name not in self._sheets:
            self._sheets[name] = _load(name)
        return self._sheets[name]

    def _crop(self, name, x, y, size, dest):
        sheet = self._sheet(name)
        if sheet is None:
            return None
        try:
            crop = sheet.subsurface((x, y, size, size)).copy()
        except ValueError:
            return None
        if dest != size:
            crop = pygame.transform.scale(crop, (dest, dest))
        return crop

    # ── World/dungeon/town terrain tiles, scaled down from 32px LPC art ──
    def world_tile(self, tile_id, dest=32):
        if self._world_tiles_spec is None:
            self._world_tiles_spec = {
                "WASTELAND":  ("terrain/dirt.png", 0, 160),
                "ASH":        ("terrain/dirt.png", 32, 160),
                "RUIN_FLOOR": ("terrain/dirt.png", 64, 160),
                "RUBBLE":     ("environments/castlefloors.png", 192, 224),
                "ROAD":       ("environments/castlewalls.png", 0, 192),
                "TOXIC_SEA":  ("terrain/lava.png", 0, 160),
                "DUNGEON":    ("environments/dungeon.png", 0, 0),
                "WALL":       ("environments/dungeon.png", 0, 0),
                "TOWN":       ("environments/castlefloors.png", 64, 192),
                "BRIDGE":     ("terrain/bridges.png", 32, 0),
                "SHRINE":     ("environments/castlefloors.png", 0, 0),
                "DOOR":       ("environments/dungeon.png", 0, 128),
                "CHEST":      ("decorations/chests.png", 0, 0),
            }
        spec = self._world_tiles_spec.get(tile_id)
        if not spec:
            return None
        name, x, y = spec
        key = (name, x, y, dest)
        if key not in self._tile_cache:
            self._tile_cache[key] = self._crop(name, x, y, 32, dest)
        return self._tile_cache[key]

    # ── Player/NPC overworld sprite: single idle "facing down" LPC frame ──
    def character_frame(self, sheet_name="characters/npcs/soldier.png", dest=32):
        key = (sheet_name, dest)
        if key not in self._char_cache:
            sheet = self._sheet(sheet_name)
            frame = None
            if sheet is not None:
                try:
                    # LPC walkcycle layout: row 2 (down-facing), col 0 (idle), 64x64 frames
                    frame = sheet.subsurface((0, 128, 64, 64)).copy()
                    if dest != 64:
                        frame = pygame.transform.scale(frame, (dest, dest))
                except ValueError:
                    frame = None
            self._char_cache[key] = frame
        return self._char_cache[key]

    # ── A handful of LPC monster sprites mapped onto select enemy sprite_types.
    # Bosses keep their own hand-tuned procedural art, so none of these keys
    # may be a substring of a "boss_*" sprite_type. ──
    def monster_sprite(self, sprite_type, dest=32):
        if "boss" in sprite_type:
            return None
        if self._monster_map is None:
            self._monster_map = {
                "ork_flying":  "enemies/bee.png",
                "ork_mounted": "enemies/snake.png",
                "ork_psyker":  "enemies/eyeball.png",
                "small_ork":   "enemies/small_worm.png",
                "beast_large": "enemies/big_worm.png",
                "beast":       "enemies/snake.png",
            }
        fname = None
        for key, fn in self._monster_map.items():
            if key in sprite_type:
                fname = fn
                break
        if not fname:
            return None
        cache_key = (fname, dest)
        if cache_key not in self._char_cache:
            sheet = self._sheet(fname)
            frame = None
            if sheet is not None:
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
