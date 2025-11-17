"""
Sound system for game audio hooks.
"""
import pygame
import os
from pathlib import Path
from typing import Dict, Optional

class SoundSystem:
    """Manages game audio"""
    
    def __init__(self, audio_dir: str = "asset/audio", enabled: bool = True):
        """
        Initialize sound system.
        Args:
            audio_dir: Directory containing audio files
            enabled: Whether sound is enabled
        """
        self.audio_dir = Path(audio_dir)
        self.enabled = enabled
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.volume = 0.5
        self.music_volume = 0.4  # Background music volume (lower than sound effects)
        self.current_music = None  # Track currently playing music
        self.start_music_playing = False  # Track if start screen music is playing
        
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            except:
                print("Warning: Could not initialize audio mixer")
                self.enabled = False
        
        # Load sounds if directory exists
        if self.audio_dir.exists() and self.enabled:
            self._load_sounds()
    
    def _load_sounds(self):
        """Load all sound files from audio directory"""
        if not self.audio_dir.exists():
            return
        
        # Common sound events
        sound_events = [
            "build_placed",
            "turret_fire",
            "enemy_death",
            "building_destroyed",
            "game_over",
            "wave_start",
            "wave_clear",
            "upgrade",
            "repair",
            "button_click"
        ]
        
        for event_name in sound_events:
            # Try .wav first, then .mp3
            sound_file = self.audio_dir / f"{event_name}.wav"
            if not sound_file.exists():
                sound_file = self.audio_dir / f"{event_name}.mp3"
            
            if sound_file.exists():
                try:
                    self.sounds[event_name] = pygame.mixer.Sound(str(sound_file))
                    self.sounds[event_name].set_volume(self.volume)
                except Exception as e:
                    print(f"Warning: Could not load sound {event_name}: {e}")
        
        # Load additional sounds (coin, hover sounds)
        # NOTE: gamestart.mp3 is NOT loaded as Sound - it's BGM using pygame.mixer.music
        additional_sounds = ["coin", "sci_fi_hover", "sci_fi_hover_high"]
        for event_name in additional_sounds:
            # Try .mp3 first, then .wav
            sound_file = self.audio_dir / f"{event_name}.mp3"
            if not sound_file.exists():
                sound_file = self.audio_dir / f"{event_name}.wav"
            
            if sound_file.exists():
                try:
                    self.sounds[event_name] = pygame.mixer.Sound(str(sound_file))
                    self.sounds[event_name].set_volume(self.volume)
                except Exception as e:
                    print(f"Warning: Could not load sound {event_name}: {e}")
    
    def play(self, event_name: str, volume: Optional[float] = None):
        """
        Play a sound effect.
        Args:
            event_name: Name of the sound event
            volume: Volume (0.0 to 1.0), uses default if None
        """
        if not self.enabled:
            return
        
        if event_name in self.sounds:
            try:
                sound = self.sounds[event_name]
                if volume is not None:
                    sound.set_volume(volume)
                sound.play()
            except Exception as e:
                print(f"Warning: Could not play sound {event_name}: {e}")
    
    def set_volume(self, volume: float):
        """Set master volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable sound"""
        self.enabled = enabled
    
    def is_enabled(self) -> bool:
        """Check if sound is enabled"""
        return self.enabled
    
    def play_music(self, music_file: str, loop: bool = True, volume: Optional[float] = None, force_restart: bool = False):
        """
        Play background music using pygame.mixer.music (NOT Sound).
        This ensures instant stopping and clean transitions.
        
        Args:
            music_file: Name of music file (e.g., "daytime.mp3")
            loop: Whether to loop the music (default True)
            volume: Volume (0.0 to 1.0), uses music_volume if None
            force_restart: If True, restart even if same music is already playing
        """
        if not self.enabled:
            return
        
        # If same music is already playing and not forcing restart, don't replay
        if not force_restart and self.current_music == music_file and pygame.mixer.music.get_busy():
            return
        
        music_path = self.audio_dir / music_file
        if not music_path.exists():
            print(f"Warning: Music file not found: {music_path}")
            return
        
        try:
            # CRITICAL: Stop any currently playing music FIRST
            # This ensures no overlap and clean transitions
            pygame.mixer.music.stop()
            
            # Load the new music file
            pygame.mixer.music.load(str(music_path))
            
            # Set volume
            music_vol = volume if volume is not None else self.music_volume
            pygame.mixer.music.set_volume(music_vol)
            
            # Play with or without looping
            if loop:
                pygame.mixer.music.play(-1)  # -1 = infinite loop
            else:
                pygame.mixer.music.play(1)  # Play once
            
            # Update state
            self.current_music = music_file
            self.start_music_playing = False  # Reset start music flag when playing other music
        except Exception as e:
            print(f"Warning: Could not play music {music_file}: {e}")
            self.current_music = None
            self.start_music_playing = False
    
    def stop_music(self):
        """
        Force stop currently playing background music IMMEDIATELY.
        This ensures gamestart.mp3 stops instantly when player clicks start.
        """
        try:
            # Force stop - no waiting, immediate cut
            pygame.mixer.music.stop()
            # Clear state immediately
            self.current_music = None
            self.start_music_playing = False
        except Exception as e:
            print(f"Warning: Could not stop music: {e}")
            # Even if error, try to clear state
            self.current_music = None
            self.start_music_playing = False
    
    def play_start_music(self):
        """
        Play gamestart.mp3 on start screen using pygame.mixer.music.
        This music loops continuously until the game starts.
        Can be cut early (before 0.40s) when player clicks start.
        
        Uses pygame.mixer.music (NOT Sound) to allow instant stopping.
        """
        if not self.enabled:
            return
        
        # Only start if not already playing
        if self.start_music_playing and self.current_music == "gamestart.mp3" and pygame.mixer.music.get_busy():
            return
        
        music_path = self.audio_dir / "gamestart.mp3"
        if not music_path.exists():
            print(f"Warning: Start music file not found: {music_path}")
            return
        
        try:
            # CRITICAL: Stop any currently playing music FIRST
            # This ensures clean transition and prevents overlap
            pygame.mixer.music.stop()
            
            # Load gamestart.mp3 using pygame.mixer.music (NOT Sound)
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.music_volume)
            
            # Play with infinite loop (-1 = loop forever)
            pygame.mixer.music.play(-1)
            
            # Update state
            self.current_music = "gamestart.mp3"
            self.start_music_playing = True
        except Exception as e:
            print(f"Warning: Could not play start music: {e}")
            self.current_music = None
            self.start_music_playing = False
    
    def play_daytime_music(self):
        """
        Play daytime.mp3 during day phase.
        Only plays if not already playing to prevent stacking.
        """
        if not self.enabled:
            return
        
        # Don't replay if already playing
        if self.current_music == "daytime.mp3" and pygame.mixer.music.get_busy():
            return
        
        self.play_music("daytime.mp3", loop=True, force_restart=False)
    
    def play_nighttime_music(self):
        """
        Play in-the-night.mp3 during night phase.
        Stops daytime music IMMEDIATELY first, then starts nighttime music.
        No fade - strict stop/start for clean transition.
        """
        if not self.enabled:
            return
        
        # CRITICAL: Stop daytime music IMMEDIATELY (strict stop before night begins)
        # This ensures no overlap between daytime and nighttime music
        pygame.mixer.music.stop()
        
        # Play nighttime music (play_music will handle loading and playing)
        self.play_music("in-the-night.mp3", loop=True, force_restart=False)
    
    def play_night_music(self):
        """Alias for play_nighttime_music() for consistency."""
        self.play_nighttime_music()
    
    def pause_music(self):
        """Pause currently playing background music"""
        try:
            pygame.mixer.music.pause()
        except Exception as e:
            print(f"Warning: Could not pause music: {e}")
    
    def unpause_music(self):
        """Unpause paused background music"""
        try:
            pygame.mixer.music.unpause()
        except Exception as e:
            print(f"Warning: Could not unpause music: {e}")
    
    def set_music_volume(self, volume: float):
        """Set background music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except Exception as e:
            print(f"Warning: Could not set music volume: {e}")

