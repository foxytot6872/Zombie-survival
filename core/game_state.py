"""
Game state management system.
"""
from enum import Enum
from typing import Optional

class GameState(Enum):
    """Game state enumeration"""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    DAY = "day"
    NIGHT = "night"
    SUMMARY = "summary"
    GAME_OVER = "game_over"
    WIN = "win"
    QUIT = "quit"

class GameStateManager:
    """Manages game state transitions"""
    
    def __init__(self):
        self.state = GameState.PLAYING
        self.previous_state: Optional[GameState] = None
        
    def set_state(self, new_state: GameState):
        """Set game state"""
        if new_state != self.state:
            self.previous_state = self.state
            self.state = new_state
            
    def get_state(self) -> GameState:
        """Get current game state"""
        return self.state
    
    def is_playing(self) -> bool:
        """Check if game is in playing state"""
        return self.state == GameState.PLAYING
    
    def is_paused(self) -> bool:
        """Check if game is paused"""
        return self.state == GameState.PAUSED
    
    def is_game_over(self) -> bool:
        """Check if game is over"""
        return self.state == GameState.GAME_OVER
    
    def is_won(self) -> bool:
        """Check if game is won"""
        return self.state == GameState.WIN
    
    def pause(self):
        """Pause the game"""
        if self.state == GameState.PLAYING:
            self.set_state(GameState.PAUSED)
    
    def resume(self):
        """Resume the game"""
        if self.state == GameState.PAUSED:
            self.set_state(GameState.PLAYING)
    
    def game_over(self):
        """Set game over state"""
        self.set_state(GameState.GAME_OVER)
    
    def win(self):
        """Set win state"""
        self.set_state(GameState.WIN)
    
    def reset(self):
        """Reset game state"""
        self.state = GameState.PLAYING
        self.previous_state = None

