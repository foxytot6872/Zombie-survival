"""
Projectile system for turrets and other weapons.
"""
from __future__ import annotations
import pygame
import math
from typing import Tuple, Optional

class Projectile(pygame.sprite.Sprite):
    """Base projectile class"""
    
    def __init__(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float], 
                 speed: float = 400.0, damage: int = 10, target_type: str = "enemy"):
        super().__init__()
        self.start_pos = pygame.Vector2(start_pos)
        self.target_pos = pygame.Vector2(target_pos)
        self.pos = pygame.Vector2(start_pos)
        self.speed = speed  # pixels per second
        self.damage = damage
        self.target_type = target_type  # "enemy" or "building"
        
        # Calculate direction to target
        direction = (self.target_pos - self.start_pos)
        if direction.length() > 0:
            self.velocity = direction.normalize() * self.speed
        else:
            self.velocity = pygame.Vector2(0, 0)
        
        # Rendering
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        
        # State
        self.active = True
        self.hit = False
        
        # Draw projectile
        self.draw_projectile()
    
    def draw_projectile(self):
        """Draw the projectile"""
        self.image.fill((0, 0, 0, 0))
        # Yellow/orange bullet
        pygame.draw.circle(self.image, (255, 200, 0), (4, 4), 3)
        pygame.draw.circle(self.image, (255, 255, 255), (4, 4), 1)
    
    def update(self, dt: float, enemy_group=None, building_group=None):
        """Update projectile position and check collisions"""
        if not self.active:
            return
        
        # Move projectile
        self.pos += self.velocity * dt
        self.rect.center = self.pos
        
        # Check collision based on target type
        if self.target_type == "enemy":
            # Check collision with enemies (turret projectiles)
            if enemy_group:
                for enemy in enemy_group:
                    if enemy.alive and self.rect.colliderect(enemy.rect):
                        # Hit enemy
                        enemy.take_damage(self.damage)
                        self.hit = True
                        self.active = False
                        return
        elif self.target_type == "building":
            # Check collision with buildings (enemy projectiles, e.g., spitter)
            if building_group:
                for building in building_group:
                    if (hasattr(building, 'state') and 
                        building.state != "destroyed" and
                        self.rect.colliderect(building.rect)):
                        # Hit building
                        if hasattr(building, 'take_damage'):
                            building.take_damage(self.damage)
                        self.hit = True
                        self.active = False
                        return
        
        # Check if projectile has traveled too far (despawn after range)
        distance_traveled = (self.pos - self.start_pos).length()
        if distance_traveled > 500:  # Max range
            self.active = False
        
        # Check if out of bounds
        if self.pos.x < 0 or self.pos.x > 1920 or self.pos.y < 0 or self.pos.y > 1080:
            self.active = False
    
    def draw(self, surface: pygame.Surface):
        """Draw the projectile"""
        if self.active:
            surface.blit(self.image, self.rect)

