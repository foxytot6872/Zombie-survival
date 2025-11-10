"""
Game state management (day/night cycle, difficulty, etc.)
"""
import time
from config import DAY_DURATION, NIGHT_DURATION, DIFFICULTY_SETTINGS

class GameState:
    def __init__(self, difficulty="Normal"):
        self.difficulty = difficulty
        self.day = 1
        self.is_day = True
        self.day_start_time = time.time()
        self.night_start_time = None
        
        # Get difficulty multipliers
        self.enemy_multiplier = DIFFICULTY_SETTINGS[difficulty]["enemy"]
        self.cost_multiplier = DIFFICULTY_SETTINGS[difficulty]["cost"]
        
        # Game state flags
        self.game_over = False
        self.paused = False
    
    def update(self):
        """Update day/night cycle"""
        current_time = time.time()
        
        if self.is_day:
            elapsed = current_time - self.day_start_time
            if elapsed >= DAY_DURATION:
                # Transition to night
                self.is_day = False
                self.night_start_time = current_time
        else:
            elapsed = current_time - self.night_start_time
            if elapsed >= NIGHT_DURATION:
                # Transition to day
                self.is_day = True
                self.day += 1
                self.day_start_time = current_time
    
    def get_time_remaining(self):
        """Get remaining time in current phase (in seconds)"""
        current_time = time.time()
        if self.is_day:
            elapsed = current_time - self.day_start_time
            return max(0, DAY_DURATION - elapsed)
        else:
            elapsed = current_time - self.night_start_time
            return max(0, NIGHT_DURATION - elapsed)
    
    def get_phase_progress(self):
        """Get progress through current phase (0.0 to 1.0)"""
        current_time = time.time()
        if self.is_day:
            elapsed = current_time - self.day_start_time
            return min(1.0, elapsed / DAY_DURATION)
        else:
            elapsed = current_time - self.night_start_time
            return min(1.0, elapsed / NIGHT_DURATION)
    
    def get_cost_multiplier(self):
        """Get cost multiplier for current difficulty"""
        return self.cost_multiplier
    
    def get_enemy_multiplier(self):
        """Get enemy multiplier for current difficulty"""
        return self.enemy_multiplier

