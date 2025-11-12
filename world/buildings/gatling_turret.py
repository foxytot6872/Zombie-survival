"""
Gatling turret - high rate of fire, low damage, short range.
"""
import pygame
import math
import constants as c
from world.building import Building, Cost, BuildState
from world.projectile import Projectile

class GatlingTurret(Building):
    """Gatling turret - high ROF, low damage, short range"""
    TYPE_ID = "turret_gatling"
    BASE_HP = 150
    BUILD_TIME = 2.0
    COST = Cost(wood=30, iron=20)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    
    def __init__(self, grid_pos, turret_image, base_image, tier=1, uid=None):
        super().__init__(grid_pos, tier=tier, uid=uid)
        
        # Gatling-specific attributes
        self.cooldown = 300  # milliseconds - very fast firing
        self.range = 150  # pixels - shorter range
        self.damage = 5  # damage per shot - low damage
        self.projectile_speed = 500.0  # pixels per second - fast projectiles
        self.angle = 0
        self.target_angle = 0
        self.rotation_speed = 240  # degrees per second - fast rotation
        self.base_image = base_image
        self.selected = False
        
        # Static image (not animated) - scale it up
        original_image = turret_image
        # Scale up by 1.5x for bigger appearance
        scale_factor = 1.5
        original_width, original_height = original_image.get_size()
        scaled_width = int(original_width * scale_factor)
        scaled_height = int(original_height * scale_factor)
        self.turret_image = pygame.transform.scale(original_image, (scaled_width, scaled_height))
        
        # Vertical offset to center turret on base (move up by a few pixels)
        self.turret_offset_y = -8  # Negative means move up
        
        base_rect = self.base_image.get_rect()
        turret_rect = self.turret_image.get_rect()
        self.rect = pygame.Rect(0, 0, max(base_rect.width, turret_rect.width),
                                max(base_rect.height, turret_rect.height))
        self.rect.center = self.pos
        
        self.create_range_circle()
        self.projectile_group = None
        self.target_enemy = None
        self.last_shot = pygame.time.get_ticks()
    
    def create_range_circle(self):
        """Create range circle"""
        self.range_image = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.range_image, (100, 150, 100, 100), (self.range, self.range), self.range)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center
    
    
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
        
        # Rotation offset (sprite points up by default)
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
    
    def is_aimed_at_target(self, target_angle, tolerance=15.0):
        """Check if aimed at target"""
        angle_diff = abs(self.angle - target_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        return angle_diff <= tolerance
    
    def shoot(self, target_enemy):
        """Shoot at target"""
        if target_enemy and target_enemy.alive:
            current_time = pygame.time.get_ticks()
            self.last_shot = current_time
            
            if self.projectile_group is not None:
                # Use the turret's visual position (with offset) for projectile spawn
                turret_visual_pos = pygame.Vector2(self.pos.x, self.pos.y + self.turret_offset_y)
                projectile = Projectile(
                    start_pos=(turret_visual_pos.x, turret_visual_pos.y),
                    target_pos=(target_enemy.pos.x, target_enemy.pos.y),
                    speed=self.projectile_speed,
                    damage=self.damage,
                    target_type="enemy"  # Target enemies
                )
                self.projectile_group.add(projectile)
    
    def get_rotated_turret(self):
        """Get rotated turret image"""
        rotated_image = pygame.transform.rotate(self.turret_image, -self.angle)
        return rotated_image
    
    def update(self, dt: float, world=None):
        """Update turret"""
        super().update(dt, world)
        
        if self.state == BuildState.ACTIVE:
            enemy_group = None
            if world and hasattr(world, 'enemy_group'):
                enemy_group = world.enemy_group
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
                    is_aimed = self.is_aimed_at_target(target_angle, tolerance=15.0)
                    
                    if can_shoot and is_aimed:
                        self.shoot(nearest_enemy)
                else:
                    self.target_enemy = None
    
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
            # Draw turret head (centered on base with vertical offset)
            rotated_turret = self.get_rotated_turret()
            # Center the turret on the base position, but offset vertically to center it better
            turret_pos = pygame.Vector2(self.pos.x, self.pos.y + self.turret_offset_y)
            turret_rect = rotated_turret.get_rect(center=turret_pos)
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

