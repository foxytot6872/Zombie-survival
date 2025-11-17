# 🎮 Game Balance Configuration Guide

This guide shows you **exactly where to adjust** every game balance value.

---

## 📁 **JSON Configuration Files** (`data/config/`)

These files control most game balance and are **easy to edit**:

### 1. **`buildings.json`** - Building Stats
**Location:** `data/config/buildings.json`

**What to adjust:**
- Building costs (wood, iron, food, coins)
- Base HP (`base_hp`)
- Build time (`build_time`)
- Production rates (`production.wood_per_min`, `iron_per_min`, `food_per_min`)
- Repair costs (`repair_cost.wood_per_hp`)

**Example:**
```json
{
  "farm": {
    "cost": {"wood": 60},
    "production": {"food_per_min": 120}  // ← Change food production here
  },
  "sawmill": {
    "cost": {"wood": 50, "iron": 10},
    "production": {"wood_per_min": 120}  // ← Change wood production here
  },
  "hq": {
    "base_hp": 2000,  // ← Change HQ HP here
    "build_time": 0.0
  }
}
```

**Buildings in this file:**
- `farm` - Food production
- `sawmill` - Wood production
- `smelter` - Iron production
- `wall` - Basic wall stats
- `hq` - Headquarters HP
- `gate` - Gate stats
- `housing` - Housing stats
- `turret_ballistic` - Basic turret stats

---

### 2. **`turrets.json`** - Turret Combat Stats
**Location:** `data/config/turrets.json`

**What to adjust:**
- Turret costs
- Base HP (`base_hp`)
- Build time (`build_time`)
- **Range** (`range`) - Attack range in pixels
- **Damage** (`damage`) - Damage per shot
- **Cooldown** (`cooldown`) - Milliseconds between shots (lower = faster)
- Projectile speed (`projectile_speed`)
- Pierce settings (`pierce`, `pierce_count`)

**Example:**
```json
{
  "turret_ballistic": {
    "range": 200,        // ← Attack range (pixels)
    "damage": 10,        // ← Damage per shot
    "cooldown": 1700,    // ← Milliseconds between shots (1700ms = 1.7s)
    "projectile_speed": 400
  },
  "turret_gatling": {
    "range": 150,
    "damage": 5,         // ← Lower damage, but...
    "cooldown": 300,     // ← ...much faster (300ms = 0.3s)
    "projectile_speed": 500
  },
  "turret_piercer": {
    "range": 250,
    "damage": 25,        // ← High damage
    "cooldown": 2000,    // ← Slow firing
    "pierce": true,
    "pierce_count": 3    // ← Pierces 3 enemies
  }
}
```

---

### 3. **`walls.json`** - Wall Stats
**Location:** `data/config/walls.json`

**What to adjust:**
- Wall costs (`cost`)
- Base HP (`base_hp`)
- Build time (`build_time`)
- Upgrade costs (`upgrade_cost`)

**Example:**
```json
{
  "wall_wood": {
    "base_hp": 250,      // ← Wood wall HP
    "build_time": 1.0,
    "cost": {"wood": 30}
  },
  "wall_iron": {
    "base_hp": 600,      // ← Iron wall HP
    "build_time": 0.8,
    "upgrade_cost": {"wood": 10, "iron": 40}
  }
}
```

---

### 4. **`waves.json`** - Wave Spawning & Timing
**Location:** `data/config/waves.json`

**What to adjust:**
- Enemy spawn composition per night (`nights[].mix`)
- Difficulty multipliers (`difficulty.easy/normal/hard`)
- Wave scaling (`increment.per_night_mult`) - Multiplier per night
- Spawn timing (`spawn.interval_sec`, `spawn.batch_size`)
- Phase durations (`day_duration`, `summary_duration`)
- Win condition (`win_nights`)

**Example:**
```json
{
  "difficulty": {
    "easy": 0.85,      // ← Easy mode: 85% enemy count
    "normal": 1.0,     // ← Normal: 100%
    "hard": 1.5        // ← Hard: 150% enemy count
  },
  "nights": [
    {"mix": {"walker": 12}},                    // Night 1
    {"mix": {"walker": 16, "runner": 6}},       // Night 2
    {"mix": {"walker": 20, "runner": 8, "brute": 2}}  // ← Edit enemy counts here
  ],
  "increment": {
    "per_night_mult": 1.12  // ← Each night: +12% more enemies (1.12×)
  },
  "spawn": {
    "interval_sec": 1.0,    // ← Spawn every 1 second
    "batch_size": 2         // ← 2 enemies per spawn
  },
  "day_duration": 30.0,     // ← Day phase: 30 seconds
  "summary_duration": 5.0,  // ← Summary phase: 5 seconds
  "win_nights": 10          // ← Win after 10 nights
}
```

---

### 5. **`survivors.json`** - Survivor Stats
**Location:** `data/config/survivors.json`

**What to adjust:**
- HP (`hp`)
- Speed (`speed`) - Pixels per second
- Carry capacity (`carry_capacity`)
- Guard stats (`range`, `ranged_dmg`, `cooldown`)

**Example:**
```json
{
  "worker": {
    "hp": 100,              // ← Worker HP
    "speed": 90,            // ← Movement speed (pixels/sec)
    "carry_capacity": 40    // ← Max resources carried
  },
  "guard": {
    "hp": 120,
    "speed": 85,
    "range": 160,           // ← Attack range
    "ranged_dmg": 8,        // ← Damage per shot
    "cooldown": 0.8         // ← Seconds between shots
  }
}
```

---

### 6. **`nodes.json`** - Resource Node Stats
**Location:** `data/config/nodes.json`

**What to adjust:**
- Total yield (`yield_total`)
- Gather per tick (`gather_per_tick`)
- Tick duration (`tick_sec`)
- Daily spawn counts (`daily_spawn.trees`, `daily_spawn.scrap`)

**Example:**
```json
{
  "tree_patch": {
    "resource": "wood",
    "yield_total": 120,      // ← Total wood per tree
    "gather_per_tick": 6,    // ← Wood per gather action
    "tick_sec": 0.6          // ← Seconds per gather
  },
  "scrap_pile": {
    "resource": "iron",
    "yield_total": 100,
    "gather_per_tick": 5,
    "tick_sec": 0.7
  },
  "daily_spawn": {
    "trees": 4,              // ← Trees spawned per day
    "scrap": 3,              // ← Scrap piles per day
    "min_dist_from_wall_px": 96
  }
}
```

---

### 7. **`research.json`** - Research Costs & Modifiers
**Location:** `data/config/research.json`

**What to adjust:**
- Research costs (`cost`)
- Research tiers (`tier`)
- Prerequisites (`prerequisites`)
- Modifiers (`modifiers`) - Multiplicative bonuses
- Unlocks (`unlocks`)

**Example:**
```json
{
  "basic_woodworking": {
    "cost": 100,             // ← Research cost in coins
    "tier": 2,
    "prerequisites": ["agriculture"],
    "unlocks": ["sawmill"],
    "modifiers": {
      "resource_prod_mult": 1.10  // ← +10% resource production
    }
  },
  "recruitment": {
    "cost": 180,
    "modifiers": {
      "max_survivors": 2     // ← +2 max survivors (additive)
    }
  }
}
```

---

### 8. **`build_items.json`** - Build Menu Items
**Location:** `data/config/build_items.json`

**What to adjust:**
- Display names (`name`)
- Descriptions (`description`)
- Base costs (`base_cost`)
- Research requirements (`requires`)

**Note:** Actual stats come from `buildings.json`, `turrets.json`, etc. This file only controls the build menu.

---

### 9. **`startup.json`** - Game Startup Settings
**Location:** `data/config/startup.json`

**What to adjust:**
- Grid settings
- Initial configurations

---

## 🐍 **Python Configuration Files**

### 10. **`difficulty_config.py`** - Difficulty Settings
**Location:** `difficulty_config.py`

**What to adjust:**
- Starting resources per difficulty
- Resource production multipliers
- Build cost multipliers
- Research cost multipliers

**Example:**
```python
DIFFICULTY_CONFIG: Dict[Difficulty, DifficultySettings] = {
    Difficulty.EASY: DifficultySettings(
        starting_resources={"wood": 500, "iron": 500, "food": 500},  # ← Starting resources
        sawmill_yield_multiplier=1.0,     # ← Sawmill production multiplier
        smelter_yield_multiplier=1.0,     # ← Smelter production multiplier
        build_cost_multiplier=0.75,       # ← Buildings cost 75% (cheaper)
        research_cost_multiplier=1.0,     // ← Research costs normal
    ),
    # ... other difficulties
}
```

---

### 11. **`upgrade_config.py`** - Upgrade Costs
**Location:** `upgrade_config.py`

**What to adjust:**
- Turret upgrade costs per tier
- Difficulty multipliers for upgrades

**Example:**
```python
TURRET_UPGRADE_CONFIG: Dict[str, list] = {
    "tier_1": [
        {"step": 1, "base_cost": {"wood": 30, "iron": 10}},  // ← First upgrade cost
        {"step": 2, "base_cost": {"wood": 50, "iron": 20}},  // ← Second upgrade cost
    ],
    # ...
}

DIFFICULTY_UPGRADE_MULTIPLIER: Dict[Difficulty, float] = {
    Difficulty.EASY: 0.5,      // ← Easy: 50% upgrade cost
    Difficulty.MEDIUM: 1.0,
    Difficulty.HARD: 2.0,      // ← Hard: 200% upgrade cost
}
```

---

## ⚙️ **Hardcoded Values** (Require Code Editing)

### 12. **Enemy Stats** - In Python Files
**Location:** `world/enemies/*.py`

**Files:**
- `world/enemies/zombie.py` - Basic zombie
- `world/enemies/runner.py` - Runner zombie
- `world/enemies/brute.py` - Brute zombie
- `world/enemies/spitter.py` - Spitter zombie
- `world/enemies/swarmling.py` - Swarmling zombie
- `world/enemies/skeleton.py` - Skeleton
- `world/enemies/archer_skeleton.py` - Archer skeleton
- `world/enemies/warrior_skeleton.py` - Warrior skeleton

**What to adjust:**
```python
class BasicZombie(Enemy):
    BASE_HP = 50          # ← Enemy HP
    SPEED = 30.0          # ← Movement speed (pixels/sec)
    DAMAGE = 5            # ← Attack damage
    ATTACK_RANGE = 32.0   # ← Attack range (pixels)
    ATTACK_COOLDOWN = 1.0 # ← Seconds between attacks
```

**For ranged enemies:**
```python
class SpitterZombie(Enemy):
    RANGED_DAMAGE = 12           # ← Ranged attack damage
    PROJECTILE_SPEED = 200.0     # ← Projectile speed
```

---

### 13. **Coin Rewards** - In `main.py`
**Location:** `main.py` around line 3898-3910

**What to adjust:**
```python
# Drop coins based on enemy difficulty/type
base_reward = 2
type_rewards = {
    "walker": 2,              # ← Basic zombie reward
    "runner": 3,              # ← Runner reward
    "brute": 5,               # ← Brute reward
    "spitter": 4,             # ← Spitter reward
    "swarmling": 1,           # ← Swarmling reward
    "skeleton": 3,            # ← Skeleton reward
    "archer_skeleton": 4,     # ← Archer reward
    "warrior_skeleton": 5     # ← Warrior reward
}
```

---

### 14. **Hire Survivor Cost** - In `main.py`
**Location:** `main.py` around line 2991

**What to adjust:**
```python
HIRE_SURVIVOR_COST = 50  # ← Cost to hire a new survivor (coins)
```

---

### 15. **Food Consumption** - In `main.py`
**Location:** `main.py` around line 3722

**What to adjust:**
```python
food_needed = alive_survivors  # ← 1 food per survivor per day
# Change to: food_needed = alive_survivors * 2  # 2 food per survivor
```

---

### 16. **Enemy Separation/Collision** - In `world/enemy.py`
**Location:** `world/enemy.py` around lines 80-88

**What to adjust:**
```python
class Enemy:
    ZOMBIE_RADIUS: float = 12.0           # ← Enemy collision radius
    SEPARATION_PUSH: float = 80.0         # ← Push force for separation
    SEPARATION_MAX_NEIGHBORS: int = 8     # ← Max neighbors to check
    SEPARATION_RANGE: float = 40.0        # ← Separation check range
    STUCK_TIME_THRESHOLD: float = 2.0     # ← Time before retargeting when stuck
```

---

### 17. **Survivor Separation/Collision** - In `world/survivor.py`
**Location:** `world/survivor.py`

**What to adjust:**
```python
class Survivor:
    SURVIVOR_RADIUS: float = 10.0         # ← Survivor collision radius
    SEPARATION_PUSH: float = 70.0         # ← Push force for separation
    SEPARATION_MAX_NEIGHBORS: int = 8     # ← Max neighbors to check
    SEPARATION_RANGE: float = 40.0        # ← Separation check range
```

---

## 📊 **Quick Reference: What File Controls What**

| **Balance Aspect** | **File Location** |
|-------------------|-------------------|
| Building costs/HP/production | `data/config/buildings.json` |
| Turret combat stats | `data/config/turrets.json` |
| Wall stats | `data/config/walls.json` |
| Wave composition & scaling | `data/config/waves.json` |
| Survivor stats | `data/config/survivors.json` |
| Resource node yields | `data/config/nodes.json` |
| Research costs/modifiers | `data/config/research.json` |
| Difficulty settings | `difficulty_config.py` |
| Upgrade costs | `upgrade_config.py` |
| Enemy stats (HP/speed/damage) | `world/enemies/*.py` (Python files) |
| Coin rewards | `main.py` line ~3898 |
| Hire survivor cost | `main.py` line ~2991 |
| Food consumption | `main.py` line ~3722 |
| Collision/separation | `world/enemy.py`, `world/survivor.py` |

---

## 🔧 **Recommended Balance Adjustment Workflow**

1. **Start with JSON files** - Easiest to edit, no code changes needed
2. **Test changes** - Run the game and see the impact
3. **Fine-tune with Python** - Adjust hardcoded values if needed

---

## 💡 **Tips**

- **Backup before editing** - Save a copy of config files
- **One change at a time** - Test incrementally
- **JSON syntax matters** - Use commas correctly, no trailing commas on last item
- **Restart game** - Changes take effect on restart (no hot-reload)

---

## 🎯 **Common Balance Tweaks**

### Make game easier:
- Lower enemy HP in `world/enemies/*.py`
- Increase coin rewards in `main.py`
- Lower building costs in `buildings.json`
- Increase production rates in `buildings.json`

### Make game harder:
- Increase enemy spawns in `waves.json`
- Increase `per_night_mult` in `waves.json`
- Lower production rates in `buildings.json`
- Increase build costs in `buildings.json`

### Speed up gameplay:
- Reduce `day_duration` in `waves.json`
- Increase production rates in `buildings.json`
- Reduce build times in `buildings.json`

### Slow down gameplay:
- Increase `day_duration` in `waves.json`
- Lower production rates in `buildings.json`
- Increase build times in `buildings.json`

