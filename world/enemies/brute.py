"""
Brute zombie enemy - high HP, slow, high damage.
"""
import pygame
from world.enemy import Enemy
from typing import Tuple, Optional

class BruteZombie(Enemy):
    """Brute zombie - slow but tough and strong."""
    TYPE_ID = "brute"
    BASE_HP = 200
    SPEED = 15.0  # pixels per second - slower than basic zombie
    DAMAGE = 15
    ATTACK_RANGE = 40.0  # pixels - longer reach
    ATTACK_COOLDOWN = 1.5  # seconds - slower attacks but more damage
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None):
        super().__init__(pos, hp)
        # Default to moving down if no buildings found
        self.set_direction((0, 1))
    
    def draw_body(self, surface: pygame.Surface):
        """Draw brute zombie body"""
        self.image.fill((0, 0, 0, 0))
        
        # Draw brute (large, dark red/brown - intimidating)
        if self.alive:
            # Body (larger, bulkier)
            pygame.draw.rect(self.image, (100, 30, 30), (2, 6, 28, 24))
            # Head (larger)
            pygame.draw.circle(self.image, (80, 20, 20), (16, 10), 8)
            # Eyes (red dots - angry)
            pygame.draw.circle(self.image, (255, 0, 0), (13, 9), 2)
            pygame.draw.circle(self.image, (255, 0, 0), (19, 9), 2)
            # Muscles/features (darker areas)
            pygame.draw.rect(self.image, (70, 15, 15), (2, 6, 28, 24), 3)
        else:
            # Dead brute (grey)
            pygame.draw.rect(self.image, (60, 60, 60), (2, 6, 28, 24))
        
        surface.blit(self.image, self.rect)

