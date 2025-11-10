import pygame as pg

class Base(pg.sprite.Sprite):
    def __init__(self, pos, max_health=100):
        pg.sprite.Sprite.__init__(self)
        # Create a simple base image
        self.image = pg.Surface((60, 60))
        self.image.fill((100, 100, 200))
        pg.draw.rect(self.image, (50, 50, 150), (0, 0, 60, 60), 3)
        pg.draw.circle(self.image, (150, 150, 255), (30, 30), 20)
        
        self.rect = self.image.get_rect()
        self.rect.center = pos
        
        self.max_health = max_health
        self.health = max_health
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0
        return self.health <= 0
    
    def draw_health_bar(self, screen):
        """Draw health bar above the base"""
        bar_width = 60
        bar_height = 8
        x = self.rect.centerx - bar_width // 2
        y = self.rect.top - 15
        
        # Background
        pg.draw.rect(screen, (100, 0, 0), (x, y, bar_width, bar_height))
        # Health
        health_width = int(bar_width * (self.health / self.max_health))
        pg.draw.rect(screen, (0, 200, 0), (x, y, health_width, bar_height))
        # Border
        pg.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 1)

