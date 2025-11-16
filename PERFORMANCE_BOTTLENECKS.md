# Performance Bottlenecks Analysis

## 🔴 CRITICAL ISSUES (Causing Lag)

### 1. **Pathfinding in Enemy Target Selection** (MAJOR BOTTLENECK)
**Location:** `world/enemy.py:645-671` in `choose_target()`

**Problem:**
- Every enemy calls `choose_target()` every 0.25 seconds (target_evaluation_interval)
- Each `choose_target()` can call `find_path()` multiple times (up to 5 turrets + 3 walls + HQ)
- `find_path()` uses A* pathfinding - **very expensive** (can check hundreds of tiles)
- **With 200 enemies:**
  - 200 enemies × 1 call per 0.25s = **800 pathfinding calls per second**
  - Each pathfinding call can check 50-200+ tiles
  - **Estimated: 40,000-160,000 tile checks per second**

**Impact:** 🔴 **CRITICAL** - This is likely causing 70-90% of lag

**Current Code:**
```python
# Lines 645-671 in enemy.py
if pathfinding and hasattr(building, 'grid_x') and hasattr(building, 'grid_y'):
    cache_key = (int(self.pos.x // 32), int(self.pos.y // 32), building.grid_x, building.grid_y)
    if cache_key in self.pathfinding_cache:
        has_path = self.pathfinding_cache[cache_key]
    else:
        # EXPENSIVE: Calls A* pathfinding
        path = pathfinding.find_path(start_grid, goal_grid, ignore_walls=ignore_walls, allow_gates=False)
        has_path = path is not None
        self.pathfinding_cache[cache_key] = has_path
```

**Solutions:**
1. **Use collision map instead of pathfinding** for "is reachable" checks
2. **Reduce pathfinding frequency** - only check when target changes significantly
3. **Limit pathfinding to top 1-2 candidates** instead of checking all 5 turrets
4. **Use simpler distance checks** for most cases, only pathfind for final target

---

### 2. **Enemy-Survivor Collision Check** (O(n×m))
**Location:** `main.py:4011-4025`

**Problem:**
- Checks EVERY enemy against EVERY survivor every frame
- **With 200 enemies and 10 survivors: 2000 collision checks per frame (120,000 per second at 60 FPS)**

**Current Code:**
```python
for survivor in survivor_group:
    for enemy in world.enemy_group:  # Nested loop!
        if enemy.alive:
            enemy_dist = (survivor.pos - enemy.pos).length()
            # ... collision handling
```

**Impact:** 🔴 **HIGH** - O(enemies × survivors) complexity

**Solutions:**
1. **Use spatial grid** for enemy-survivor collision (already built at line 3833!)
2. **Only check nearby enemies** (same cell + 8 surrounding cells)
3. **Cooldown on collision checks** (check every 2-3 frames instead of every frame)

---

### 3. **Multiple Building Group Loops**
**Location:** Throughout `main.py`

**Problem:**
- Looping over `building_group` multiple times per frame:
  - Line 3584: Building updates
  - Line 3717: Finding HQ (could cache this)
  - Line 4068: Drawing buildings
  - Line 4076: Debug footprints
  - Line 4170: Building selection highlights

**Impact:** 🟡 **MEDIUM** - With 100+ buildings, multiple full loops add up

**Solutions:**
1. **Cache HQ reference** - don't search every time
2. **Combine loops** where possible
3. **Only iterate active buildings** when possible

---

### 4. **Survivor Pathfinding**
**Location:** `world/survivor.py` in `move_toward()`

**Problem:**
- Survivors recalculate paths frequently (every 0.5s or when target moves >32px)
- A* pathfinding is expensive
- **With 10 survivors: up to 20 pathfinding calls per second**

**Impact:** 🟡 **MEDIUM** - Less severe than enemy pathfinding, but still significant

**Solutions:**
1. **Increase path recalculation interval** (1.0s instead of 0.5s)
2. **Increase movement threshold** (64px instead of 32px)
3. **Limit pathfinding distance** - don't pathfind for very long paths

---

### 5. **Spatial Grid Rebuilt Every Frame**
**Location:** `main.py:3833-3837`

**Problem:**
- Rebuilding spatial grid from scratch every frame
- Allocating new SpatialGrid object each frame

**Impact:** 🟢 **LOW-MEDIUM** - Less severe, but inefficient

**Solutions:**
1. **Reuse spatial grid** - clear and rebuild instead of creating new object
2. **Only rebuild when needed** (enemy count changed significantly)

---

## 📊 Performance Impact Estimate

| Issue | Estimated CPU Impact | Priority |
|-------|---------------------|----------|
| Enemy Pathfinding | 70-90% of lag | 🔴 **CRITICAL** |
| Enemy-Survivor Collision | 5-10% of lag | 🔴 **HIGH** |
| Building Loops | 2-5% of lag | 🟡 **MEDIUM** |
| Survivor Pathfinding | 2-5% of lag | 🟡 **MEDIUM** |
| Spatial Grid Rebuild | 1-2% of lag | 🟢 **LOW** |

---

## ✅ Recommended Fixes (Priority Order)

### Fix 1: Replace Pathfinding with Collision Map Checks
**Effort:** Medium | **Impact:** 🔴 **CRITICAL**

Instead of calling `find_path()`, use a simple flood-fill or raycast to check reachability:
```python
# Simple reachability check using collision map
def is_reachable(collision_map, start, goal, max_distance=100):
    # Use simple raycast or limited flood-fill
    # Much faster than full A* pathfinding
```

### Fix 2: Use Spatial Grid for Enemy-Survivor Collision
**Effort:** Low | **Impact:** 🔴 **HIGH**

The spatial grid is already built! Just use it:
```python
# Line 4011 - REPLACE with:
for survivor in survivor_group:
    nearby_enemies = spatial_grid.get_nearby(survivor.pos, radius_cells=1)
    for enemy in nearby_enemies:
        # ... collision check
```

### Fix 3: Reduce Pathfinding Frequency
**Effort:** Low | **Impact:** 🟡 **MEDIUM**

Only pathfind for top 1-2 candidates, not all 5 turrets + 3 walls.

### Fix 4: Cache HQ Reference
**Effort:** Very Low | **Impact:** 🟡 **LOW**

Store `world.hq` instead of searching every time.

---

## 🚀 Quick Wins (Easy Fixes)

1. **Line 4011:** Use spatial grid for enemy-survivor collision (already built!)
2. **Line 3717:** Cache HQ reference (search once, reuse)
3. **Line 3833:** Reuse spatial grid object instead of creating new one
4. **world/enemy.py:677:** Reduce turret candidates from 5 to 2

These 4 quick fixes alone could reduce lag by 15-25% with minimal effort.

