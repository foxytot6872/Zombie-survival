# Zombie Survival Game - Current Status

## Game Overview
- **Genre**: Tower Defense / Survival
- **Engine**: Pygame
- **Resolution**: 1920x1080 (configurable via constants.py)
- **Language**: Python 3.9+

## Core Systems

### Resources
- **Wood**: Basic building material
- **Iron**: Advanced building material  
- **Food**: Resource for survivors
- **Coins**: Currency dropped by zombies, used for research

### Research System
- **Research Button**: Located at top-left of screen
- **Research Panel**: Modal window showing available research
- **Research Items**:
  - Unlock Sawmill (25 coins)
  - Unlock Smelter (40 coins)
  - Tier 2 Turret (60 coins)
  - Railgun Turret (100 coins)
- **Unlock Mechanism**: Buildings hidden until researched, then appear in build menu

### Day Random Event System (NEW)
- **Event Trigger**: One random event rolls at the start of each day
- **Event Types**:
  - **Lucky Day**: +50% resource production
  - **Scrap Jackpot**: +50% coin drops from zombies
  - **Exhausted Workers**: -25% production
  - **Supply Shortage**: +25% building costs
  - **Overclock Turrets**: +25% fire rate, +10% damage taken
- **Event Display**: Banner notification shows "Day X – [Event Name]: [Description]"
- **Modifier System**: Temporary modifiers affect gameplay throughout the day
- **Auto-Clear**: Effects automatically reset when next day starts
- **No Event Chance**: 20% chance of no event (keeps events special)

### Wave System
- **Day/Night Cycle**: Alternates between day (resource gathering) and night (zombie waves)
- **Wave Manager**: Handles wave progression, difficulty scaling
- **Spawner**: Manages enemy spawning with configurable intervals and batch sizes

## Starting Layout (NEW)

### Initial Setup
- **HQ Position**: Center of screen
- **Wall Compound**: Rectangular walls surrounding HQ (4-tile padding)
- **Gate**: Located at bottom-center of compound (allows survivor passage)
- **Turrets**: Positioned outside walls:
  - 3 turrets on top side
  - 2 turrets on bottom side (avoiding gate area)
  - 1 turret on left side
  - 1 turret on right side
- **Resource Nodes**: Spawn in clusters around the compound:
  - Top-left cluster: Trees (wood)
  - Top-right cluster: Scrap (iron)
  - Bottom-left cluster: Scrap (iron)
  - Bottom-right cluster: Trees (wood)
  - Nodes maintain minimum distance from compound and each other

## Buildings

### Defensive Buildings
1. **HQ (Headquarters)**
   - 2x2 footprint
   - 2000 HP
   - Uses `base.png` sprite
   - Auto-repairs during day
   - Cannot be sold
   - HP bar always visible
   - Positioned at center of starting compound

2. **Ballistic Turret**
   - 1x1 footprint
   - Tier system (1-3)
   - Tier-specific base images and firing animations (4 frames each)
   - Sprite sheets: `Turret_lv1.png`, `Turret_lv2.png`, `Turret_lv3.png`
   - Base images: `Base_lv1.png`, `Base_lv2.png`, `Base_lv3.png`
   - Fire rate affected by day event modifiers

3. **Gatling Turret**
   - 1x1 footprint
   - Static image (not animated)
   - Uses `Gatling_Base_lv1.png` and `Gatling_lv1.png`

4. **Piercer Turret (Railgun)**
   - 1x1 footprint
   - Tier system (1-3)
   - 8-frame firing animation (64x64 pixels per frame)
   - Projectile fires on last frame only
   - Slower animation speed (200ms per frame)
   - Sprite sheets: `Railgunturret_lv1.png`, `Railgunturret_lv2.png`, `Railgunturret_lv3.png`
   - Base images: `Railgunbase_lv1.png`, `Railgunbase_lv2.png`, `Railgunbase_lv3.png`
   - **Requires Research**: "railgun_turret" unlock
   - Fire rate affected by day event modifiers

5. **Wall**
   - 1x1 footprint
   - Autotiling system
   - Variants: Wood Wall, Iron Wall
   - Can upgrade wood → iron
   - Forms compound perimeter at game start

6. **Gate**
   - 1x1 footprint
   - Allows passage (not fully blocking)
   - Positioned at bottom-center of starting compound

### Resource Buildings
1. **Farm**
   - 1x1 footprint
   - Produces food passively
   - Always available
   - Production affected by day event modifiers

2. **Sawmill**
   - 1x1 footprint
   - Produces wood passively
   - **Requires Research**: "sawmill" unlock
   - Production affected by day event modifiers

3. **Smelter**
   - 1x1 footprint
   - Produces iron passively
   - **Requires Research**: "smelter" unlock
   - Production affected by day event modifiers

### Building Upgrade System
- **Progress-Based Upgrades**: Buildings require 3 upgrade steps before tier increases
- **Upgrade Panel**: Uses `upgrade_1-2_panel.png` (3 frames showing progress: 0%, 33%, 66%)
- **Darkened Variant**: `upgrade_1-2_panel_darken.png` shown when can't afford or hovering
- **Clickable Area**: Only specific region (62,216) to (318,332) triggers upgrade
- **Cost Scaling**: Upgrade cost increases with tier
- **Build Cost Modifiers**: Affected by day event modifiers (e.g., Supply Shortage)

## Enemies

### Enemy Types
1. **BasicZombie (Walker)**
   - Sprite sheet: `Zombie_Normal_Sheet.png` (32 frames, 48x48 pixels)
   - Animations:
     - Idle: frames 1-4
     - Walking: frames 5-10 (flips for left movement)
     - Attacking: frames 11-19
     - Hurt: frames 20-23
     - Death: frames 24-32 (plays once, zombie removed after completion)
   - Coin drop: 2 coins (affected by day event modifiers)
   - Death animation must complete before removal

2. **RunnerZombie**
   - Faster variant
   - Coin drop: 3 coins (affected by day event modifiers)

3. **BruteZombie**
   - Tank variant
   - Coin drop: 5 coins (affected by day event modifiers)

4. **SpitterZombie**
   - Ranged attacker
   - Coin drop: 4 coins (affected by day event modifiers)

5. **SwarmlingZombie**
   - Weak but numerous
   - Coin drop: 1 coin (affected by day event modifiers)

### Enemy Behavior
- Pathfinding to HQ
- Separation behavior (avoid overlapping)
- Attack buildings in range
- Death animations (BasicZombie has full animation sequence)
- Building damage affected by day event modifiers

## UI Systems

### HUD (Heads-Up Display)
- **Top-Right**: Day/Night counter, Zombie count
- **Top-Center**: HQ HP bar (always visible)
- **Event Banners**: Fade in/out notifications (used for day events)

### Building Panel
- **Location**: Bottom-right corner
- **Features**:
  - Building info (name, HP, tier)
  - Upgrade panel with progress visualization
  - Upgrade button uses custom sprite with clickable region
  - Repair and Sell buttons (currently moved elsewhere per user request)

### Research Panel
- **Modal Window**: Semi-transparent overlay
- **Features**:
  - Lists all available research
  - Shows coin cost
  - Unlock buttons (green if affordable, gray if not)
  - "Unlocked" status for purchased research
  - ESC key or click outside to close

### Building Buttons (NEW LAYOUT)
- **Location**: Bottom-left of screen
- **Layout**: Horizontal (left to right)
- **Spacing**: 105 pixels between buttons (100px width + 5px gap)
- **Position**: 10px from bottom, 10px from left
- **Dynamic**: Buttons rebuild when research unlocks new buildings

### Research Button (NEW LAYOUT)
- **Location**: Top-left of screen (10, 10)
- **Size**: 120x40 pixels
- **Function**: Opens/closes research panel

### Resource Display
- **Location**: Top-left area (x=400)
- **Shows**: Wood, Iron, Food, Coins (gold color)
- **Enemy Count**: Also displayed

### Debug System (ENHANCED)
- **Toggle**: F12 key
- **Location**: Top-left overlay panel
- **Display Info**:
  - Cursor position
  - FPS
  - Building/Enemy/Turret counts
  - Wave state, Day, Night
  - Coin count
  - Research unlock status
  - Current day event
  - Active modifiers
- **Debug Actions**:
  - **F1**: Add +100 Resources
  - **F2**: Instant Build
  - **F3**: Spawn Zombie @ Mouse
  - **F4**: Clear All Enemies
  - **F5**: Clear All Buildings
  - **F6**: Toggle Spawner
  - **F7**: Kill All Enemies
  - **F8**: Complete All Buildings
  - **1**: Add +100 Coins
  - **2**: Unlock All Research
  - **3**: Roll Day Event
  - **F9**: Skip to Night
  - **F10**: Skip to Summary
  - **F11**: Cycle Difficulty

## Visual Assets

### Sprites
- **Tree Nodes**: `Tree_node.png` (4 variations, 32x32 tiles, randomly selected per node)
- **HQ**: `base.png` (64x64, scales to fit)
- **Upgrade Panels**: `upgrade_1-2_panel.png` and `upgrade_1-2_panel_darken.png` (3 frames each, 384x386 pixels)
- **Turret Animations**: Multiple tier-specific sprite sheets
- **Zombie Animations**: Full sprite sheet with 32 frames

### Tiles
- **Grass Tiles**: `Grass_tile.png` (3 variations)

## Game Mechanics

### Building Placement
- Grid-based system (32x32 pixel tiles)
- Preview ghost when in build mode
- Resource cost checking (affected by day event modifiers)
- Collision detection
- Construction time system

### Combat
- Turrets target nearest enemies
- Projectile system for ranged attacks
- Enemy attack buildings in range
- HP system for all buildings
- Turret fire rate affected by day event modifiers
- Building damage taken affected by day event modifiers

### Resource Gathering
- **Tree Nodes**: Spawn in clusters (top-left, bottom-right)
  - Random texture variation (4 variants from sprite sheet)
  - Minimum distance from compound and other nodes
- **Scrap Piles**: Spawn in clusters (top-right, bottom-left)
  - Minimum distance from compound and other nodes
- **Daily Spawn**: Nodes spawn around the starting compound in clusters
- Worker assignment system
- Resource production affected by day event modifiers

### Day Event Modifiers
- **resource_prod_mult**: Affects Farm/Sawmill/Smelter production
- **coin_drop_mult**: Affects zombie coin drops
- **build_cost_mult**: Affects building construction costs
- **turret_fire_rate_mult**: Affects turret cooldown (lower = faster)
- **building_damage_taken_mult**: Affects damage buildings receive

### Save/Load
- Save system for game state
- Wave progress tracking
- Building persistence

## Technical Details

### File Structure
```
main.py                    # Main game loop
world/
  ├── building.py         # Base building class
  ├── buildings/          # Building implementations
  ├── enemy.py            # Base enemy class
  ├── enemies/            # Enemy implementations
  ├── resources.py       # Resource management
  ├── research.py         # Research system
  ├── map.py              # Grid system
  ├── pathfinding.py     # A* pathfinding
  ├── nodes.py            # Resource nodes
  └── debug.py            # Debug system
ui/
  ├── hud.py              # HUD display
  ├── building_panel.py   # Building info panel
  ├── research_button.py  # Research button
  ├── research_panel.py   # Research panel
  ├── game_over.py        # Game over screen
  └── pause_menu.py       # Pause menu
core/
  ├── wave_manager.py     # Wave system
  ├── game_state.py       # State management
  ├── save_system.py      # Save/load
  ├── sound.py            # Sound system
  └── day_events.py       # Day random event system (NEW)
data/config/
  ├── waves.json          # Wave definitions
  ├── buildings.json      # Building configs
  ├── research.json       # Research definitions
  └── nodes.json          # Node configs
```

### Key Features
- Object-oriented design with inheritance
- Sprite-based rendering
- Animation systems (turret firing, zombie states)
- Tier-based upgrades with progress system
- Research-based unlock system
- Coin economy from zombie kills
- Wave-based enemy spawning
- Day/night cycle
- Resource management
- Building construction and upgrades
- Day random event system with modifiers
- Clustered resource node spawning
- Centered compound starting layout

## Recent Changes
1. ✅ Research system implementation
2. ✅ Coin currency and zombie drops
3. ✅ Building unlock system
4. ✅ Research UI (button + panel)
5. ✅ Upgrade progress system (3-step progression)
6. ✅ Zombie sprite sheet integration
7. ✅ Death animation completion before removal
8. ✅ Tier-specific turret assets
9. ✅ HQ sprite integration
10. ✅ Day random event system (NEW)
11. ✅ Debug tool enhancements (NEW)
12. ✅ UI layout reorganization (NEW)
13. ✅ Centered compound starting layout (NEW)
14. ✅ Clustered resource node spawning (NEW)

## Current State
- **Playable**: Yes
- **Core Systems**: Complete
- **Research System**: Fully functional
- **Day Event System**: Fully functional
- **Starting Layout**: Centered compound with walls and turrets
- **Resource Spawning**: Clustered around compound
- **Visual Assets**: Mostly integrated
- **Balance**: Tuning in progress
