# Audio System Implementation Guide

## Overview
This document explains the complete audio system implementation for Zombie Rush, including start screen music, daytime BGM, and nighttime BGM.

## File Structure

```
Zombie-survival/
├── core/
│   └── sound.py          # Centralized audio manager (SoundSystem class)
├── main.py               # Game loop with music state transitions
└── asset/
    └── audio/
        ├── gamestart.mp3      # Start screen music (0.40s, loops)
        ├── daytime.mp3        # Day phase background music
        └── in-the-night.mp3   # Night phase background music
```

## Implementation Details

### 1. Sound System (`core/sound.py`)

**Key Methods Added:**

- `play_start_music()` - Plays `gamestart.mp3` on start screen (loops continuously)
- `play_daytime_music()` - Plays `daytime.mp3` during day phase (prevents stacking)
- `play_nighttime_music()` - Stops daytime, plays `in-the-night.mp3` during night phase
- `play_music()` - Enhanced with `force_restart` parameter to prevent duplicate playback
- `stop_music()` - Stops all background music

**Key Features:**
- Prevents overlapping music by checking if same track is already playing
- Uses `pygame.mixer.music` for background music (separate from SFX)
- Tracks current music state to avoid unnecessary reloads

### 2. Game Flow Integration (`main.py`)

#### Start Screen Music Logic
**Location:** `main.py` line ~3606-3625

```python
if game_state_manager.get_state() == GameState.MENU:
    # Play gamestart.mp3 on start screen (loops until game starts)
    sound_system.play_start_music()
```

**Behavior:**
- Starts playing immediately when on start screen
- Loops continuously until player clicks to start
- Can be cut early (before 0.40s) if player clicks quickly

#### Stop Start Music When Game Begins
**Location:** `main.py` line ~2591-2599

```python
def open_difficulty_selection():
    # Stop gamestart.mp3 immediately when player clicks to start
    sound_system.stop_music()
    # ... rest of function
```

**Location:** `main.py` line ~2621-2630

```python
def handle_mode_selected(mode: GameMode):
    # Force-stop gamestart.mp3 when game page loads
    sound_system.stop_music()
    # ... rest of function
```

#### Daytime Music Logic
**Location:** `main.py` line ~4008-4010 (first time initialization)

```python
if not hasattr(wave_manager, '_prev_state'):
    # Start daytime music when game first loads (if in day phase)
    if wave_manager.state == WaveManager.STATE_DAY:
        sound_system.play_daytime_music()
```

**Location:** `main.py` line ~4095-4100 (day phase transition)

```python
if wave_manager.state == WaveManager.STATE_DAY:
    # ... day phase setup ...
    # Start Day Phase BGM: Play daytime.mp3 (loop = True)
    # If already playing, won't stack or replay
    sound_system.play_daytime_music()
```

**Behavior:**
- Starts when game page loads (if in day phase)
- Starts when transitioning from night/summary to day
- Won't replay if already playing (prevents stacking)

#### Nighttime Music Logic
**Location:** `main.py` line ~4134-4139 (night phase transition)

```python
elif wave_manager.state == WaveManager.STATE_NIGHT:
    # ... night phase setup ...
    # Nighttime music logic: Stop daytime.mp3 immediately, then start in-the-night.mp3
    # No fade required - strict stop before night begins
    sound_system.play_nighttime_music()
```

**Behavior:**
- Stops `daytime.mp3` immediately when night begins
- Starts `in-the-night.mp3` immediately after (loops)
- No fade transition (strict stop/start)

#### Return to Day Cycle
**Location:** `main.py` line ~4095-4100 (day phase transition)

When transitioning from night back to day:
- `play_nighttime_music()` stops automatically (via `play_daytime_music()`)
- `play_daytime_music()` starts `daytime.mp3` again
- This happens in the same day phase transition code

#### Music Stop on Game Over/Win
**Location:** `main.py` line ~3994, ~3933, ~4072

```python
# Stop music when game ends
sound_system.stop_music()
```

## State Flow Diagram

```
START SCREEN (MENU)
    ↓ play_start_music() → gamestart.mp3 (loops)
    ↓
PLAYER CLICKS START
    ↓ stop_music() → cuts gamestart.mp3
    ↓
DIFFICULTY/MODE SELECTION
    ↓ (no music)
    ↓
GAME STARTS (PLAYING)
    ↓ play_daytime_music() → daytime.mp3 (loops)
    ↓
DAY PHASE
    ↓ daytime.mp3 continues
    ↓
NIGHT PHASE TRANSITION
    ↓ play_nighttime_music() → stops daytime, starts in-the-night.mp3
    ↓
NIGHT PHASE
    ↓ in-the-night.mp3 continues
    ↓
DAY PHASE TRANSITION (next day)
    ↓ play_daytime_music() → stops in-the-night, starts daytime.mp3
    ↓
(cycle repeats)
```

## Code Placement Summary

### `core/sound.py`
- **Lines 25**: Added `start_music_playing` flag
- **Lines 119-160**: Enhanced `play_music()` with duplicate prevention
- **Lines 171-201**: Added `play_start_music()` method
- **Lines 203-215**: Added `play_daytime_music()` method
- **Lines 217-230**: Added `play_nighttime_music()` method

### `main.py`
- **Line ~3607**: Start screen music initialization
- **Line ~2594**: Stop start music when clicking to start
- **Line ~2627**: Force-stop start music when game loads
- **Line ~4009**: First-time daytime music initialization
- **Line ~4100**: Day phase music start
- **Line ~4139**: Night phase music transition
- **Lines ~3933, 3994, 4072**: Music stop on game over/win

## Testing Checklist

- [ ] Start screen plays `gamestart.mp3` and loops
- [ ] Clicking start before 0.40s cuts the music immediately
- [ ] Clicking start after 0.40s stops music normally
- [ ] Game page loads with `daytime.mp3` playing (if in day phase)
- [ ] Day phase transition plays `daytime.mp3` (doesn't stack if already playing)
- [ ] Night phase transition stops `daytime.mp3` and starts `in-the-night.mp3`
- [ ] Next day transition stops `in-the-night.mp3` and starts `daytime.mp3`
- [ ] Game over/win stops all music
- [ ] Returning to menu stops all music

## Notes

- All music uses `pygame.mixer.music` (separate from SFX which use `pygame.mixer.Sound`)
- Music volume is set to 0.4 (40%) to stay below sound effects
- No fade transitions implemented (strict stop/start for clean transitions)
- System prevents overlapping music by checking current track before playing

