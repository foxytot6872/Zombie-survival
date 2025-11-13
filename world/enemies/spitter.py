"""
Spitter zombie enemy - ranged attacker.
"""
import pygame
from world.enemy import Enemy
from world.projectile import Projectile
from typing import Tuple, Optional

class SpitterZombie(Enemy):
    """Spitter zombie - ranged attacker with projectile."""
    TYPE_ID = "spitter"
    BASE_HP = 40
    SPEED = 25.0  # pixels per second - slower than basic zombie
    DAMAGE = 8  # Melee damage if close
    ATTACK_RANGE = 150.0  # pixels - ranged attack
    ATTACK_COOLDOWN = 2.0  # seconds - slower ranged attacks
    RANGED_DAMAGE = 12  # Ranged damage
    PROJECTILE_SPEED = 200.0  # pixels per second
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None):
        super().__init__(pos, hp)
        self.ranged = True
        self.range_damage = self.RANGED_DAMAGE
        self.projectile_speed = self.PROJECTILE_SPEED
        # Default to moving down if no buildings found
        self.set_direction((0, 1))
    
    def draw_body(self, surface: pygame.Surface):
        """Draw spitter zombie body"""
        self.image.fill((0, 0, 0, 0))
        
        # Draw spitter (purple/green - toxic appearance)
        if self.alive:
            # Body (slender, ranged)
            pygame.draw.rect(self.image, (100, 50, 150), (5, 9, 22, 18))
            # Head
            pygame.draw.circle(self.image, (80, 40, 130), (16, 11), 6)
            # Eyes (green dots - toxic)
            pygame.draw.circle(self.image, (0, 255, 0), (14, 10), 1)
            pygame.draw.circle(self.image, (0, 255, 0), (18, 10), 1)
            # Mouth (open, ready to spit)
            pygame.draw.ellipse(self.image, (50, 150, 50), (14, 13, 4, 3))
            # Outline
            pygame.draw.rect(self.image, (70, 30, 120), (5, 9, 22, 18), 2)
        else:
            # Dead spitter (grey)
            pygame.draw.rect(self.image, (70, 70, 70), (5, 9, 22, 18))
        
        surface.blit(self.image, self.rect)
    
    def attack_building(self, building):
        """Attack a building with ranged attack if far, melee if close"""
        if not building or not hasattr(building, 'take_damage'):
            return
        
        distance = (self.pos - building.pos).length()
        
        # Ranged attack if in range and far enough
        if distance > 50 and self.ranged and distance <= self.attack_range:
            # Spawn projectile (if projectile group exists)
            if hasattr(self, 'projectile_group') and self.projectile_group is not None:
                # Create enemy projectile (targets buildings)
                projectile = Projectile(
                    start_pos=(self.pos.x, self.pos.y),
                    target_pos=(building.pos.x, building.pos.y),
                    speed=self.projectile_speed,
                    damage=self.range_damage,
                    target_type="building"  # Target buildings, not enemies
                )
                # Change projectile color to green (acid)
                projectile.image.fill((0, 0, 0, 0))
                pygame.draw.circle(projectile.image, (100, 255, 100), (4, 4), 3)
                pygame.draw.circle(projectile.image, (0, 255, 0), (4, 4), 1)
                self.projectile_group.add(projectile)
        elif distance <= 32:  # Close range - melee attack
            # Melee attack if close
            # Pass world for damage modifiers
            world = getattr(self, 'world', None)
            building.take_damage(self.damage, world)
        
        self.on_attack(building)

