# WARPGATE: Chronicles of the 41st Millennium

A Warhammer 40K-themed retro RPG built in Python with Pygame. Recruit a warband of elite Imperial units, explore the ash wastes of Armageddon, and battle the forces of Chaos in turn-based tactical combat.

## What This Is

**WARPGATE** is a full-featured turn-based RPG inspired by classic Final Fantasy and Tactics games, set in the Warhammer 40,000 universe. Lead a party of four iconic Imperial archetypes through multiple dungeons and story-driven encounters. Features include multi-floor dungeons, strategic turn-based combat with resource management, extensive equipment and item systems, and a corruption mechanic that escalates as you face darker threats.

### Stack
- **Language:** Python 3
- **Framework / Runtime:** Pygame
- **Notable Libraries:** Pygame (rendering/audio/input)
- **Data:** JSON-based configuration files for items, enemies, spells, and story

## How It's Organized

```
warpgate/
  main.py                 Entry point, initializes Pygame and Game loop
  constants.py            All game configuration: colors, tile IDs, status effects,
                          enemy AI types, story flags, character classes, resources
  
  engine/
    game.py               Main game state machine (1200+ lines). Handles all game
                          states (TITLE, CLASS_SELECT, WORLD, DUNGEON, BATTLE, etc.)
                          and transitions between them
    renderer.py           Pygame rendering layer. Draws UI, battle screens, menus,
                          sprites, dialogues, particle effects (damage floats)
    sprites.py            Sprite classes for animated characters and enemies
    input_handler.py      Keyboard input handling (arrow keys, confirm, cancel)
    audio_manager.py      Music and sound effect playback
    save_manager.py       Serialization / deserialization of game state
  
  entities/
    character.py          Party member class. Tracks HP, mana (Warp/Faith), stats,
                          abilities, equipment, status effects
    enemy.py              Enemy class. AI decision-making, attack patterns, drops,
                          split mechanics (e.g., Pink Horror → Blue Horrors)
    party.py              Party container, inventory, morale, corruption tracking
  
  combat/
    battle.py             Turn-based battle engine. Handles action resolution, damage
                          calculation, buffs/debuffs, status effects, special abilities,
                          enemy AI actions, loot distribution
  
  world/
    world_map.py          64x64 tile grid map with locations (towns, dungeons, shrines)
    dungeon.py            Multi-floor dungeon generation with treasure chests and bosses
    town.py               Town layouts with NPCs, shops, shrines
    tile.py               Tile type definitions and properties
  
  data/
    loader.py             Loads item, enemy, story, and spell data from JSON config files
    config/
      (referenced but not shown: item definitions, enemy stats, spells, story text)
  
  assets/
    (image and audio files, plus sprite tilesets)
  
  saves/                  Player save data (3 slots)

```

**How it fits together:** The game runs a 60 FPS loop in `Game.run()`. Each frame updates the current state (world exploration, battle, menus, dialogue) and renders the result. Players explore a world map, enter dungeons, fight random and boss encounters, manage party resources (HP, Warp charges, Faith points, items), and progress through a story unlocked by completing dungeons. Combat uses a turn-order system based on agility, with player-selected actions (attack, spells/rites, items) resolved against AI-controlled enemies. Buffs, debuffs, status effects, and boss mechanics (phase transitions, special abilities) add tactical depth.

## How to Run It

### Requirements
- Python 3.7+
- Pygame

### Installation & Running

```bash
# Install dependencies
pip install pygame

# Run the game
python warpgate/main.py
```

The game launches in fullscreen-windowed mode at 768×672 (256×224 internal resolution scaled 3×). A dummy SDL audio driver is used if audio hardware is unavailable.

### Controls
- **Arrow Keys:** Move (world/town/dungeon), navigate menus
- **Z / Enter:** Confirm selection
- **X / Escape:** Cancel / open menu
- **Q:** Exit game (from title screen)

### Game Flow
1. **Title Screen** → Press Z to start
2. **Class Select** → Pick four characters from six classes (Astartes, Inquisitor, Psyker, Sister, Tech-Priest, Commissar)
3. **World Exploration** → Move across the Ash Wastes. Visit towns for shops and NPCs. Enter dungeons (gated by story progression)
4. **Dungeons** → Multi-floor crawls. Fight random encounters, open chests (XP, items, gelt), reach boss at the end
5. **Battle** → Turn-based combat. Choose actions for each party member, resolve enemy turns, collect rewards
6. **Story Progression** → Defeat bosses to unlock new dungeons and advance toward the ending

### Save/Load
- **In-game Menu** → "SAVE" or press Escape to access save screen
- Saves to `warpgate/saves/` (3 slots max)
- Load on title screen with Z / Escape key

## Features

### Character System
- **Six Classes:** Each with unique abilities, resource types (Warp, Faith, cooldowns), and stat growth
  - Astartes: Tank, high damage
  - Inquisitor: Hybrid, versatile abilities
  - Psyker: Mage, Warp resource (risk of "Perils of the Warp")
  - Sister: Healer, Faith resource, Miraculous Intervention passive
  - Tech-Priest: Utility/repair, random buffs from Omnissiah
  - Commissar: Morale/support, blocks cowardly retreat

### Combat Mechanics
- **Resources:** HP, Warp Charges (psykers), Acts of Faith (sisters), cooldowns
- **Status Effects:** Plague, Psychic Static, Catatonia, Synaptic Lock, Warp Madness, Blood Rage, Vaporization, Crystallization, Vox-Jammed, Rout
- **Buffs/Debuffs:** Damage reduction, physical immunity, stat boosts, strength debuffs, status immunity
- **Damage Types:** Physical, Fire, Holy, Warp, Sonic — some abilities trigger special effects (e.g., Holy damage on daemons)
- **Boss Mechanics:** Phase transitions (Ghazghkull), special abilities (Waaagh! charge, summoning), resource management

### Equipment & Items
- **Slots:** Helm, Body, Main Hand, Off-hand, Relic
- **Consumables:** Stimm injectors, grenades, sacred ungents, warp dust
- **Weapons:** Bolt pistols, force staves, laspistols, omnissian axes — with special properties (overheat, status infliction, relic bonuses)
- **Shop System:** Buy gear with gelt (currency)

### World Building
- **64×64 tile-based world map** with varied terrain: wasteland, ash, rubble, road, toxic sea, dungeon floor, town, walls, doors, chests, shrines, bridges, grass, water, rock, cement, stairs
- **Encounter Rates:** Different regions have different monster pools (Ash Wastes, Encampment, Fungal Caves, Manufactorum, Iron Fortress, Rok)
- **Towns:** Safe zones with NPCs, dialogue, shops, shrines (restore party)
- **Dungeons:** Multi-floor challenge zones with bosses and key items
- **Progression Gating:** Bosses unlock new dungeon access

### Story Elements
- **Story Flags:** Track completion (intro, encampment clear, caves clear, etc.)
- **Dialogue System:** NPC portraits, multi-page conversations, branching dialogue returns
- **Transmission Sequences:** Story cutscenes that play between major events
- **Ending Choices:** Sacrifice or Gambit — influences final scenes

### Corruption & Morale
- **Corruption:** Tracks Chaos influence. High corruption (≥25%) causes random status effects in combat
- **Morale:** Affects party damage. Commissar prevents retreat if low. Boosted by victory, reduced by party member deaths

## Try Asking

- How does the turn-order system in Battle calculate agility-based ordering?
- What happens if a Psyker rolls snake eyes on Perils of the Warp?
- How does the Sister's Miraculous Intervention passive prevent a KO?
- Can you explain how boss phase transitions work (e.g., Ghazghkull Phase 1 → Phase 2)?

---

**Made with Python and Pygame.**  
Set in the Warhammer 40,000 universe. Inspired by Final Fantasy and Tactics Ogre.

Throne Gelt awaits, warrior. For the Emperor.
