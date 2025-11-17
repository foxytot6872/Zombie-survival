# 🎮 Central Balance Configuration Guide

## Overview

All game balance values are now centralized in **`data/config/balance.json`**.

This file contains:
- **Base values** (normal/medium difficulty) in the `"base"` section
- **Difficulty multipliers** in the `"difficulty_multipliers"` section

Other difficulties automatically multiply base values by their multipliers.

---

## 📝 How to Edit Balance

### 1. **Edit `data/config/balance.json`**

All balance values are in one place! Simply edit the JSON file:

#### **Base Values (Normal Difficulty)**
- Edit values in `"base"` section
- These are the values for **MEDIUM/NORMAL** difficulty
- Other difficulties automatically scale from these

#### **Difficulty Multipliers**
- Edit multipliers in `"difficulty_multipliers"` section
- Multipliers are applied to base values
- Example: `"building_cost": 1.5` means buildings cost 1.5× base cost

### 2. **Save and Restart**
- Changes take effect after restarting the game
- No code changes needed!

---

## 📋 Balance Sections

### `base.buildings` - Building Stats
```json
{
  "farm": {
    "cost": {"wood": 60},           // Building cost
    "base_hp": 150,                 // Hit points
    "build_time": 3.0,              // Build time (seconds)
    "production": {"food_per_min": 120}  // Resource production
  }
}
```

### `base.turrets` - Turret Stats
```json
{
  "turret_ballistic": {
    "cost": {"wood": 40, "iron": 30},
    "base_hp": 220,
    "build_time": 2.5,
    "range": 200,                   // Attack range (pixels)
    "damage": 10,                   // Damage per shot
    "cooldown": 1700,               // Cooldown (milliseconds)
    "projectile_speed": 400         // Projectile speed
  }
}
```

### `base.enemies` - Enemy Stats
```json
{
  "walker": {
    "base_hp": 50,                  // Enemy HP
    "speed": 30.0,                  // Movement speed (pixels/sec)
    "damage": 5,                    // Attack damage
    "attack_range": 32.0,           // Attack range
    "attack_cooldown": 1.0          // Cooldown (seconds)
  }
}
```

### `base.waves` - Wave Configuration
```json
{
  "nights": [
    {"mix": {"walker": 12}},        // Night 1: 12 walkers
    {"mix": {"walker": 16, "runner": 6}}  // Night 2: 16 walkers + 6 runners
  ],
  "increment": {
    "per_night_mult": 1.12          // Each night: +12% more enemies
  },
  "spawn": {
    "interval_sec": 1.0,            // Spawn every 1 second
    "batch_size": 2                 // 2 enemies per spawn
  },
  "day_duration": 30.0,             // Day phase: 30 seconds
  "summary_duration": 5.0,          // Summary phase: 5 seconds
  "win_nights": 10                  // Win after 10 nights
}
```

### `base.economy` - Economy Settings
```json
{
  "coin_rewards": {
    "base_reward": 2,               // Default coin reward
    "walker": 2,                    // Coins per walker kill
    "brute": 5                      // Coins per brute kill
  },
  "hire_survivor_cost": 50,        // Cost to hire survivor
  "food_per_survivor_per_day": 1   // Food consumption rate
}
```

---

## 🔢 Difficulty Multipliers

All multipliers are relative to **MEDIUM** difficulty (1.0 = normal).

### Available Multipliers:
- `enemy_count` - Number of enemies spawned
- `enemy_hp` - Enemy hit points
- `enemy_damage` - Enemy attack damage
- `enemy_speed` - Enemy movement speed
- `building_cost` - Building costs
- `building_hp` - Building hit points
- `production_rate` - Resource production rates
- `coin_rewards` - Coin drops from enemies
- `research_cost` - Research costs
- `upgrade_cost` - Turret upgrade costs
- `starting_resources` - Starting wood/iron/food

### Example:
```json
"hard": {
  "enemy_count": 1.5,              // 50% more enemies
  "enemy_hp": 1.3,                 // 30% more HP
  "building_cost": 1.4,            // 40% more expensive
  "production_rate": 0.6,          // 40% less production
  "coin_rewards": 0.9,             // 10% less coins
  "starting_resources": {"wood": 150, "iron": 150, "food": 150}
}
```

---

## ✅ Benefits

1. **Single File** - All balance in one place
2. **Easy Editing** - Just edit JSON, no code changes
3. **Consistent** - Base values for normal, multipliers for others
4. **Backward Compatible** - Old config files still work as fallbacks

---

## 🔄 Migration from Old System

The old config files (`buildings.json`, `turrets.json`, etc.) still work as **fallbacks** if `balance.json` is missing or invalid.

However, for easier management, **use `balance.json`** as your single source of truth.

---

## 📚 Quick Reference

| **What to Change** | **Section in balance.json** |
|-------------------|---------------------------|
| Building costs/HP | `base.buildings.*` |
| Turret stats | `base.turrets.*` |
| Enemy stats | `base.enemies.*` |
| Wave composition | `base.waves.nights` |
| Spawn timing | `base.waves.spawn` |
| Coin rewards | `base.economy.coin_rewards` |
| Starting resources | `difficulty_multipliers.*.starting_resources` |
| Difficulty scaling | `difficulty_multipliers.*` |

---

## ⚠️ Tips

- **Edit base values** to change normal difficulty
- **Edit multipliers** to adjust difficulty scaling
- **Backup before editing** - Save a copy!
- **Check JSON syntax** - Use commas correctly
- **Restart game** - Changes take effect on restart

---

## 🎯 Example: Make Game Easier

1. Open `data/config/balance.json`
2. Find `base.economy.coin_rewards` 
3. Increase values: `"walker": 2` → `"walker": 5`
4. Find `difficulty_multipliers.hard.building_cost`
5. Lower multiplier: `1.4` → `1.2`
6. Save and restart

---

## 🎯 Example: Adjust Enemy Difficulty

1. Open `data/config/balance.json`
2. Find `base.enemies.walker.base_hp`
3. Change: `50` → `40` (20% less HP for normal)
4. Find `difficulty_multipliers.hard.enemy_hp`
5. Change: `1.3` → `1.1` (less HP scaling for hard)
6. Save and restart

---

**That's it! Happy balancing! 🎮**

