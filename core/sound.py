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
        
        # Load additional sounds (coin, gamestart, hover sounds)
        additional_sounds = ["coin", "gamestart", "sci_fi_hover", "sci_fi_hover_high"]
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

