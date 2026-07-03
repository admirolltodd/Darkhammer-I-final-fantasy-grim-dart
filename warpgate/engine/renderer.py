import os
import pygame
import math
import random
from constants import *
from engine.sprites import SpriteAssets, PIXEL_FONT_PATH, TITLE_FONT_PATH

TILE_ID_NAMES = {
    T_WASTELAND: "WASTELAND", T_ASH: "ASH",        T_RUBBLE: "RUBBLE",
    T_ROAD: "ROAD",           T_TOXIC_SEA: "TOXIC_SEA", T_RUIN_FLOOR: "RUIN_FLOOR",
    T_DUNGEON: "DUNGEON",     T_TOWN: "TOWN",       T_WALL: "WALL",
    T_DOOR: "DOOR",           T_CHEST: "CHEST",     T_SHRINE: "SHRINE",
    T_BRIDGE: "BRIDGE",       T_GRASS: "GRASS",     T_WATER: "WATER",
    T_ROCK: "ROCK",           T_CEMENT: "CEMENT",   T_STAIRS: "STAIRS",
}

class Renderer:
    def __init__(self):
        self.surface = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self._font   = None
        self.assets  = SpriteAssets.get()
        self._particles = []
        self._shake_frames = 0
        self._shake_mag    = 0
        self._stars = [(random.randint(0, INTERNAL_W), random.randint(0, INTERNAL_H), random.randint(1,3)) for _ in range(80)]
        self._star_scroll  = 0

    def get_font(self):
        if self._font is None:
            try:
                self._font = pygame.font.Font(PIXEL_FONT_PATH, FONT_SIZE)
            except (FileNotFoundError, pygame.error):
                self._font = pygame.font.SysFont("monospace", FONT_SIZE, bold=True)
        return self._font

    def get_title_font(self, size=24):
        key = ("title", size)
        if not hasattr(self, "_title_fonts"):
            self._title_fonts = {}
        if key not in self._title_fonts:
            try:
                self._title_fonts[key] = pygame.font.Font(TITLE_FONT_PATH, size)
            except (FileNotFoundError, pygame.error):
                self._title_fonts[key] = pygame.font.SysFont("serif", size, bold=True)
        return self._title_fonts[key]

    def draw_title_text(self, text, x, y, color=UI_HIGHLIGHT, size=24, shadow=True):
        f = self.get_title_font(size)
        t = str(text).upper()
        if shadow:
            s = f.render(t, True, UI_SHADOW)
            self.surface.blit(s, (x + 1, y + 2))
        img = f.render(t, True, color)
        self.surface.blit(img, (x, y))
        return img.get_width()

    def shake(self, frames=4, magnitude=3):
        self._shake_frames = frames
        self._shake_mag    = magnitude

    def add_particle(self, x, y, color, count=6, speed=2, life=20):
        for _ in range(count):
            dx = random.uniform(-speed, speed)
            dy = random.uniform(-speed, speed)
            self._particles.append([x, y, dx, dy, color, life, life])

    def _tick_particles(self):
        alive = []
        for p in self._particles:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
            if p[5] > 0:
                alive.append(p)
        self._particles = alive

    def _draw_particles(self):
        for p in self._particles:
            alpha = int(255 * (p[5] / p[6]))
            c = p[4]
            pygame.draw.rect(self.surface, c, (int(p[0]), int(p[1]), 2, 2))

    def draw_text(self, text, x, y, color=UI_TEXT, bg=None, shadow=True):
        f = self.get_font()
        t = str(text).upper()
        if shadow:
            s = f.render(t, False, UI_SHADOW)
            self.surface.blit(s, (x+1, y+1))
        if bg:
            s = f.render(t, False, bg)
            self.surface.blit(s, (x, y))
        img = f.render(t, False, color)
        self.surface.blit(img, (x, y))
        return img.get_width()

    def draw_box(self, x, y, w, h, bg=UI_BG, border=UI_BORDER, title=None, texture=None):
        # Interior — try textured paper background first, fall back to solid fill
        tex = self.assets.gui_bg_patch(texture or "paper", w, h)
        if tex:
            self.surface.blit(tex, (x, y))
        else:
            pygame.draw.rect(self.surface, bg, (x, y, w, h))
        # Top-edge inner highlight strip
        hl = tuple(min(255, c + 14) for c in bg)
        pygame.draw.rect(self.surface, hl, (x + 4, y + 4, w - 8, 2))
        # Bottom-edge inner shadow strip
        sh = tuple(max(0, c - 8) for c in bg)
        pygame.draw.rect(self.surface, sh, (x + 4, y + h - 6, w - 8, 2))

        # 3-layer border: dark outer → gold band → dark inner
        outer = tuple(max(0, c // 4) for c in border)
        pygame.draw.rect(self.surface, outer,  (x,   y,   w,   h  ), 1)
        pygame.draw.rect(self.surface, border, (x+1, y+1, w-2, h-2), 2)
        pygame.draw.rect(self.surface, outer,  (x+3, y+3, w-6, h-6), 1)

        # Corner diamond ornaments
        for cx, cy in [(x+1, y+1), (x+w-5, y+1), (x+1, y+h-5), (x+w-5, y+h-5)]:
            pygame.draw.rect(self.surface, border, (cx+1, cy,   2, 4))
            pygame.draw.rect(self.surface, border, (cx,   cy+1, 4, 2))

        if title:
            tw = self.draw_text(title, x + 6, y + 5, UI_HIGHLIGHT)
            pygame.draw.line(self.surface, border, (x + 5, y + 14), (x + tw + 8, y + 14), 1)

    def draw_hp_bar(self, x, y, w, current, maximum, label=None):
        pct = max(0, current / max(1, maximum))
        color = UI_HP_GOOD if pct > 0.5 else (UI_HP_MID if pct > 0.25 else UI_HP_LOW)
        pygame.draw.rect(self.surface, C_DARK_GREY, (x, y, w, 6))
        pygame.draw.rect(self.surface, color, (x, y, int(w * pct), 6))
        pygame.draw.rect(self.surface, UI_BORDER, (x, y, w, 6), 1)
        if label:
            self.draw_text(label, x, y - 8, UI_TEXT, shadow=False)

    def draw_resource_bar(self, x, y, w, current, maximum, color=UI_MP_COLOR):
        pct = max(0, current / max(1, maximum))
        pygame.draw.rect(self.surface, C_DARK_GREY, (x, y, w, 4))
        pygame.draw.rect(self.surface, color, (x, y, int(w * pct), 4))
        pygame.draw.rect(self.surface, UI_BORDER, (x, y, w, 4), 1)

    def draw_scrolling_stars(self, speed=0.3):
        self._star_scroll = (self._star_scroll + speed) % INTERNAL_H
        for sx, sy, sz in self._stars:
            ny = int((sy + self._star_scroll) % INTERNAL_H)
            brightness = 80 + sz * 40
            c = (brightness, brightness, brightness)
            pygame.draw.rect(self.surface, c, (sx, ny, sz, sz))

    def render_title(self, blink_on, game_ticks):
        self.surface.fill(C_BLACK)
        self.draw_scrolling_stars(0.2)

        # Animated warp glow for the main logo
        phase = math.sin(game_ticks * 0.05) * 0.5 + 0.5
        glow_c = (int(100 + 80*phase), int(20 + 10*phase), int(140 + 40*phase))

        # Large Duvall title
        t1w = self.draw_title_text("WARPGATE", 0, 38, glow_c, size=28, shadow=False)
        t1w = self.draw_title_text("WARPGATE", 0, 36, C_GOLD, size=28, shadow=True)
        # Centre it now we know the width
        self.surface.fill(C_BLACK, (0, 32, INTERNAL_W, 36))
        self.draw_scrolling_stars(0)  # redraw stars only in dirty rect area — skip, stars already drawn
        cx = (INTERNAL_W - t1w) // 2
        self.draw_title_text("WARPGATE", cx + 1, 38, glow_c, size=28, shadow=False)
        self.draw_title_text("WARPGATE", cx,     36, C_GOLD,  size=28, shadow=True)

        sub = "BATTLE FOR ARMAGEDDON"
        sw = self.draw_title_text(sub, 0, 66, C_MID_GREY, size=12, shadow=False)
        self.surface.fill(C_BLACK, (0, 62, INTERNAL_W, 18))
        scx = (INTERNAL_W - sw) // 2
        self.draw_title_text(sub, scx, 66, C_MID_GREY, size=12, shadow=True)

        # Aquila symbol (pixel art)
        ax, ay = INTERNAL_W // 2 - 8, 88
        for ppx, ppy in [(0,2),(1,1),(2,0),(3,1),(3,2),(2,3),(4,3),(5,3),
                         (5,2),(6,1),(7,0),(8,1),(8,2),(7,3),(3,4),(4,4),(4,5)]:
            pygame.draw.rect(self.surface, C_GOLD, (ax + ppx, ay + ppy, 1, 1))

        self.draw_text("IN THE GRIM DARKNESS OF THE FAR FUTURE,", 10, 110, C_DARK_RED)
        self.draw_text("THERE IS ONLY WAR.", 60, 120, C_DARK_RED)

        if blink_on:
            msg = "PRESS ENTER TO SERVE THE EMPEROR"
            mx = (INTERNAL_W - len(msg) * FONT_SIZE) // 2
            self.draw_text(msg, mx, 152, C_GOLD)

        self.draw_text("V1.0  ---  IMPERIUM OF MAN", 52, 212, C_MID_GREY)

    def render_class_select(self, class_defs, selected_slots, current_slot, cursor_class, scroll_tick):
        self.surface.fill(C_BLACK)
        self.draw_scrolling_stars(0.1)
        self.draw_text("ASSEMBLE YOUR WARBAND", 40, 4, C_GOLD)
        self.draw_text(f"SLOT {current_slot + 1} OF {MAX_PARTY}", 180, 4, C_MID_GREY)

        # Class list
        for i, (cid, cdef) in enumerate(class_defs.items()):
            y = 20 + i * 20
            color = C_GOLD if i == cursor_class else UI_TEXT
            sel = ">" if i == cursor_class else " "
            self.draw_text(f"{sel} {cdef['name']}", 4, y, color)
            self.draw_text(cdef["short_desc"], 96, y, C_MID_GREY)

        # Stats of highlighted class
        cid = list(class_defs.keys())[cursor_class]
        cdef = class_defs[cid]
        bx, by, bw, bh = 4, 140, 248, 70
        self.draw_box(bx, by, bw, bh, title="DATASLATE")
        self.draw_text(cdef["lore"], bx+4, by+12, C_LIGHT_GREY)

        # Chosen slots
        for i, s in enumerate(selected_slots):
            if s is not None:
                self.draw_text(f"[{i+1}] {CLASS_NAMES[s]}", 4, 215 + i*9, C_GREEN)

        self.draw_text("ENTER: SELECT  ESC: BACK", 40, 212, C_MID_GREY)

    def render_world_map(self, world, party, anim_tick):
        self.surface.fill(C_BLACK)
        cam_x = party.world_x - INTERNAL_W // (TILE * 2)
        cam_y = party.world_y - INTERNAL_H // (TILE * 2)

        tiles_x = INTERNAL_W // TILE + 2
        tiles_y = INTERNAL_H // TILE + 2

        TILE_COLORS = {
            T_WASTELAND:  (45, 40, 35),
            T_ASH:        (55, 50, 45),
            T_RUBBLE:     (60, 55, 50),
            T_ROAD:       (70, 65, 60),
            T_TOXIC_SEA:  (20, 35, 55),
            T_RUIN_FLOOR: (50, 45, 40),
            T_DUNGEON:    (30, 25, 20),
            T_TOWN:       (50, 40, 20),
            T_WALL:       (40, 35, 30),
            T_BRIDGE:     (65, 60, 55),
            T_SHRINE:     (80, 70, 20),
            T_GRASS:      (25, 55, 20),
            T_WATER:      (15, 35, 75),
            T_ROCK:       (55, 50, 48),
            T_CEMENT:     (65, 62, 60),
            T_STAIRS:     (70, 60, 40),
        }
        TILE_MARKS = {
            T_TOWN:    ("T", C_GOLD),
            T_DUNGEON: ("D", C_RED),
            T_SHRINE:  ("+", C_YELLOW),
            T_STAIRS:  ("S", C_LIGHT_GREY),
        }

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                wx = cam_x + tx
                wy = cam_y + ty
                px = tx * TILE
                py = ty * TILE
                tile_id = world.get_tile(wx, wy)
                color = TILE_COLORS.get(tile_id, C_DARK_GREY)

                # Animate toxic sea
                if tile_id == T_TOXIC_SEA:
                    phase = (anim_tick // 20 + wx + wy) % 3
                    color = [(20,35,55),(25,45,60),(15,30,50)][phase]

                sprite = self.assets.world_tile(TILE_ID_NAMES.get(tile_id))
                if sprite:
                    self.surface.blit(sprite, (px, py))
                else:
                    pygame.draw.rect(self.surface, color, (px, py, TILE-1, TILE-1))

                # Grid mark for special tiles
                if tile_id in TILE_MARKS:
                    ch, mc = TILE_MARKS[tile_id]
                    self.draw_text(ch, px + TILE//4, py + TILE//4, mc, shadow=False)

        # Party sprite — animated walk cycle
        px = (party.world_x - cam_x) * TILE
        py = (party.world_y - cam_y) * TILE
        blink = (anim_tick // 15) % 2
        party_sprite = self.assets.walk_frame(
            facing=getattr(party, "facing", "down"),
            anim_tick=anim_tick,
            dest=TILE,
            moving=getattr(party, "moving", False),
        )
        if party_sprite:
            self.surface.blit(party_sprite, (px, py))
        else:
            pcol = C_GOLD if blink else C_YELLOW
            pygame.draw.rect(self.surface, pcol, (px+4, py+4, 8, 8))
            pygame.draw.rect(self.surface, C_BLACK, (px+5, py+6, 2, 2))
            pygame.draw.rect(self.surface, C_BLACK, (px+9, py+6, 2, 2))

        # HUD strip
        pygame.draw.rect(self.surface, C_BLACK, (0, INTERNAL_H - 16, INTERNAL_W, 16))
        self.draw_text(f"LOC: {party.location}", 4, INTERNAL_H - 13, C_MID_GREY)
        self.draw_text(f"GELT: {party.gelt}", 160, INTERNAL_H - 13, C_GOLD)
        self.draw_text(f"CORRUPT: {party.corruption}%", 208, INTERNAL_H - 13, UI_CORRUPT if party.corruption > 25 else C_MID_GREY)

    def _draw_battle_background(self, anim_tick, zone="ash_wastes"):
        """Layered battle backdrop: sprite backdrop (if available) + procedural overlays."""
        BATTLE_H = INTERNAL_H - 60
        HORIZON  = 55
        VP       = INTERNAL_W // 2

        # Try sprite-based city backdrop
        backdrop = self.assets.battle_backdrop(zone, INTERNAL_W, BATTLE_H)
        if backdrop:
            self.surface.blit(backdrop, (0, 0))
            tint = pygame.Surface((INTERNAL_W, BATTLE_H))
            tint.fill((0, 0, 0))
            tint.set_alpha(110)
            self.surface.blit(tint, (0, 0))
        else:
            # Procedural sky: banded gradient, deep purple-black → ember-amber at horizon
            sky_bands = [
                (0,                HORIZON * 1 // 5, ( 6,  3, 14)),
                (HORIZON * 1 // 5, HORIZON * 2 // 5, (10,  5, 18)),
                (HORIZON * 2 // 5, HORIZON * 3 // 5, (18,  7, 16)),
                (HORIZON * 3 // 5, HORIZON * 4 // 5, (28, 10, 12)),
                (HORIZON * 4 // 5, HORIZON,           (42, 15,  8)),
            ]
            for y0, y1, c in sky_bands:
                pygame.draw.rect(self.surface, c, (0, y0, INTERNAL_W, max(1, y1 - y0)))

            # Ground: scorched plain below horizon
            ground_bands = [
                (HORIZON,      HORIZON + 25, (22, 14, 10)),
                (HORIZON + 25, HORIZON + 60, (17, 11,  8)),
                (HORIZON + 60, BATTLE_H,     (12,  8,  6)),
            ]
            for y0, y1, c in ground_bands:
                pygame.draw.rect(self.surface, c, (0, y0, INTERNAL_W, max(1, y1 - y0)))

        # Horizon fire-glow (pulsing)
        phase = math.sin(anim_tick * 0.04) * 0.5 + 0.5
        for dy in range(-4, 7):
            t  = 1.0 - abs(dy) / 6.0
            gr = int((90 + 50 * phase) * t)
            gg = int((25 +  8 * phase) * t)
            pygame.draw.line(self.surface, (gr, gg, 5),
                             (0, HORIZON + dy), (INTERNAL_W, HORIZON + dy))

        # Ruined building silhouettes on the horizon
        ruins = [
            ( 8, HORIZON - 20, 14, 20),
            (50, HORIZON - 14, 18, 14),
            (95, HORIZON - 25, 12, 25),
            (145, HORIZON - 18, 16, 18),
            (185, HORIZON - 11, 20, 11),
            (225, HORIZON - 22, 13, 22),
        ]
        for rx, ry, rw, rh in ruins:
            pygame.draw.rect(self.surface, (5, 3, 3), (rx, ry, rw, rh))
            if rh > 14:
                for wx in range(rx + 2, rx + rw - 2, 5):
                    pygame.draw.rect(self.surface, (14, 7, 4), (wx, ry + 4, 2, 3))
            for cx in range(rx, rx + rw, 4):
                if (cx // 4) % 2 == 0:
                    pygame.draw.rect(self.surface, (5, 3, 3), (cx, ry - 3, 3, 3))

        # Perspective grid: lines converge to vanishing point, horizontal rows compress
        grid_c = (30, 20, 14)
        for gx in range(0, INTERNAL_W + 1, 20):
            pygame.draw.line(self.surface, grid_c, (VP, HORIZON), (gx, BATTLE_H), 1)
        for i in range(1, 7):
            t  = (i / 6) ** 1.8
            gy = HORIZON + int(t * (BATTLE_H - HORIZON))
            pygame.draw.line(self.surface, grid_c, (0, gy), (INTERNAL_W, gy))

        # Animated smoke columns rising from burning ruins
        for si, sx in enumerate([30, 120, 200]):
            for p in range(5):
                drift = int(math.sin((anim_tick * 0.06) + si * 1.3 + p * 0.7) * 4)
                sy = HORIZON - 10 - p * 7
                if sy < 0:
                    break
                br = 22 + p * 4
                pygame.draw.rect(self.surface, (br, br - 4, br - 7),
                                 (sx + drift, sy, 4, 6))

    def render_battle(self, battle, menu_state, anim_tick, damage_floats=None):
        zone = getattr(battle, "zone", "ash_wastes") or "ash_wastes"
        self._draw_battle_background(anim_tick, zone)

        alive_e = battle.alive_enemies()
        alive_p = battle.alive_party()

        # ── Draw enemies ──
        slots = [(INTERNAL_W // 5, 30), (2*INTERNAL_W // 5, 30),
                 (3*INTERNAL_W // 5, 30), (4*INTERNAL_W // 5, 30)]
        # Resolve the currently hovered target (targeting mode)
        target_obj = None
        tm = menu_state.get("target_mode") if menu_state else None
        if tm:
            if tm == "enemy":
                pool = battle.alive_enemies()
            elif tm == "fallen":
                pool = [m for m in battle.party.members if not m.alive]
            else:
                pool = battle.alive_party()
            if pool:
                target_obj = pool[menu_state.get("target_idx", 0) % len(pool)]

        for i, enemy in enumerate(battle.enemies[:4]):
            if i >= len(slots):
                break
            ex, ey = slots[i]
            if not enemy.alive:
                continue
            self._draw_enemy_sprite(enemy, ex - 20, ey, anim_tick)
            if enemy is target_obj and (anim_tick // 8) % 2 == 0:
                pygame.draw.polygon(self.surface, C_GOLD,
                                    [(ex - 4, ey - 14), (ex + 4, ey - 14), (ex, ey - 7)])
            # HP bar (only if scanned)
            if enemy.scanned or enemy.boss:
                self.draw_hp_bar(ex - 20, ey + 38, 40, enemy.hp, enemy.max_hp)
                self.draw_text(f"{enemy.hp}", ex - 18, ey + 46, C_MID_GREY, shadow=False)
            self.draw_text(enemy.name[:10], ex - 22, ey + 50, UI_TEXT, shadow=False)
            if enemy.status != STATUS_NONE:
                sc = STATUS_COLORS.get(enemy.status, C_WHITE)
                self.draw_text(STATUS_NAMES[enemy.status][:4], ex - 18, ey + 58, sc, shadow=False)

        # ── Party status panel ──
        panel_y = INTERNAL_H - 60
        pygame.draw.rect(self.surface, C_DARK_GREY, (0, panel_y, INTERNAL_W, 60))
        pygame.draw.rect(self.surface, UI_BORDER,   (0, panel_y, INTERNAL_W, 60), 1)

        for i, char in enumerate(battle.party.members):
            cx = 4 + i * 64
            cy = panel_y + 2
            color = UI_TEXT if char.alive else C_MID_GREY
            if char is target_obj and (anim_tick // 8) % 2 == 0:
                pygame.draw.polygon(self.surface, C_GOLD,
                                    [(cx - 1, cy + 1), (cx - 1, cy + 7), (cx + 3, cy + 4)])
                cx += 6
            self.draw_text(char.name[:6], cx, cy, color, shadow=False)
            self.draw_text(f"LV{char.level}", cx + 44, cy, C_MID_GREY, shadow=False)
            hp_c = UI_HP_GOOD if char.hp > char.max_hp * 0.5 else (UI_HP_MID if char.hp > char.max_hp * 0.25 else UI_HP_LOW)
            self.draw_text(f"{char.hp:3}/{char.max_hp}", cx, cy + 10, hp_c if char.alive else C_DARK_RED, shadow=False)
            self.draw_hp_bar(cx, cy + 20, 60, char.hp, char.max_hp)
            if char.alive and char.status != STATUS_NONE:
                sc = STATUS_COLORS.get(char.status, C_WHITE)
                self.draw_text(STATUS_NAMES[char.status][:6], cx, cy + 28, sc, shadow=False)
            elif not char.alive:
                self.draw_text("FALLEN", cx, cy + 28, C_DARK_RED, shadow=False)
            # Resource bar
            if char.warp_max_total > 0:
                self.draw_resource_bar(cx, cy + 36, 60, char.warp, char.warp_max_total, UI_MP_COLOR)
                self.draw_text(f"WC:{char.warp}", cx, cy + 42, C_WARP, shadow=False)
            elif char.faith_max > 0:
                self.draw_resource_bar(cx, cy + 36, 60, char.faith_pts, char.faith_max, C_GOLD)
                self.draw_text(f"AoF:{char.faith_pts}", cx, cy + 42, C_GOLD, shadow=False)

        # ── Command menu ──
        if tm:
            hint = "SELECT TARGET  (ARROWS: CYCLE / ENTER: CONFIRM / ESC: BACK)"
            self.draw_box(0, panel_y - 28, INTERNAL_W, 26)
            self.draw_text(hint, 8, panel_y - 18, C_GOLD, shadow=False)
        elif menu_state:
            self._draw_battle_menu(menu_state, panel_y)

        # ── Battle log ──
        self._draw_battle_log(battle.log, panel_y)

        # ── Damage floats ──
        if damage_floats:
            for df in damage_floats:
                self.draw_text(str(df[0]), df[1], df[2], C_YELLOW, shadow=False)

        self._tick_particles()
        self._draw_particles()

    def _draw_enemy_sprite(self, enemy, x, y, tick):
        bob = int(math.sin(tick * 0.1) * 2)
        y += bob
        c  = enemy.color
        st = enemy.sprite_type

        # Try boss sprite first (explicit map, larger dest)
        if "boss" in st:
            img = self.assets.boss_sprite(st, dest=48)
            if img:
                self.surface.blit(img, (x - 6, y - 6))
                return
        else:
            img = self.assets.monster_sprite(st)
            if img:
                self.surface.blit(img, (x, y))
                return

        if "boss" in st:
            # Large boss sprite
            w, h = 36, 36
            pygame.draw.rect(self.surface, c, (x, y, w, h))
            # Details
            pygame.draw.rect(self.surface, C_BLACK, (x+8,  y+8,  6, 6))
            pygame.draw.rect(self.surface, C_BLACK, (x+22, y+8,  6, 6))
            pygame.draw.rect(self.surface, C_BRIGHT_RED, (x+8, y+8, 6, 6))
            pygame.draw.rect(self.surface, C_BRIGHT_RED, (x+22, y+8, 6, 6))
            pygame.draw.rect(self.surface, C_BLOOD, (x+6, y+20, 24, 4))
        elif "heavy" in st:
            w, h = 26, 30
            pygame.draw.rect(self.surface, c, (x, y, w, h))
            pygame.draw.rect(self.surface, C_STEEL, (x+2, y+2, w-4, 12))
            pygame.draw.rect(self.surface, C_BLOOD, (x+8, y+18, 10, 3))
        elif "daemon" in st:
            w, h = 22, 26
            pygame.draw.rect(self.surface, c, (x, y, w, h))
            # Wings
            pygame.draw.rect(self.surface, c, (x-6, y+4, 8, 16))
            pygame.draw.rect(self.surface, c, (x+w, y+4, 8, 16))
            pygame.draw.rect(self.surface, C_BRIGHT_RED, (x+6, y+8, 4, 4))
            pygame.draw.rect(self.surface, C_BRIGHT_RED, (x+12, y+8, 4, 4))
        elif "small_daemon" in st or "swarm" in st:
            w, h = 10, 12
            for di in range(min(3, 4)):
                ox = di * 6
                pygame.draw.rect(self.surface, c, (x+ox, y+di*2, w, h))
        elif "tyranid" in st:
            w = 16 if "small" in st else (24 if "medium" in st else 30)
            h = w + 4
            pygame.draw.rect(self.surface, c, (x, y, w, h))
            pygame.draw.rect(self.surface, C_BONE, (x+4, y+4, w-8, 8))
        elif "necron" in st:
            w, h = 18, 24
            pygame.draw.rect(self.surface, C_STEEL, (x, y, w, h))
            pygame.draw.rect(self.surface, c, (x+4, y+4, w-8, h-8))
            pygame.draw.rect(self.surface, C_BRIGHT_RED, (x+6, y+6, 6, 3))
        else:
            # Generic humanoid
            w, h = 14, 18
            pygame.draw.rect(self.surface, c, (x, y, w, h))
            pygame.draw.rect(self.surface, C_BONE, (x+3, y+2, 8, 8))
            pygame.draw.rect(self.surface, C_BLACK, (x+5, y+4, 2, 2))
            pygame.draw.rect(self.surface, C_BLACK, (x+9, y+4, 2, 2))

        # Status indicator
        if enemy.status != STATUS_NONE:
            sc = STATUS_COLORS.get(enemy.status, C_WHITE)
            pygame.draw.rect(self.surface, sc, (x + w//2 - 2, y - 6, 4, 4))

    def _draw_battle_menu(self, menu_state, panel_y):
        opts = menu_state.get("options", [])
        selected = menu_state.get("selected", 0)
        sub = menu_state.get("sub", False)

        mx = 0
        my = panel_y - 28
        mw = INTERNAL_W
        mh = 26

        self.draw_box(mx, my, mw, mh)
        for i, opt in enumerate(opts[:4]):
            ox = mx + 4 + i * (mw // 4)
            oy = my + 4
            c  = C_GOLD if i == selected else UI_TEXT
            arrow = ">" if i == selected else " "
            self.draw_text(f"{arrow}{opt}", ox, oy, c, shadow=False)

        if sub:
            sub_opts = menu_state.get("sub_options", [])
            sub_sel  = menu_state.get("sub_selected", 0)
            sw = 180
            sh = min(len(sub_opts), 8) * 10 + 8
            sx = 4
            sy = my - sh - 4
            self.draw_box(sx, sy, sw, sh)
            visible_start = max(0, sub_sel - 4)
            for i, sopt in enumerate(sub_opts[visible_start:visible_start+8]):
                soy = sy + 4 + i * 10
                idx = visible_start + i
                c   = C_GOLD if idx == sub_sel else UI_TEXT
                arrow = ">" if idx == sub_sel else " "
                self.draw_text(f"{arrow}{sopt}", sx + 4, soy, c, shadow=False)

    def _draw_battle_log(self, log, panel_y):
        log_x = 0
        log_y = panel_y - 50
        log_w = INTERNAL_W
        log_h = 22

        pygame.draw.rect(self.surface, (5, 5, 10), (log_x, log_y, log_w, log_h))
        pygame.draw.rect(self.surface, C_DARK_GREY, (log_x, log_y, log_w, log_h), 1)

        recent = log[-2:] if log else []
        for i, msg in enumerate(recent):
            self.draw_text(msg[:40], log_x + 2, log_y + 2 + i * 10, C_LIGHT_GREY, shadow=False)

    def render_dialogue(self, npc_name, portrait_id, text, page, total_pages, blink):
        bx, by, bw, bh = 0, INTERNAL_H - 56, INTERNAL_W, 56
        self.draw_box(bx, by, bw, bh, texture="wood")

        # Portrait — try sprite, fall back to initials placeholder
        portrait = self.assets.npc_portrait(portrait_id, dest=40)
        if portrait:
            self.surface.blit(portrait, (bx + 2, by + 2))
        else:
            pygame.draw.rect(self.surface, C_DARK_GREY, (bx + 2, by + 2, 40, 40))
            self.draw_text(portrait_id[:2], bx + 14, by + 17, C_GOLD)

        # Name (drawn with Duvall at slightly larger size)
        self.draw_title_text(npc_name, bx + 46, by + 2, C_GOLD, size=10)

        # Text (wrap at 28 chars)
        lines = self._wrap_text(text, 26)
        for i, line in enumerate(lines[:4]):
            self.draw_text(line, bx + 46, by + 16 + i * 10, UI_TEXT, shadow=False)

        # Page indicator
        if total_pages > 1:
            self.draw_text(f"{page+1}/{total_pages}", bx + bw - 20, by + bh - 12, C_MID_GREY, shadow=False)
        if blink:
            self.draw_text("V", bx + bw - 10, by + bh - 12, C_GOLD, shadow=False)

    def render_main_menu(self, options, selected, party):
        # Darken the background
        dark = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 180))
        self.surface.blit(dark, (0, 0))

        mx, my, mw = 80, 20, 100
        self.draw_box(mx, my, mw, len(options) * 14 + 12, title="COMMAND")

        for i, opt in enumerate(options):
            oy = my + 12 + i * 14
            c  = C_GOLD if i == selected else UI_TEXT
            self.draw_text(f"{'>' if i==selected else ' '} {opt}", mx + 4, oy, c)

        # Party mini-strip
        for i, m in enumerate(party.members):
            px = 4
            py = 20 + i * 45
            self.draw_box(px, py, 72, 43)
            hc = UI_HP_GOOD if m.hp > m.max_hp * 0.5 else (UI_HP_MID if m.hp > m.max_hp * 0.25 else UI_HP_LOW)
            self.draw_text(m.name[:6], px+4, py+4, UI_TEXT if m.alive else C_DARK_RED)
            self.draw_text(f"{m.class_name[:10]}", px+4, py+13, C_MID_GREY)
            self.draw_text(f"HP {m.hp}/{m.max_hp}", px+4, py+22, hc)
            self.draw_hp_bar(px+4, py+32, 60, m.hp, m.max_hp)

    def render_status_screen(self, character, page):
        self.surface.fill(C_BLACK)
        self.draw_box(0, 0, INTERNAL_W, INTERNAL_H, title=f"DATASLATE: {character.name}")

        self.draw_text(character.class_name, 4, 14, C_GOLD)
        self.draw_text(f"LV {character.level}  XP {character.xp}", 100, 14, UI_TEXT)

        stats = [
            ("HP",    f"{character.hp}/{character.max_hp}"),
            ("STR",   str(character.str_total)),
            ("DEF",   str(character.def_total)),
            ("AGI",   str(character.agi_total)),
            ("FAITH", str(character.faith_total)),
            ("PSY",   str(character.psy_total)),
            ("HIT%",  str(character.hit_total)),
            ("EVA%",  str(character.eva_total)),
        ]
        for i, (lbl, val) in enumerate(stats):
            col = i % 2
            row = i // 2
            sx = 4 + col * 120
            sy = 28 + row * 14
            self.draw_text(f"{lbl}:", sx, sy, C_MID_GREY)
            self.draw_text(val,       sx + 44, sy, UI_TEXT)

        # Equipment
        self.draw_text("EQUIPMENT", 4, 90, C_GOLD)
        for i, slot in enumerate(ALL_SLOTS):
            eq = character.equipment[slot]
            name = eq["name"][:18] if eq else "---"
            self.draw_text(f"{slot[:4]}:", 4, 102 + i * 10, C_MID_GREY)
            self.draw_text(name, 40, 102 + i * 10, UI_TEXT)

        # Status
        if character.status != STATUS_NONE:
            sc = STATUS_COLORS.get(character.status, C_WHITE)
            self.draw_text(STATUS_NAMES[character.status], 4, 155, sc)
        else:
            self.draw_text("STATUS: NOMINAL", 4, 155, C_GREEN)

        self.draw_text("ESC: BACK", 4, INTERNAL_H - 10, C_MID_GREY)

    def render_shop(self, shop_items, selected, party, mode="BUY"):
        self.surface.fill(C_BLACK)
        self.draw_box(0, 0, INTERNAL_W, INTERNAL_H, title="IMPERIAL ARMORY")
        self.draw_text(f"THRONE GELT: {party.gelt}", 4, 10, C_GOLD)
        self.draw_text(f"MODE: {mode}", 160, 10, C_MID_GREY)

        for i, item in enumerate(shop_items):
            y = 22 + i * 12
            c = C_GOLD if i == selected else UI_TEXT
            mark = ">" if i == selected else " "
            name = item["name"][:20]
            cost = item.get("cost", 0)
            self.draw_text(f"{mark}{name}", 4, y, c)
            self.draw_text(f"{cost}G", 210, y, C_GOLD if c == C_GOLD else C_MID_GREY)

        if shop_items and selected < len(shop_items):
            item = shop_items[selected]
            desc = item.get("desc", "")
            by = INTERNAL_H - 24
            self.draw_box(0, by, INTERNAL_W, 24)
            self.draw_text(desc[:40], 4, by + 4, C_LIGHT_GREY)

        self.draw_text("ENTER: BUY  ESC: LEAVE", 40, INTERNAL_H - 10, C_MID_GREY)

    def render_inventory(self, inv_items, selected, party, item_db):
        self.surface.fill(C_BLACK)
        self.draw_box(0, 0, INTERNAL_W, INTERNAL_H, title="WAR GEAR - SUPPLIES")
        self.draw_text(f"GELT: {party.gelt}", 4, 10, C_GOLD)

        for i, (item_id, count) in enumerate(inv_items):
            y = 22 + i * 10
            if y > INTERNAL_H - 30:
                break
            c = C_GOLD if i == selected else UI_TEXT
            mark = ">" if i == selected else " "
            name = item_db.get(item_id, {}).get("name", item_id)[:22]
            self.draw_text(f"{mark}{name}", 4, y, c)
            self.draw_text(f"x{count}", 210, y, C_MID_GREY)

        if inv_items and selected < len(inv_items):
            item_id = inv_items[selected][0]
            item = item_db.get(item_id, {})
            desc = item.get("desc", "")
            by = INTERNAL_H - 20
            self.draw_box(0, by, INTERNAL_W, 20)
            self.draw_text(desc[:38], 4, by + 4, C_LIGHT_GREY)

    def render_level_up(self, character, old_stats, new_stats):
        self.surface.fill(C_BLACK)
        self.draw_scrolling_stars(0.1)
        self.draw_box(20, 20, INTERNAL_W - 40, INTERNAL_H - 40, title="LEVEL UP!")
        self.draw_text(f"{character.name} ASCENDS TO LEVEL {character.level}", 24, 32, C_GOLD)
        self.draw_text("THE EMPEROR'S LIGHT SHINES BRIGHTER THROUGH YOU.", 24, 44, C_LIGHT_GREY)

        stat_keys = ["HP","STR","DEF","AGI","FAITH","PSY"]
        for i, k in enumerate(stat_keys):
            old_v = old_stats.get(k, 0)
            new_v = new_stats.get(k, 0)
            diff  = new_v - old_v
            y = 60 + i * 14
            self.draw_text(f"{k}:", 28, y, C_MID_GREY)
            self.draw_text(str(old_v), 70, y, UI_TEXT)
            self.draw_text("->", 90, y, C_MID_GREY)
            self.draw_text(str(new_v), 106, y, C_GREEN)
            if diff > 0:
                self.draw_text(f"+{diff}", 130, y, C_GOLD)

        self.draw_text("PRESS ENTER TO CONTINUE", 40, INTERNAL_H - 32, C_GOLD)

    def render_game_over(self, tick):
        self.surface.fill(C_BLACK)
        alpha = min(255, tick * 3)
        ov = pygame.Surface((INTERNAL_W, INTERNAL_H))
        ov.fill(C_DARK_RED)
        ov.set_alpha(alpha // 3)
        self.surface.blit(ov, (0, 0))

        if tick > 60:
            msg1 = "THE EMPEROR WEEPS"
            msg2 = "YOUR WARBAND IS SHATTERED"
            msg3 = "THE DARKNESS CONSUMES ALL"
            x1 = (INTERNAL_W - len(msg1) * FONT_SIZE) // 2
            x2 = (INTERNAL_W - len(msg2) * FONT_SIZE) // 2
            x3 = (INTERNAL_W - len(msg3) * FONT_SIZE) // 2
            self.draw_text(msg1, x1, 80, C_DARK_RED)
            if tick > 90:
                self.draw_text(msg2, x2, 100, C_MID_GREY)
            if tick > 120:
                self.draw_text(msg3, x3, 120, C_MID_GREY)
            if tick > 150:
                self.draw_text("PRESS ENTER TO SERVE AGAIN", 28, 160, C_DARK_GREY)

    def render_victory_screen(self, tick, xp, gelt, items):
        self.surface.fill(C_BLACK)
        self.draw_scrolling_stars(0.3)
        self.draw_text("FOR THE EMPEROR!", 60, 30, C_GOLD)
        self.draw_text(f"XP EARNED: {xp}", 60, 50, UI_TEXT)
        self.draw_text(f"GELT LOOTED: {gelt}", 60, 62, C_GOLD)
        if items:
            self.draw_text("ITEMS RECOVERED:", 60, 76, C_MID_GREY)
            for i, item in enumerate(items[:4]):
                self.draw_text(f"- {item['name'][:24]}", 64, 86 + i * 10, UI_TEXT)
        self.draw_text("PRESS ENTER TO CONTINUE", 32, 170, C_GOLD)

    def render_dungeon(self, dungeon, party, anim_tick):
        self.surface.fill((5, 5, 8))
        cam_x = party.world_x - INTERNAL_W // (TILE * 2)
        cam_y = party.world_y - INTERNAL_H // (TILE * 2)

        # Choose tileset based on dungeon zone
        dzone        = getattr(dungeon, "zone", "")
        iron_fortress = dzone == "iron_fortress"
        fungal_caves  = dzone == "fungal_caves"

        DTILE_COLORS = {
            T_WALL:       (25, 20, 20),
            T_RUIN_FLOOR: (35, 30, 28),
            T_DOOR:       (60, 45, 20),
            T_CHEST:      (80, 65, 15),
            T_SHRINE:     (70, 60, 15),
            T_CEMENT:     (50, 50, 55),
            T_STAIRS:     (60, 55, 40),
        }
        DTILE_MARKS = {
            T_DOOR:   ("D", C_RUST),
            T_CHEST:  ("C", C_GOLD),
            T_SHRINE: ("+", C_YELLOW),
            T_STAIRS: ("^", C_LIGHT_GREY),
        }

        for ty in range(INTERNAL_H // TILE + 2):
            for tx in range(INTERNAL_W // TILE + 2):
                wx = cam_x + tx
                wy = cam_y + ty
                px = tx * TILE
                py = ty * TILE
                tile_id = dungeon.get_tile(wx, wy)

                # Zone-specific tileset lookup
                sprite = None
                if iron_fortress:
                    if tile_id in (T_RUIN_FLOOR, T_DUNGEON):
                        sprite = self.assets.space_block_tile(
                            SpriteAssets.SBLOCK_FLOOR_COL, SpriteAssets.SBLOCK_FLOOR_ROW, TILE)
                    elif tile_id == T_WALL:
                        sprite = self.assets.space_block_tile(
                            SpriteAssets.SBLOCK_WALL_COL, SpriteAssets.SBLOCK_WALL_ROW, TILE)
                    elif tile_id == T_DOOR:
                        sprite = self.assets.space_block_tile(
                            SpriteAssets.SBLOCK_DOOR_COL, SpriteAssets.SBLOCK_DOOR_ROW, TILE)
                elif fungal_caves:
                    if tile_id in (T_RUIN_FLOOR, T_DUNGEON):
                        sprite = self.assets.kenney_cave_tile(
                            SpriteAssets.KCAVE_FLOOR_COL, SpriteAssets.KCAVE_FLOOR_ROW, TILE)
                    elif tile_id == T_WALL:
                        sprite = self.assets.kenney_cave_tile(
                            SpriteAssets.KCAVE_WALL_COL, SpriteAssets.KCAVE_WALL_ROW, TILE)
                    elif tile_id == T_DOOR:
                        sprite = self.assets.kenney_cave_tile(
                            SpriteAssets.KCAVE_DOOR_COL, SpriteAssets.KCAVE_DOOR_ROW, TILE)
                    elif tile_id == T_STAIRS:
                        sprite = self.assets.kenney_cave_tile(
                            SpriteAssets.KCAVE_STAIR_COL, SpriteAssets.KCAVE_STAIR_ROW, TILE)
                else:
                    if tile_id in (T_RUIN_FLOOR, T_DUNGEON):
                        sprite = self.assets.dungeon_tile(
                            SpriteAssets.DTILE_FLOOR_COL, SpriteAssets.DTILE_FLOOR_ROW, TILE)
                    elif tile_id == T_WALL:
                        sprite = self.assets.dungeon_tile(
                            SpriteAssets.DTILE_WALL_COL, SpriteAssets.DTILE_WALL_ROW, TILE)
                    elif tile_id == T_DOOR:
                        sprite = self.assets.dungeon_tile(
                            SpriteAssets.DTILE_DOOR_COL, SpriteAssets.DTILE_DOOR_ROW, TILE)
                    elif tile_id == T_CHEST:
                        sprite = self.assets.dungeon_tile(
                            SpriteAssets.DTILE_CHEST_COL, SpriteAssets.DTILE_CHEST_ROW, TILE)
                    elif tile_id == T_STAIRS:
                        sprite = self.assets.dungeon_tile(
                            SpriteAssets.DTILE_STAIR_COL, SpriteAssets.DTILE_STAIR_ROW, TILE)

                # Fall back to world_tile then solid colour
                if sprite is None:
                    sprite = self.assets.world_tile(TILE_ID_NAMES.get(tile_id))

                if sprite:
                    self.surface.blit(sprite, (px, py))
                elif tile_id == T_WALL:
                    pygame.draw.rect(self.surface, (25, 20, 20), (px, py, TILE, TILE))
                    pygame.draw.rect(self.surface, (35, 30, 28), (px, py, TILE, 2))
                elif tile_id == T_RUIN_FLOOR:
                    v = (wx * 13 + wy * 7) % 5
                    pygame.draw.rect(self.surface, (35+v, 30+v, 28+v), (px, py, TILE, TILE))
                    pygame.draw.rect(self.surface, (20, 15, 15), (px, py, TILE, 1))
                else:
                    color = DTILE_COLORS.get(tile_id, (20, 15, 15))
                    pygame.draw.rect(self.surface, color, (px, py, TILE, TILE))
                if tile_id in DTILE_MARKS:
                    ch, mc = DTILE_MARKS[tile_id]
                    self.draw_text(ch, px + TILE//4, py + TILE//4, mc, shadow=False)

        # Party — animated walk cycle
        px2 = (party.world_x - cam_x) * TILE
        py2 = (party.world_y - cam_y) * TILE
        blink = (anim_tick // 20) % 2
        party_sprite = self.assets.walk_frame(
            facing=getattr(party, "facing", "down"),
            anim_tick=anim_tick,
            dest=TILE,
            moving=getattr(party, "moving", False),
        )
        if party_sprite:
            self.surface.blit(party_sprite, (px2, py2))
        else:
            pcol = C_GOLD if blink else C_YELLOW
            pygame.draw.rect(self.surface, pcol, (px2+4, py2+4, 8, 8))
            pygame.draw.rect(self.surface, C_BLACK, (px2+5, py2+6, 2, 2))
            pygame.draw.rect(self.surface, C_BLACK, (px2+9, py2+6, 2, 2))

        # Minimap
        self._draw_minimap(dungeon, party, anim_tick)

        # HUD
        pygame.draw.rect(self.surface, C_BLACK, (0, INTERNAL_H - 12, INTERNAL_W, 12))
        self.draw_text(f"{dungeon.name}  FL.{dungeon.floor}", 4, INTERNAL_H - 10, C_MID_GREY)
        self.draw_text(f"GELT:{party.gelt}", 160, INTERNAL_H - 10, C_GOLD)

    def _draw_minimap(self, dungeon, party, tick):
        mm_size = 40
        mm_x = INTERNAL_W - mm_size - 4
        mm_y = 4
        pygame.draw.rect(self.surface, (10, 8, 8), (mm_x, mm_y, mm_size, mm_size))
        pygame.draw.rect(self.surface, C_DARK_GREY, (mm_x, mm_y, mm_size, mm_size), 1)

        scale = mm_size / max(dungeon.width, dungeon.height)
        for (wx, wy) in dungeon.visited:
            tile_id = dungeon.get_tile(wx, wy)
            px = mm_x + int(wx * scale)
            py = mm_y + int(wy * scale)
            c = (40, 35, 30) if tile_id == T_RUIN_FLOOR else (20, 15, 15)
            if tile_id == T_CHEST:
                c = C_GOLD
            elif tile_id == T_DOOR:
                c = C_RUST
            pygame.draw.rect(self.surface, c, (px, py, max(1, int(scale)), max(1, int(scale))))

        # Party position on minimap
        ppx = mm_x + int(party.world_x * scale)
        ppy = mm_y + int(party.world_y * scale)
        blink = (tick // 15) % 2
        if blink:
            pygame.draw.rect(self.surface, C_GOLD, (ppx, ppy, 2, 2))

    def render_town(self, town, party, anim_tick):
        self.surface.fill((15, 12, 10))
        cam_x = party.world_x - INTERNAL_W // (TILE * 2)
        cam_y = party.world_y - INTERNAL_H // (TILE * 2)

        TOWN_COLORS = {
            T_RUIN_FLOOR: (40, 35, 30),
            T_WALL:       (30, 25, 20),
            T_ROAD:       (50, 45, 40),
            T_DOOR:       (70, 55, 20),
            T_SHRINE:     (80, 70, 20),
        }

        for ty in range(INTERNAL_H // TILE + 2):
            for tx in range(INTERNAL_W // TILE + 2):
                wx = cam_x + tx
                wy = cam_y + ty
                px = tx * TILE
                py = ty * TILE
                tile_id = town.get_tile(wx, wy)
                sprite = self.assets.world_tile(TILE_ID_NAMES.get(tile_id))
                if sprite:
                    self.surface.blit(sprite, (px, py))
                else:
                    color = TOWN_COLORS.get(tile_id, (20, 15, 12))
                    pygame.draw.rect(self.surface, color, (px, py, TILE, TILE))
                if tile_id == T_DOOR:
                    self.draw_text("D", px + TILE//4, py + TILE//4, C_RUST, shadow=False)
                elif tile_id == T_SHRINE:
                    self.draw_text("+", px + TILE//4, py + TILE//4, C_GOLD, shadow=False)

        # NPCs
        npc_sprite = self.assets.character_frame("characters/npcs/soldier_altcolor.png")
        for npc in town.npcs:
            nx = (npc.x - cam_x) * TILE
            ny = (npc.y - cam_y) * TILE
            if 0 <= nx < INTERNAL_W and 0 <= ny < INTERNAL_H:
                if npc_sprite:
                    self.surface.blit(npc_sprite, (nx, ny))
                else:
                    pygame.draw.rect(self.surface, npc.color, (nx+3, ny+3, 10, 12))
                    pygame.draw.rect(self.surface, C_BONE, (nx+5, ny+3, 6, 6))
                self.draw_text(npc.name[:4], nx, ny + TILE - 8, C_MID_GREY, shadow=False)

        # Party — animated walk cycle
        px2 = (party.world_x - cam_x) * TILE
        py2 = (party.world_y - cam_y) * TILE
        party_sprite = self.assets.walk_frame(
            facing=getattr(party, "facing", "down"),
            anim_tick=anim_tick,
            dest=TILE,
            moving=getattr(party, "moving", False),
        )
        if party_sprite:
            self.surface.blit(party_sprite, (px2, py2))
        else:
            pygame.draw.rect(self.surface, C_GOLD, (px2+3, py2+3, 10, 12))
            pygame.draw.rect(self.surface, C_BONE, (px2+5, py2+3, 6, 6))

        # HUD
        pygame.draw.rect(self.surface, C_BLACK, (0, INTERNAL_H - 12, INTERNAL_W, 12))
        self.draw_text(town.name, 4, INTERNAL_H - 10, C_MID_GREY)
        self.draw_text(f"GELT:{party.gelt}", 160, INTERNAL_H - 10, C_GOLD)

    def render_save_screen(self, slots, selected, mode="SAVE"):
        self.surface.fill(C_BLACK)
        self.draw_box(20, 20, INTERNAL_W - 40, INTERNAL_H - 40, title=f"{mode} - EMPEROR'S LEDGER")
        for i in range(3):
            sy = 36 + i * 48
            c  = C_GOLD if i == selected else UI_TEXT
            self.draw_box(24, sy, INTERNAL_W - 48, 44)
            if slots[i] is None:
                self.draw_text(f"SLOT {i+1}: EMPTY", 28, sy + 8, C_DARK_GREY)
                self.draw_text("THE EMPEROR'S LEDGER IS EMPTY HERE.", 28, sy + 22, C_DARK_GREY)
            else:
                s = slots[i]
                self.draw_text(f"SLOT {i+1}: {s['location']}", 28, sy + 4, c)
                self.draw_text(f"PARTY: " + ", ".join(p["name"] for p in s["party"][:3]), 28, sy + 14, UI_TEXT)
                self.draw_text(f"CORRUPT: {s['corruption']}%  TIME: {s['playtime']//60}m", 28, sy + 24, C_MID_GREY)
        self.draw_text("ENTER: CONFIRM  ESC: BACK", 40, INTERNAL_H - 28, C_MID_GREY)

    def render_ending(self, choice, tick, cursor=0, rok_cleared=False, corruption=0):
        self.surface.fill(C_BLACK)
        self.draw_scrolling_stars(0.1)

        # ── Choice screen: Ghazghkull kneels — what do you do? ──
        if choice is None:
            self.draw_title_text("THE BEAST KNEELS", 30, 30, C_GOLD, size=16)
            self.draw_text("GHAZGHKULL MAG URUK THRAKA IS BEATEN.", 20, 70, C_LIGHT_GREY)
            self.draw_text("YOUR WEAPON IS RAISED.", 20, 84, C_LIGHT_GREY)
            options = [
                "EXECUTE THE BEAST",
                "LEAVE HIM TO ARMAGEDDON'S DEFENDERS",
            ]
            for i, opt in enumerate(options):
                y = 120 + i * 20
                c = C_GOLD if cursor == i else C_MID_GREY
                if cursor == i:
                    self.draw_text(">", 24, y, C_GOLD)
                self.draw_text(opt, 36, y, c)
            self.draw_text("UP/DOWN TO CHOOSE - ENTER TO DECIDE", 24, INTERNAL_H - 20, C_DARK_GOLD)
            return

        # ── Epilogue ──
        if choice == "execution":
            lines = [
                "THE SHOT ECHOES THROUGH THE IRON FORTRESS.",
                "GHAZGHKULL MAG URUK THRAKA IS DEAD.",
                "ACROSS ARMAGEDDON, A MILLION ORKS FEEL IT.",
                "THE WAAAGH! DOES NOT END. IT SHATTERS --",
                "A THOUSAND WARBOSSES NOW CLAIM HIS THRONE,",
                "AND TURN THEIR CHOPPAS ON EACH OTHER.",
            ]
        else:
            lines = [
                "YOU LOWER YOUR WEAPON.",
                "YARRICK'S LEGIONS TAKE THE BEAST IN CHAINS.",
                "PROPHET OF THE WAAAGH! -- BROKEN, DISPLAYED, DIMINISHED.",
                "EVERY ORK ON ARMAGEDDON SEES THEIR GOD-WARLORD KNEEL.",
                "SOME SAY HE SMILED AS THE CHAINS CLOSED.",
                "SOME SAY THIS WAS HIS PLAN ALL ALONG.",
            ]
        lines.append("")
        if rok_cleared:
            lines += [
                "THE WARP BEACON IS SILENT. NO NEW WAAAGH!S ANSWER.",
                "ARMAGEDDON WILL BURN FOR YEARS. BUT IT WILL HOLD.",
            ]
        else:
            lines += [
                "BUT IN THE VOID, THE BEACON STILL SINGS.",
                "MORE SHIPS. MORE WAAAGH!S. THEY ARE COMING.",
            ]
        if corruption >= 50:
            lines += ["", "AND IN YOUR DREAMS, THE WARP WHISPERS YOUR NAMES."]
        lines += [
            "",
            "IN THE GRIM DARKNESS OF THE FAR FUTURE,",
            "THERE IS ONLY WAR.",
            "THE EMPEROR ENDURES. SO MUST WE.",
        ]

        max_lines = min(len(lines), tick // 40)
        for i, line in enumerate(lines[:max_lines]):
            y = 24 + i * 12
            c = C_LIGHT_GREY if line else C_DARK_GREY
            self.draw_text(line, 16, y, c if line else C_BLACK)

        if tick > len(lines) * 40 + 60:
            self.draw_text("PRESS ENTER", 88, INTERNAL_H - 16, C_GOLD)

    def _wrap_text(self, text, width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= width:
                current = f"{current} {word}".strip()
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def present(self, screen):
        if self._shake_frames > 0:
            ox = random.randint(-self._shake_mag, self._shake_mag)
            oy = random.randint(-self._shake_mag, self._shake_mag)
            self._shake_frames -= 1
        else:
            ox, oy = 0, 0
        scaled = pygame.transform.scale(self.surface, (SCREEN_W, SCREEN_H))
        screen.blit(scaled, (ox * SCALE, oy * SCALE))
        pygame.display.flip()
