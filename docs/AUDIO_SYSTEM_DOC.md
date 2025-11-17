# 5.3 Audio System

## Overview

The game features a layered audio system with dynamic background music (BGM) that transitions based on game state, ambient sound effects (SFX) for gameplay feedback, and seamless music switching between day and night phases.

## Architecture

### Components

1. **Background Music (BGM)**
   - Uses `pygame.mixer.music` for streaming music tracks
   - Supports looping and instant stop/start transitions
   - State-based music selection (menu, day phase, night phase)

2. **Sound Effects (SFX)**
   - Uses `pygame.mixer.Sound` for short audio clips
   - Includes button clicks, coin collection, building actions, combat sounds
   - Non-blocking playback for responsive feedback

3. **Audio Manager**
   - Centralized `SoundSystem` class (`core/sound.py`)
   - Manages music transitions, volume control, and playback state
   - Prevents music overlap and ensures clean state transitions

## Music Tracks

### Background Music

| Track | File | Usage | Loop |
|-------|------|-------|------|
| Start Screen | `gamestart.mp3` | Main menu / difficulty selection | Yes |
| Day Phase | `daytime.mp3` | Daytime gameplay | Yes |
| Night Phase | `in-the-night.mp3` | Nighttime combat | Yes |

### Music Transition Rules

1. **Start Screen → Game**
   - `gamestart.mp3` plays on menu load (loops continuously)
   - **Instant stop** when player clicks "Start" or enters game
   - No fade-out required (immediate cut)

2. **Day Phase Music**
   - Starts when game page loads (if in day phase)
   - Plays `daytime.mp3` (loop = True)
   - Does not restart if already playing (prevents stacking)

3. **Day → Night Transition**
   - Immediately stops `daytime.mp3`
   - Immediately starts `in-the-night.mp3` (loop = True)
   - No fade required (strict stop/start for clean transition)

4. **Night → Day Transition**
   - Stops `in-the-night.mp3`
   - Plays `daytime.mp3` again
   - Clean cycle repeats

5. **Game Over / Win**
   - Stops all background music immediately
   - Plays game over sound effect

## Sound Effects

### Available SFX

- **UI Interactions**: Button clicks, menu navigation
- **Economy**: Coin collection, resource gathering
- **Construction**: Building placement, upgrade sounds
- **Combat**: Turret firing, enemy hits, wave clear
- **Game State**: Game over, victory sounds

### SFX Implementation

- Loaded on initialization from `asset/audio/` directory
- Played via `sound_system.play(sfx_name)`
- Non-blocking (does not pause game loop)
- Volume controlled separately from music

## Technical Implementation

### Key Functions

```python
# Music Control
sound_system.play_start_music()      # Menu music
sound_system.play_daytime_music()    # Day phase BGM
sound_system.play_nighttime_music()  # Night phase BGM
sound_system.stop_music()            # Force stop all music

# Sound Effects
sound_system.play("button_click")    # Play SFX by name
sound_system.set_music_volume(0.7)   # Adjust music volume
sound_system.set_sfx_volume(0.8)     # Adjust SFX volume
```

### State Management

- **Current Music Tracking**: `SoundSystem.current_music` stores active track
- **Overlap Prevention**: Always stops previous music before starting new track
- **Instant Stop**: `pygame.mixer.music.stop()` called immediately (no buffering delay)

### Integration Points

- **Game State Manager**: Music changes based on `GameState` (MENU, PLAYING)
- **Wave Manager**: Music switches on `STATE_DAY` / `STATE_NIGHT` transitions
- **UI Events**: Button clicks trigger SFX via `sound_system.play()`

## Volume Control

- **Music Volume**: Separate control for background music (default: 0.7)
- **SFX Volume**: Separate control for sound effects (default: 0.8)
- **Master Mute**: Can disable entire audio system if needed
- **Per-Track Control**: Individual volume setting when loading tracks

## Design Philosophy

1. **Non-Intrusive**: Music enhances atmosphere without overwhelming gameplay
2. **State-Aware**: Audio reflects current game phase (calm day vs. intense night)
3. **Responsive**: SFX provide immediate feedback for player actions
4. **Clean Transitions**: No audio glitches or overlapping tracks
5. **Performance**: Efficient loading and caching of audio assets

## Future Enhancements

- Dynamic music intensity based on enemy count
- Adaptive volume based on combat intensity
- Additional ambient tracks for different game states
- Spatial audio for 3D sound positioning (if applicable)

