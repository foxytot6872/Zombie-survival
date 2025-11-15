"""
Wave management system for coordinating night waves.
"""
import json
from typing import Dict, Optional, Tuple

class WaveManager:
    """Manages wave-based spawning and day/night cycles"""
    
    STATE_DAY = "DAY"
    STATE_NIGHT = "NIGHT"
    STATE_SUMMARY = "SUMMARY"
    
    def __init__(self, world, waves_cfg: Dict, difficulty: str = "normal"):
        """
        Initialize wave manager.
        Args:
            world: World object containing game state
            waves_cfg: Wave configuration dictionary
            difficulty: Difficulty level ("easy", "normal", "hard")
        """
        self.world = world
        self.cfg = waves_cfg
        self.difficulty = difficulty
        self.night = 1
        self.day = 1
        self.state = self.STATE_DAY
        self.timer = 0.0
        self.day_duration = waves_cfg.get("day_duration", 30.0)
        self.summary_duration = waves_cfg.get("summary_duration", 5.0)
        self.win_nights = waves_cfg.get("win_nights", 10)
        
        # Statistics
        self.enemies_killed = 0
        self.enemies_spawned = 0
        
    def start_day(self):
        """Start a new day"""
        self.state = self.STATE_DAY
        self.timer = 0.0
        self.day += 1
        # Trigger node spawn event (handled by main.py)
        if hasattr(self, 'on_day_start'):
            self.on_day_start()
        
    def start_night(self):
        """Start a night wave"""
        self.state = self.STATE_NIGHT
        self.timer = 0.0
        self.enemies_spawned = 0
        
    def start_summary(self):
        """Start the summary phase after a wave"""
        self.state = self.STATE_SUMMARY
        self.timer = 0.0
        
    def get_wave_recipe(self) -> Dict[str, int]:
        """Get the enemy recipe for the current night"""
        # Get base recipe for this night (loop if we exceed defined nights)
        night_index = min(self.night - 1, len(self.cfg["nights"]) - 1)
        base_mix = self.cfg["nights"][night_index]["mix"].copy()
        
        # Calculate difficulty multiplier
        difficulty_mult = self.cfg["difficulty"].get(self.difficulty, 1.0)
        
        # Calculate night scaling multiplier
        night_mult = self.cfg["increment"]["per_night_mult"] ** (self.night - 1)
        
        # Apply multipliers
        total_mult = difficulty_mult * night_mult
        
        # Scale enemy counts
        recipe = {}
        for enemy_type, count in base_mix.items():
            recipe[enemy_type] = int(count * total_mult)
        
        return recipe
    
    def update(self, dt: float, spawner, world) -> str:
        """
        Update wave manager.
        Returns:
            Current state or "WIN" if won
        """
        old_state = self.state
        self.timer += dt
        
        if self.state == self.STATE_DAY:
            # Day phase: wait for day duration, then start night
            if self.timer >= self.day_duration:
                self.start_night()
                
        elif self.state == self.STATE_NIGHT:
            # Night phase: spawn enemies until wave is complete
            # Spawner handles actual spawning
            # Update enemies spawned count
            if spawner:
                self.enemies_spawned = spawner.spawn_count
            
            # Check if wave is complete (spawner done and no enemies)
            if spawner and spawner.done:
                # Check if all enemies are dead
                if world and hasattr(world, 'enemy_group'):
                    if len(world.enemy_group) == 0:
                        self.start_summary()
                        
        elif self.state == self.STATE_SUMMARY:
            # Summary phase: wait for summary duration, then start next day
            if self.timer >= self.summary_duration:
                # Check win condition
                if self.night > self.win_nights:
                    return "WIN"
                self.start_day()
        
        return self.state
    
    def get_current_wave_info(self) -> Dict:
        """Get information about the current wave"""
        recipe = self.get_wave_recipe()
        return {
            "night": self.night,
            "day": self.day,
            "state": self.state,
            "recipe": recipe,
            "enemies_killed": self.enemies_killed,
            "enemies_spawned": self.enemies_spawned
        }
    
    def is_won(self) -> bool:
        """Check if game is won"""
        return self.night > self.win_nights
    
    def reset(self):
        """Reset wave manager"""
        self.night = 1
        self.day = 1
        self.state = self.STATE_DAY
        self.timer = 0.0
        self.enemies_killed = 0
        self.enemies_spawned = 0

