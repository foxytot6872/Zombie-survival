"""
Swarmling zombie enemy - tiny HP, very fast.
"""
import pygame
from world.enemy import Enemy
from typing import Tuple, Optional

class SwarmlingZombie(Enemy):
    """Swarmling zombie - very fast but very weak."""
    TYPE_ID = "swarmling"
    BASE_HP = 10
    SPEED = 80.0  # pixels per second - very fast
    DAMAGE = 2
    ATTACK_RANGE = 24.0  # pixels - small reach
    ATTACK_COOLDOWN = 0.5  # seconds - very fast attacks
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None):
        super().__init__(pos, hp)
        # Make swarmling smaller
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        # Default to moving down if no buildings found
        self.set_direction((0, 1))
    
    def draw_body(self, surface: pygame.Surface):
        """Draw swarmling zombie body"""
        self.image.fill((0, 0, 0, 0))
        
        # Draw swarmling (small, grey/brown - tiny)
        if self.alive:
            # Body (small)
            pygame.draw.rect(self.image, (120, 100, 80), (4, 6, 12, 10))
            # Head (small)
            pygame.draw.circle(self.image, (100, 80, 60), (10, 7), 3)
            # Eyes (tiny dots)
            pygame.draw.circle(self.image, (150, 0, 0), (9, 6), 1)
            pygame.draw.circle(self.image, (150, 0, 0), (11, 6), 1)
            # Outline
            pygame.draw.rect(self.image, (80, 60, 40), (4, 6, 12, 10), 1)
        else:
            # Dead swarmling (grey)
            pygame.draw.rect(self.image, (60, 60, 60), (4, 6, 12, 10))
        
        surface.blit(self.image, self.rect)

