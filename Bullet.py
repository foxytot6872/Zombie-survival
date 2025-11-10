import pygame as pg
import math

class Bullet(pg.sprite.Sprite):
    def __init__(self, start_pos, target, damage, speed=8):
        pg.sprite.Sprite.__init__(self)
        # Create bullet image
        self.image = pg.Surface((8, 8))
        self.image.fill((255, 255, 0))
        pg.draw.circle(self.image, (255, 200, 0), (4, 4), 4)
        
        self.rect = self.image.get_rect()
        self.rect.center = start_pos
        
        self.target = target
        self.damage = damage
        self.speed = speed
        
        # Calculate direction
        if target:
            dx = target.rect.centerx - start_pos[0]
            dy = target.rect.centery - start_pos[1]
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                self.dx = (dx / distance) * speed
                self.dy = (dy / distance) * speed
            else:
                self.dx = 0
                self.dy = 0
        else:
            self.dx = 0
            self.dy = 0
    
    def update(self):
        if self.target and self.target.alive():
            # Update direction to track moving target
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                self.dx = (dx / distance) * self.speed
                self.dy = (dy / distance) * self.speed
        
        self.rect.centerx += self.dx
        self.rect.centery += self.dy
    
    def check_hit(self, enemies):
        """Check if bullet hit an enemy"""
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                return enemy
        return None

