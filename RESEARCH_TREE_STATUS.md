# Research Tree Status Report

## Overview
The game currently has **two research systems** implemented:

1. **Simple Research System** (`research.json` + `ResearchManager`)
2. **Visual Research Tree UI** (`research_tree.py`)

---

## 1. Simple Research System

### Current Implementation
- **File**: `data/config/research.json`
- **Manager**: `world/research.py` (ResearchManager class)
- **UI Panel**: `ui/research_panel.py`

### Available Research Items (4 total)
| Research Key | Name | Cost | Unlocks |
|-------------|------|------|---------|
| `sawmill_unlock` | Unlock Sawmill | 25 coins | `sawmill` |
| `smelter_unlock` | Unlock Smelter | 40 coins | `smelter` |
| `turret_t2` | Tier 2 Turret | 60 coins | `turret_lv2` |
| `railgun_turret` | Railgun Turret | 100 coins | `railgun_turret` |

### Features
✅ **Working:**
- Research definitions loaded from JSON
- Coin cost system
- Unlock tracking (`unlocked` set)
- Purchase tracking (`purchased` set)
- Building unlock integration (Sawmill, Smelter, Railgun Turret)
- UI panel with unlock buttons
- Button color coding (green = affordable, gray = can't afford)
- "UNLOCKED" status display

❌ **Missing:**
- Tier system (no tier grouping)
- Modifier system (no stat bonuses)
- Research tier sorting
- `apply_research_modifiers()` function
- `is_research_unlocked(key)` helper (alias exists but not used)
- `get_research_by_tier()` function
- Multiplicative modifier stacking with day events

### Integration Status
- ✅ Research button in top-left (R key or click)
- ✅ Building buttons rebuild based on unlocks
- ✅ Research panel displays all items
- ❌ No modifier application to gameplay
- ❌ No tier progression system

---

## 2. Visual Research Tree UI

### Current Implementation
- **File**: `research_tree.py`
- **UI System**: Full-screen research tree with visual nodes
- **Categories**: 4 sections (Resource, Turret, NPC, Base)

### Available Research Nodes (20 total)

#### Resource Tree (6 nodes)
1. **Sawmill** - 100 coins - Unlock sawmill building
2. **Advanced Woodcutting** - 200 coins - +15% wood income (requires Sawmill)
3. **Auto Lumber Bot** - 350 coins - Automated wood harvesting (requires Advanced Woodcutting)
4. **Smelter** - 120 coins - Unlock smelter building
5. **Alloy Research** - 220 coins - Improved iron yield (requires Smelter)
6. **High-Tech Forge** - 380 coins - Unlock high tier materials (requires Alloy)

#### Turret Tree (4 nodes)
1. **Tier 1 Turret** - 150 coins - Basic projectile turret
2. **Tier 2 Turret** - 250 coins - Enhanced damage (requires Tier 1)
3. **Railgun Turret** - 400 coins - Long-range piercing shot (requires Tier 2)
4. **Flamethrower Tower** - 500 coins - Area denial flames (requires Railgun)

#### NPC Tree (4 nodes)
1. **Worker NPC +1** - 120 coins - Add another worker slot
2. **NPC Efficiency +10%** - 220 coins - Workers gather faster (requires Worker NPC +1)
3. **Gathering Speed +20%** - 320 coins - Further gather boost (requires NPC Efficiency)
4. **Combat NPC** - 420 coins - Unlock guard NPC patrol (requires Gathering Speed)

#### HQ/Base Tree (6 nodes)
1. **HQ Reinforcement** - 180 coins - +20% HQ HP
2. **Perimeter Walls** - 260 coins - Unlock perimeter upgrades (requires HQ Reinforcement)
3. **Auto-Repair System** - 320 coins - Slow passive repairs (requires Perimeter)
4. **Radar System** - 320 coins - Reveal incoming hordes (requires Perimeter)

### Features
✅ **Working:**
- Visual node-based UI
- Parent-child relationships (prerequisites)
- Node states: locked, unlockable, unlocked
- Color-coded nodes (gray = locked, green = unlockable, yellow = unlocked)
- Connection lines between nodes
- Tooltip system on hover
- Coin cost display
- Persistent unlock states (GLOBAL_NODE_STATES)
- Section-based organization

❌ **Missing:**
- Actual gameplay integration (effects are placeholders)
- Modifier application to game stats
- Building unlock integration (only adds to `unlocked` set)
- Tier system in UI
- Research effects implementation

### Integration Status
- ✅ Opens via R key or research button
- ✅ Pauses game when open
- ✅ Visual feedback and tooltips
- ❌ Research effects not applied to gameplay
- ❌ No connection to building unlocks
- ❌ No modifier system integration

---

## 3. Comparison & Issues

### System Discrepancy
The two systems are **not synchronized**:
- `research.json` has 4 items
- `research_tree.py` has 20 items
- They use different unlock keys
- Effects are not shared

### Missing Features (from original requirements)
Based on the conversation history, the following were requested but not fully implemented:

1. **Tier System** (Tier 1-4 + Optional Branches)
   - ❌ Not implemented in `research.json`
   - ❌ Not displayed in `research_panel.py`
   - ✅ Partially in `research_tree.py` (visual only)

2. **Modifier System**
   - ❌ No `modifiers` field in `research.json`
   - ❌ No `apply_research_modifiers()` function
   - ❌ No multiplicative stacking with day events
   - ❌ No modifier application to:
     - Gather speed
     - Haul speed
     - Building HP
     - Building damage taken
     - Turret fire rate
     - Turret range
     - Enemy skeleton damage

3. **Research Items Missing**
   - ❌ Worker Efficiency I/II
   - ❌ Logistics I/II
   - ❌ Basic/Advanced Armor
   - ❌ Gatling Turret unlock
   - ❌ Ballistic Turret Tier 2/3
   - ❌ Turret Engineering I/II
   - ❌ Defensive Masterwork
   - ❌ Anti-Magic
   - ❌ Coin Fortune
   - ❌ Reinforced Gates
   - ❌ Housing Expansion I

---

## 4. Recommendations

### Priority 1: Unify Systems
- Choose one system (recommend enhancing `research.json` + `ResearchManager`)
- Migrate all research items to JSON format
- Implement tier system in JSON
- Add modifier support

### Priority 2: Implement Modifiers
- Add `modifiers` field to research items
- Implement `apply_research_modifiers()` in ResearchManager
- Integrate with day event modifiers (multiplicative stacking)
- Apply modifiers to:
  - Survivor gather/haul speed
  - Building HP/damage taken
  - Turret fire rate/range
  - Enemy damage (skeleton types)

### Priority 3: Add Missing Research Items
- Add all Tier 1-4 research items
- Add optional branch items
- Ensure proper unlock chains

### Priority 4: UI Improvements
- Add tier labels to research panel
- Group items by tier
- Show modifier effects in tooltips
- Visual indicator for purchased items

---

## 5. Current State Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Basic Research System | ✅ Working | 4 items, basic unlocks |
| Visual Research Tree | ✅ Working | 20 items, visual only |
| Tier System | ❌ Missing | Not in JSON or UI |
| Modifier System | ❌ Missing | No stat bonuses |
| Building Unlocks | ✅ Partial | Sawmill, Smelter, Railgun work |
| Turret Upgrades | ❌ Missing | No tier unlock checks |
| UI Integration | ✅ Working | Both systems accessible |
| Gameplay Effects | ❌ Missing | No modifiers applied |

---

## 6. Files to Update

### High Priority
1. `data/config/research.json` - Add all research items with tiers and modifiers
2. `world/research.py` - Add modifier system and tier support
3. `ui/research_panel.py` - Add tier grouping and modifier display

### Medium Priority
4. `main.py` - Integrate modifier application in game loop
5. `world/building.py` - Apply building HP modifiers
6. `world/buildings/turret.py` - Apply fire rate/range modifiers
7. `world/survivor.py` - Apply gather/haul speed modifiers

### Low Priority
8. `research_tree.py` - Sync with JSON system or deprecate
9. `ui/research_button.py` - Ensure proper integration

---

**Last Updated**: Current session
**Status**: Research system is functional but incomplete. Core features work, but advanced features (tiers, modifiers) are missing.

