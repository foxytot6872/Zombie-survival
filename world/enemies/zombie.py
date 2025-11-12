"""
Basic Zombie enemy.
"""
import pygame
from world.enemy import Enemy
from typing import Tuple, Optional

class BasicZombie(Enemy):
    """Basic zombie enemy - targets and attacks buildings."""
    TYPE_ID = "walker"  # Changed to match waves.json
    BASE_HP = 50
    SPEED = 30.0  # pixels per second
    DAMAGE = 5
    ATTACK_RANGE = 32.0  # pixels - range for attacking buildings
    ATTACK_COOLDOWN = 1.0  # seconds - time between attacks
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None):
        super().__init__(pos, hp)
        
        # Zombie-specific: will target buildings (movement handled in base class)
        # Default to moving down if no buildings found
        self.set_direction((0, 1))  # Down direction (fallback)
    
    def draw_body(self, surface: pygame.Surface):
        """Draw zombie body"""
        self.image.fill((0, 0, 0, 0))
        
        # Draw zombie (green rectangle with darker green outline)
        if self.alive:
            # Body
            pygame.draw.rect(self.image, (100, 150, 100), (4, 8, 24, 20))
            # Head
            pygame.draw.circle(self.image, (80, 120, 80), (16, 10), 6)
            # Eyes (red dots)
            pygame.draw.circle(self.image, (200, 0, 0), (14, 9), 1)
            pygame.draw.circle(self.image, (200, 0, 0), (18, 9), 1)
            # Outline
            pygame.draw.rect(self.image, (50, 100, 50), (4, 8, 24, 20), 2)
        else:
            # Dead zombie (grey)
            pygame.draw.rect(self.image, (80, 80, 80), (4, 8, 24, 20))
        
        surface.blit(self.image, self.rect)

