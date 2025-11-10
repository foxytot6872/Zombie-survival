import pygame as pg
import math

class Enemy(pg.sprite.Sprite):
    def __init__(self, path, speed=1, health=100, reward=10):
        pg.sprite.Sprite.__init__(self)
        # Create a simple red square for the enemy
        self.image = pg.Surface((30, 30))
        self.image.fill((200, 50, 50))
        pg.draw.circle(self.image, (150, 0, 0), (15, 15), 15)
        self.rect = self.image.get_rect()
        
        self.path = path  # List of waypoints [(x1, y1), (x2, y2), ...]
        self.path_index = 0
        self.speed = speed
        self.max_health = health
        self.health = health
        self.reward = reward
        
        # Start at first waypoint
        if self.path:
            self.rect.center = self.path[0]
            self.path_index = 1
    
    def update(self):
        if self.path_index < len(self.path):
            target = self.path[self.path_index]
            dx = target[0] - self.rect.centerx
            dy = target[1] - self.rect.centery
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < self.speed:
                # Reached waypoint, move to next
                self.rect.center = target
                self.path_index += 1
            else:
                # Move toward waypoint
                self.rect.centerx += (dx / distance) * self.speed
                self.rect.centery += (dy / distance) * self.speed
    
    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0
    
    def get_progress(self):
        """Returns how far along the path the enemy is (0.0 to 1.0)"""
        if not self.path or self.path_index >= len(self.path):
            return 1.0
        return self.path_index / len(self.path)