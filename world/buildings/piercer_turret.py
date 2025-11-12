"""
Piercer turret - low rate of fire, high damage, pierces enemies.
"""
import pygame
import math
import constants as c
from world.building import Building, Cost, BuildState
from world.projectile import Projectile

class PiercerTurret(Building):
    """Piercer turret - low ROF, high damage, pierces through enemies"""
    TYPE_ID = "turret_piercer"
    BASE_HP = 250
    BUILD_TIME = 3.0
    COST = Cost(wood=50, iron=40)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    
    def __init__(self, grid_pos, sprite_sheet, base_image, tier=1, uid=None):
        super().__init__(grid_pos, tier=tier, uid=uid)
        
        # Piercer-specific attributes
        self.cooldown = 2000  # milliseconds - slow firing
        self.range = 250  # pixels - longer range
        self.damage = 25  # damage per shot - high damage
        self.projectile_speed = 600.0  # pixels per second - very fast projectiles
        self.pierce = True  # Pierces through enemies
        self.pierce_count = 3  # Number of enemies to pierce
        self.angle = 0
        self.target_angle = 0
        self.rotation_speed = 120  # degrees per second - slower rotation
        self.base_image = base_image
        self.selected = False
        
        # Animation state
        self.sprite_sheet = sprite_sheet
        self.animation_list = self.load_image()
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.last_shot = pygame.time.get_ticks()
        self.is_shooting = False
        self.animation_playing = False
        self.target_enemy = None
        
        self.turret_image = self.animation_list[self.frame_index]
        
        base_rect = self.base_image.get_rect()
        turret_rect = self.turret_image.get_rect()
        self.rect = pygame.Rect(0, 0, max(base_rect.width, turret_rect.width),
                                max(base_rect.height, turret_rect.height))
        self.rect.center = self.pos
        
        self.create_range_circle()
        self.projectile_group = None
        self.enemy_group = None
    
    def create_range_circle(self):
        """Create range circle"""
        self.range_image = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.range_image, (150, 100, 100, 100), (self.range, self.range), self.range)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center
    
    def load_image(self):
        """Load animation frames"""
        size = self.sprite_sheet.get_height()
        animation_list = []
        for x in range(c.ANIMATION_STEPS):
            temp_img = self.sprite_sheet.subsurface(x*size, 0, size, size)
            animation_list.append(temp_img)
        return animation_list
    
    def find_nearest_enemy(self, enemy_group):
        """Find nearest enemy within range"""
        if not enemy_group:
            return None
        
        nearest_enemy = None
        nearest_distance = float('inf')
        
        for enemy in enemy_group:
            if not enemy.alive:
                continue
            
            distance = math.sqrt(
                (enemy.pos.x - self.pos.x) ** 2 +
                (enemy.pos.y - self.pos.y) ** 2
            )
            
            if distance <= self.range and distance < nearest_distance:
                nearest_distance = distance
                nearest_enemy = enemy
        
        return nearest_enemy
    
    def calculate_angle_to_target(self, target_pos):
        """Calculate angle to target"""
        dx = target_pos.x - self.pos.x
        dy = target_pos.y - self.pos.y
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # Rotation offset
        rotation_offset = 90
        angle_deg += rotation_offset
        
        return angle_deg
    
    def rotate_toward_target(self, dt, target_angle):
        """Rotate toward target"""
        # Normalize angles
        while self.angle < 0:
            self.angle += 360
        while self.angle >= 360:
            self.angle -= 360
        while target_angle < 0:
            target_angle += 360
        while target_angle >= 360:
            target_angle -= 360
        
        # Calculate shortest rotation
        diff = target_angle - self.angle
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        
        # Rotate toward target
        max_rotation = self.rotation_speed * dt
        if abs(diff) <= max_rotation:
            self.angle = target_angle
        else:
            self.angle += max_rotation if diff > 0 else -max_rotation
        
        # Normalize again
        while self.angle < 0:
            self.angle += 360
        while self.angle >= 360:
            self.angle -= 360
    
    def is_aimed_at_target(self, target_angle, tolerance=5.0):
        """Check if aimed at target"""
        angle_diff = abs(self.angle - target_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        return angle_diff <= tolerance
    
    def shoot(self, target_enemy):
        """Shoot at target with piercing projectile"""
        if target_enemy and target_enemy.alive:
            current_time = pygame.time.get_ticks()
            self.is_shooting = True
            self.animation_playing = True
            self.frame_index = 0
            self.update_time = current_time
            self.last_shot = current_time
            
            if self.projectile_group is not None:
                # Create piercing projectile
                projectile = PiercingProjectile(
                    start_pos=(self.pos.x, self.pos.y),
                    target_pos=(target_enemy.pos.x, target_enemy.pos.y),
                    speed=self.projectile_speed,
                    damage=self.damage,
                    pierce_count=self.pierce_count,
                    enemy_group=self.enemy_group
                )
                self.projectile_group.add(projectile)
    
    def play_shooting_animation(self, dt):
        """Play shooting animation"""
        if not self.is_shooting or not self.animation_playing:
            return
        
        current_time = pygame.time.get_ticks()
        if current_time - self.update_time >= c.ANIMATION_DELAY:
            self.update_time = current_time
            self.frame_index += 1
            
            if self.frame_index >= len(self.animation_list):
                self.frame_index = 0
                self.animation_playing = False
        
        self.frame_index = min(self.frame_index, len(self.animation_list) - 1)
        self.turret_image = self.animation_list[self.frame_index]
    
    def get_rotated_turret(self):
        """Get rotated turret image"""
        current_frame = self.animation_list[self.frame_index]
        rotated_image = pygame.transform.rotate(current_frame, -self.angle)
        return rotated_image
    
    def update(self, dt: float, world=None):
        """Update turret"""
        super().update(dt, world)
        
        if self.state == BuildState.ACTIVE:
            enemy_group = None
            if world and hasattr(world, 'enemy_group'):
                enemy_group = world.enemy_group
                self.enemy_group = enemy_group
            if world and hasattr(world, 'projectile_group'):
                self.projectile_group = world.projectile_group
            
            if enemy_group:
                nearest_enemy = self.find_nearest_enemy(enemy_group)
                
                if nearest_enemy and nearest_enemy.alive:
                    target_angle = self.calculate_angle_to_target(nearest_enemy.pos)
                    self.target_angle = target_angle
                    self.target_enemy = nearest_enemy
                    
                    self.rotate_toward_target(dt, target_angle)
                    
                    current_time = pygame.time.get_ticks()
                    time_since_last_shot = current_time - self.last_shot
                    can_shoot = time_since_last_shot >= self.cooldown
                    is_aimed = self.is_aimed_at_target(target_angle, tolerance=5.0)
                    
                    if can_shoot and is_aimed and not self.animation_playing:
                        self.shoot(nearest_enemy)
                else:
                    self.target_enemy = None
                    if not self.animation_playing:
                        self.is_shooting = False
                        self.frame_index = 0
                        self.turret_image = self.animation_list[self.frame_index]
            
            if self.is_shooting and self.animation_playing:
                self.play_shooting_animation(dt)
            elif not self.is_shooting:
                self.frame_index = 0
                self.turret_image = self.animation_list[self.frame_index]
    
    def draw(self, surface: pygame.Surface):
        """Draw turret"""
        # Draw range circle if selected (behind base)
        if self.selected and self.state == BuildState.ACTIVE:
            self.update_range_position()
            surface.blit(self.range_image, self.range_rect)
        
        # Draw base
        base_rect = self.base_image.get_rect(center=self.pos)
        surface.blit(self.base_image, base_rect)
        
        # Draw construction overlay if constructing
        if self.state == BuildState.CONSTRUCTING:
            w, h = self.FOOTPRINT
            overlay = pygame.Surface((w * 32, h * 32), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            overlay_rect = overlay.get_rect(center=self.pos)
            surface.blit(overlay, overlay_rect)
            
            # Draw progress bar
            pct = self.progress / self.BUILD_TIME if self.BUILD_TIME > 0 else 1.0
            bar_width = w * 32 - 4
            bar_height = 4
            bar_x = overlay_rect.x + 2
            bar_y = overlay_rect.bottom - 6
            pygame.draw.rect(surface, (200, 220, 80), (bar_x, bar_y, int(bar_width * pct), bar_height))
        elif self.state == BuildState.ACTIVE:
            # Draw turret head
            rotated_turret = self.get_rotated_turret()
            turret_rect = rotated_turret.get_rect(center=self.pos)
            surface.blit(rotated_turret, turret_rect)
            
            # Draw HP bar if damaged
            if self.hp < self.max_hp:
                hp_pct = self.hp / self.max_hp
                hp_color = (0, 255, 0) if hp_pct > 0.5 else (255, 255, 0) if hp_pct > 0.25 else (255, 0, 0)
                bar_width = 30
                bar_height = 4
                bar_x = self.rect.centerx - bar_width // 2
                bar_y = self.rect.top - 8
                pygame.draw.rect(surface, (0, 0, 0), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2))
                pygame.draw.rect(surface, hp_color, (bar_x, bar_y, int(bar_width * hp_pct), bar_height))
    
    def update_range_position(self):
        """Update range circle position"""
        self.range_rect.center = self.rect.center


# Piercing projectile class
class PiercingProjectile(Projectile):
    """Projectile that pierces through multiple enemies"""
    
    def __init__(self, start_pos, target_pos, speed=400.0, damage=10, pierce_count=3, enemy_group=None):
        super().__init__(start_pos, target_pos, speed, damage, target_type="enemy")
        self.pierce_count = pierce_count
        self.pierced_enemies = set()  # Track which enemies have been hit
        self.enemy_group = enemy_group
    
    def update(self, dt: float, enemy_group=None, building_group=None):
        """Update piercing projectile"""
        if not self.active:
            return
        
        # Use provided enemy group or stored one
        if enemy_group is None:
            enemy_group = self.enemy_group
        
        # Move projectile
        self.pos += self.velocity * dt
        self.rect.center = self.pos
        
        # Check collision with enemies (piercing)
        if enemy_group:
            for enemy in enemy_group:
                if enemy.alive and enemy not in self.pierced_enemies:
                    if self.rect.colliderect(enemy.rect):
                        # Hit enemy
                        enemy.take_damage(self.damage)
                        self.pierced_enemies.add(enemy)
                        self.hit = True
                        
                        # Check if pierce count exceeded
                        if len(self.pierced_enemies) >= self.pierce_count:
                            self.active = False
                            return
        
        # Check if projectile has traveled too far
        distance_traveled = (self.pos - self.start_pos).length()
        if distance_traveled > 800:  # Max range for piercer
            self.active = False
        
        # Check if out of bounds
        if self.pos.x < 0 or self.pos.x > 1920 or self.pos.y < 0 or self.pos.y > 1080:
            self.active = False

