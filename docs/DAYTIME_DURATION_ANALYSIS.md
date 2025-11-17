# Daytime Duration Analysis - Complete Breakdown

## 📍 **PRIMARY DEFINITION LOCATION**

### **File: `data/config/waves.json`**
**Line: 42**

```json
{
  "day_duration": 30.0,
  "summary_duration": 5.0,
  "win_nights": 10
}
```

**Value:** `30.0` seconds

**This is the SOURCE OF TRUTH** - all other references load from this file.

---

## 🔄 **HOW IT'S LOADED AND USED**

### **File: `core/wave_manager.py`**
**Line: 35** - Loaded during initialization

```python
def __init__(self, world, waves_cfg: Dict, difficulty: str = "normal"):
    # ...
    self.day_duration = waves_cfg.get("day_duration", 30.0)  # ← LOADED HERE
    self.summary_duration = waves_cfg.get("summary_duration", 5.0)
```

**Default fallback:** `30.0` seconds (if config missing)

---

### **File: `core/wave_manager.py`**
**Line: 151-159** - **THE TRANSITION LOGIC**

```python
def update(self, dt: float, spawner, world) -> str:
    old_state = self.state
    self.timer += dt  # ← Timer increments every frame
    
    if self.state == self.STATE_DAY:
        # Day phase: wait for day duration, then start night
        if self.timer >= self.day_duration:  # ← TRANSITION CHECK
            # Increment night counter when transitioning from day to night
            self.night += 1
            self.start_night()  # ← TRANSITION TO NIGHT
```

**How it works:**
1. `self.timer` starts at `0.0` when day begins (line 62 in `start_day()`)
2. `self.timer += dt` increments every frame (line 149)
3. When `self.timer >= self.day_duration` (30.0 seconds), transition to night occurs
4. Uses a **timer-based system** (NOT hard-coded counter, NOT event-based)

---

## 📋 **ALL LOCATIONS WHERE `day_duration` APPEARS**

### 1. **Config File (Source of Truth)**
- **File:** `data/config/waves.json`
- **Line:** 42
- **Value:** `30.0`
- **Purpose:** Primary configuration

### 2. **Wave Manager Initialization**
- **File:** `core/wave_manager.py`
- **Line:** 35
- **Code:** `self.day_duration = waves_cfg.get("day_duration", 30.0)`
- **Purpose:** Loads value from config into instance variable

### 3. **Day → Night Transition Check**
- **File:** `core/wave_manager.py`
- **Line:** 153
- **Code:** `if self.timer >= self.day_duration:`
- **Purpose:** **THE ACTUAL TRANSITION TRIGGER**

### 4. **Default Fallback in main.py**
- **File:** `main.py`
- **Line:** 1497
- **Code:** `"day_duration": 30.0,`
- **Purpose:** Fallback config if `waves.json` doesn't exist

### 5. **Balance System (if used)**
- **File:** `core/balance.py`
- **Line:** 246-248
- **Code:** 
  ```python
  def get_day_duration(self) -> float:
      return self._get_base_value("waves.day_duration", 30.0)
  ```
- **Purpose:** Balance system accessor (may not be actively used)

### 6. **Documentation/Config Files**
- **File:** `data/config/balance.json` (line 184)
- **File:** `data/config/BALANCE_README.md` (line 93)
- **File:** `BALANCE_CONFIG_GUIDE.md` (lines 126, 149, 486, 491)
- **Purpose:** Documentation and alternative config references

---

## ⚙️ **TRANSITION MECHANISM**

### **Type: Timer-Based (NOT Hard-Coded Counter)**

**How it works:**
1. **Day starts:** `start_day()` is called → `self.timer = 0.0` (line 62)
2. **Every frame:** `wave_manager.update(dt, ...)` is called → `self.timer += dt` (line 149)
3. **Transition check:** `if self.timer >= self.day_duration:` (line 153)
4. **When condition met:** `self.start_night()` is called (line 159)

**Key Variables:**
- `self.timer` - Accumulates delta time (dt) each frame
- `self.day_duration` - Threshold value (30.0 seconds from config)
- `dt` - Delta time (frame time, typically ~0.016s at 60 FPS)

**Formula:**
```
Day Duration = 30.0 seconds
Timer increments by dt each frame
Transition occurs when: timer >= 30.0
```

---

## 🔍 **EXACT VARIABLE/FUNCTION THAT CONTROLS DAYTIME**

### **Primary Control:**
- **Variable:** `wave_manager.day_duration` (instance variable)
- **Loaded from:** `waves_config["day_duration"]` (from `waves.json`)
- **Default:** `30.0` seconds

### **Transition Logic:**
- **Function:** `wave_manager.update(dt, spawner, world)` (line 142)
- **Check:** `if self.timer >= self.day_duration:` (line 153)
- **Action:** `self.start_night()` (line 159)

### **Timer Management:**
- **Reset:** `self.timer = 0.0` in `start_day()` (line 62)
- **Increment:** `self.timer += dt` in `update()` (line 149)

---

## 📊 **SUMMARY**

| Aspect | Details |
|--------|---------|
| **Source File** | `data/config/waves.json` (line 42) |
| **Value** | `30.0` seconds |
| **Loaded In** | `core/wave_manager.py` line 35 |
| **Used In** | `core/wave_manager.py` line 153 |
| **Transition Type** | **Timer-based** (NOT hard-coded, NOT counter-based) |
| **Mechanism** | `timer += dt` each frame, check `timer >= day_duration` |
| **Reset Point** | When `start_day()` is called (timer = 0.0) |

---

## 🎯 **TO CHANGE DAYTIME DURATION**

**Option 1: Edit Config File (Recommended)**
- **File:** `data/config/waves.json`
- **Line:** 42
- **Change:** `"day_duration": 30.0` → `"day_duration": 45.0` (or desired value)

**Option 2: Edit Fallback in main.py**
- **File:** `main.py`
- **Line:** 1497
- **Change:** `"day_duration": 30.0` → `"day_duration": 45.0`

**Note:** The value is loaded once during `WaveManager.__init__()`, so changes require restarting the game.

---

## ✅ **VERIFICATION**

The daytime duration is **NOT scattered** - it's centralized:
1. **Defined once** in `waves.json` (source of truth)
2. **Loaded once** in `wave_manager.__init__()` (line 35)
3. **Used once** in `wave_manager.update()` (line 153)

All other references are either:
- Fallback defaults (main.py)
- Documentation (markdown files)
- Balance system accessors (may not be actively used)

**The system is clean and centralized!** 🎉

