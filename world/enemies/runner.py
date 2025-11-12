"""
Runner zombie enemy - fast, low HP.
"""
import pygame
from world.enemy import Enemy
from typing import Tuple, Optional

class RunnerZombie(Enemy):
    """Runner zombie - fast but weak."""
    TYPE_ID = "runner"
    BASE_HP = 25
    SPEED = 60.0  # pixels per second - faster than basic zombie
    DAMAGE = 3
    ATTACK_RANGE = 32.0
    ATTACK_COOLDOWN = 0.8  # seconds - faster attacks
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None):
        super().__init__(pos, hp)
        # Default to moving down if no buildings found
        self.set_direction((0, 1))
    
    def draw_body(self, surface: pygame.Surface):
        """Draw runner zombie body"""
        self.image.fill((0, 0, 0, 0))
        
        # Draw runner (orange/yellow rectangle - faster appearance)
        if self.alive:
            # Body (leaner, more agile)
            pygame.draw.rect(self.image, (200, 150, 50), (6, 10, 20, 16))
            # Head
            pygame.draw.circle(self.image, (180, 130, 40), (16, 12), 5)
            # Eyes (yellow dots - more alert)
            pygame.draw.circle(self.image, (255, 200, 0), (14, 11), 1)
            pygame.draw.circle(self.image, (255, 200, 0), (18, 11), 1)
            # Outline
            pygame.draw.rect(self.image, (150, 100, 30), (6, 10, 20, 16), 2)
        else:
            # Dead runner (grey)
            pygame.draw.rect(self.image, (80, 80, 80), (6, 10, 20, 16))
        
        surface.blit(self.image, self.rect)

