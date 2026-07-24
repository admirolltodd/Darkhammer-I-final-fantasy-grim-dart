# WARPGATE: Chronicles of the 41st Millennium

A turn-based RPG in the style of classic Final Fantasy games, set in an original
grimdark universe inspired by Warhammer 40,000. Lead a four-person warband across
the volcanic ash wastes of a besieged hive world, fight turn-based battles against
orks, daemons, and heretics, and hold back the encroaching corruption of the warp.

This is a fan-made, non-commercial project built for personal/portfolio use — an
homage to both classic JRPG combat and the grimdark 40k aesthetic, not an official
Games Workshop product.

## Features

- **Turn-based party combat** — agility-based initiative order, physical attacks,
  psychic/faith-fueled powers, item use, and tactical retreat.
- **Six playable classes**, each with a distinct resource and identity: Astartes
  (melee juggernaut), Inquisitor, Psyker (Warp powers, with a risk of "Perils of
  the Warp" backfiring), Sister of Battle (Faith powers), Tech-Priest, and
  Commissar. Classes promote into elite forms (e.g. Psyker to Primaris Psyker,
  Sister to Canoness) as they level.
- **Deep combat systems** — status effects, buffs/debuffs, elemental/warp damage
  types, weapon overheat mechanics, critical hits, relic items, boss-specific
  abilities and phase transitions, and enemy special mechanics (e.g. splitting
  daemons, summoned reinforcements).
- **Corruption & morale** — a party-wide corruption meter that can trigger warp
  madness and other debuffs at high levels, and a morale system that shifts with
  victories, deaths, and retreats.
- **World exploration** — an overworld map connecting hive cities, dungeons, and
  shrines (including the climactic Ghazghkull's Iron Fortress), plus town and
  dungeon navigation with its own tile/rendering system.
- **Save/load system** and a dedicated audio manager for music and sound effects.
- **Retro presentation** — a low-resolution internal framebuffer (256x224)
  scaled up 3x, rendered with Pygame for a classic 16-bit RPG look.

## Tech Stack

- **Python 3** with **Pygame** for rendering, input, and audio.
- No external game engine — custom tile/world renderer, battle system, and save
  manager, all built from scratch on top of Pygame.

## Requirements

- Python 3.9+ (recommended)
- Pygame (not currently pinned in a `requirements.txt` — install manually):

  ```bash
  pip install pygame
  ```

  Adding a `requirements.txt` with a pinned Pygame version would be a nice future
  improvement to this repo.

## How to Run

```bash
pip install pygame
python warpgate/main.py
```

The game needs a real display to run (it opens a window via SDL/Pygame). For
headless environments (e.g. CI or automated testing), `warpgate/main.py` falls
back to `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` automatically when
those environment variables aren't already set, so the game can still boot
without a display attached — though obviously there's nothing to see in that
mode.

Tested on Windows/Mac/Linux wherever Python + Pygame are available.

## Repository Layout

- `warpgate/main.py` — entry point
- `warpgate/engine/` — game loop, renderer, input, audio, and save management
- `warpgate/entities/` — characters, enemies, and party state
- `warpgate/combat/` — the turn-based battle system
- `warpgate/world/` — overworld map, towns, and dungeons
- `warpgate/data/` and `warpgate/assets/data/` — data loading and game
  configuration (classes, spells, etc.)

Various tile/sprite assets and free asset packs (Kenney.nl, Dungeon Crawl Stone
Soup) are bundled at the repo root for use by the renderer.

This repo also ships a `.gitignore` for Python build artifacts and save files.

## License

MIT — see [LICENSE](LICENSE).
