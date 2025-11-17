"""
Flamethrower turret - short range, area damage, continuous fire.
"""
import pygame
import math
import constants as c
from world.building import Building, Cost, BuildState
from world.projectile import Projectile

class FlamethrowerTurret(Building):
    """Flamethrower turret - short range, area damage"""
    TYPE_ID = "turret_flamethrower"
    BASE_HP = 180
    BUILD_TIME = 2.5
    COST = Cost(wood=50, iron=40)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    ALLOW_MAX_TIER_PROGRESS = True
    
    def __init__(self, grid_pos, sprite_sheets=None, base_images=None, tier=1, uid=None, world=None):
        """Initialize Flamethrower turret."""
        super().__init__(grid_pos, tier=tier, uid=uid, world=world)
        
        # Flamethrower-specific attributes
        self.base_cooldown = 200  # milliseconds - fast firing
        self.cooldown = self.base_cooldown
        self.base_range = 120  # pixels - very short range
        self.range = self.base_range
        self.damage = 8  # damage per shot
        self.effective_damage = self.damage
        self.projectile_speed = 300.0  # pixels per second - slower projectiles
        self.noise_value = 2  # Noise value for spawn attraction
        self.effective_projectile_speed = self.projectile_speed
        self.angle = 0
        self.target_angle = 0
        self.rotation_speed = 200  # degrees per second
        self.selected = False
        
        # Handle sprite sheets and base images
        if sprite_sheets is not None and base_images is not None:
            self.sprite_sheets = self._normalize_sprite_sheets(sprite_sheets)
            self.base_images = self._normalize_base_images(base_images)
            self.base_image = self._get_base_image_for_tier(self.tier)
            self.sprite_sheet = self._get_sprite_sheet_for_tier(self.tier)
        else:
            # Create placeholder
            placeholder_base = pygame.Surface((32, 32))
            placeholder_base.fill((200, 100, 50))  # Orange/red for flamethrower
            self.base_images = [placeholder_base]
            self.base_image = placeholder_base
            placeholder_turret = pygame.Surface((32, 32))
            placeholder_turret.fill((255, 150, 0))  # Bright orange
            self.sprite_sheets = [placeholder_turret]
            self.sprite_sheet = placeholder_turret
        
        # Animation state
        self.animation_state = "idle"
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.08  # seconds per frame
        self.animation_list = []
        self.is_animated = False
        
        # Load animation frames
        if self.sprite_sheet:
            self._load_animation_frames()
        
        # Firing state
        self.last_shot = pygame.time.get_ticks()
        self.is_shooting = False
        self.target_enemy = None
        
        # Target check cooldown
        self.last_target_check = 0.0
        self.target_check_interval = 0.25  # seconds
        
        # Projectile group (will be set by world)
        self.projectile_group = None
        
        # Update rect
        self._refresh_rect()
    
    def _normalize_sprite_sheets(self, sprite_sheets):
        """Normalize sprite sheets to list format"""
        if isinstance(sprite_sheets, list):
            return sprite_sheets
        return [sprite_sheets]
    
    def _normalize_base_images(self, base_images):
        """Normalize base images to list format"""
        if isinstance(base_images, list):
            return base_images
        return [base_images]
    
    def _get_sprite_sheet_for_tier(self, tier):
        """Get sprite sheet for given tier"""
        if not self.sprite_sheets:
            return None
        tier_index = min(tier - 1, len(self.sprite_sheets) - 1)
        return self.sprite_sheets[tier_index]
    
    def _get_base_image_for_tier(self, tier):
        """Get base image for given tier"""
        if not self.base_images:
            return None
        tier_index = min(tier - 1, len(self.base_images) - 1)
        base_img = self.base_images[tier_index]
        # Check if it's a sprite sheet (for animated bases like Gatling lv3)
        if isinstance(base_img, pygame.Surface) and base_img.get_width() > 64:
            # Assume it's a sprite sheet, use first frame
            return base_img.subsurface((0, 0, 64, 64))
        return base_img
    
    def _load_animation_frames(self):
        """Load animation frames from sprite sheet"""
        if not self.sprite_sheet:
            return
        
        size = 64  # Default frame size
        if hasattr(self.sprite_sheet, 'get_height'):
            size = self.sprite_sheet.get_height()
        
        sheet_width = self.sprite_sheet.get_width()
        num_frames = sheet_width // size if size > 0 else 1
        
        self.animation_list = []
        for i in range(num_frames):
            if i * size < sheet_width:
                frame = self.sprite_sheet.subsurface((i * size, 0, size, size))
                self.animation_list.append(frame)
        
        if self.animation_list:
            self.is_animated = True
    
    def _refresh_rect(self):
        """Update rect to match base image size"""
        if self.base_image:
            self.rect = self.base_image.get_rect(center=self.pos)
        else:
            self.rect = pygame.Rect(0, 0, 32, 32)
            self.rect.center = self.pos
    
    def find_nearest_enemy(self, enemy_group, spatial_grid=None):
        """Find the nearest enemy within range"""
        if not enemy_group:
            return None
        
        nearest_enemy = None
        nearest_distance = float('inf')
        
        # Use spatial grid if available
        if spatial_grid:
            nearby_enemies = spatial_grid.get_nearby(self.pos, self.range)
            candidates = [e for e in nearby_enemies if hasattr(e, 'alive') and e.alive]
        else:
            candidates = [e for e in enemy_group if hasattr(e, 'alive') and e.alive]
        
        for enemy in candidates:
            if not hasattr(enemy, 'pos'):
                continue
            distance = (self.pos - enemy.pos).length()
            if distance <= self.range and distance < nearest_distance:
                nearest_enemy = enemy
                nearest_distance = distance
        
        return nearest_enemy
    
    def update(self, dt, world=None, enemy_group=None, projectile_group=None, spatial_grid=None):
        """Update turret"""
        super().update(dt, world)
        
        # Get enemy_group and projectile_group from world if not provided
        if world:
            if enemy_group is None and hasattr(world, 'enemy_group'):
                enemy_group = world.enemy_group
            if projectile_group is None and hasattr(world, 'projectile_group'):
                projectile_group = world.projectile_group
            if spatial_grid is None and hasattr(world, 'spatial_grid'):
                spatial_grid = world.spatial_grid
        
        if self.state != BuildState.ACTIVE:
            return
        
        # Set projectile group if provided
        if projectile_group:
            self.projectile_group = projectile_group
        
        # Update range and damage from modifiers
        if world and hasattr(world, 'modifiers'):
            range_mult = world.modifiers.get("turret_range_mult", 1.0)
            self.range = int(self.base_range * range_mult)
            damage_mult = world.modifiers.get("turret_damage_mult", 1.0)
            self.effective_damage = int(self.damage * damage_mult)
            fire_rate_mult = world.modifiers.get("turret_fire_rate_mult", 1.0)
            self.cooldown = int(self.base_cooldown / fire_rate_mult)
        
        if not enemy_group:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Check for targets periodically
        if current_time - (self.last_target_check * 1000) >= self.target_check_interval * 1000:
            self.target_enemy = self.find_nearest_enemy(enemy_group, spatial_grid)
            self.last_target_check = current_time / 1000.0
        
        # Rotate toward target
        if self.target_enemy and hasattr(self.target_enemy, 'pos'):
            direction = self.target_enemy.pos - self.pos
            if direction.length() > 0:
                target_angle = math.degrees(math.atan2(direction.y, direction.x))
                # Normalize angle
                angle_diff = target_angle - self.angle
                while angle_diff > 180:
                    angle_diff -= 360
                while angle_diff < -180:
                    angle_diff += 360
                
                # Rotate toward target
                max_rotation = self.rotation_speed * dt
                if abs(angle_diff) <= max_rotation:
                    self.angle = target_angle
                else:
                    self.angle += max_rotation if angle_diff > 0 else -max_rotation
        else:
            self.target_enemy = None
        
        # Fire at target
        if self.target_enemy and hasattr(self.target_enemy, 'pos'):
            distance = (self.pos - self.target_enemy.pos).length()
            if distance <= self.range:
                if current_time - self.last_shot >= self.cooldown:
                    self.fire(self.target_enemy.pos)
                    self.last_shot = current_time
                    self.is_shooting = True
            else:
                self.target_enemy = None
        
        # Update animation
        if self.is_animated and self.animation_list:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_delay:
                self.animation_timer = 0.0
                if self.is_shooting:
                    self.frame_index = (self.frame_index + 1) % len(self.animation_list)
                else:
                    self.frame_index = 0
    
    def fire(self, target_pos):
        """Fire a projectile at target"""
        if not self.projectile_group:
            return
        
        # Create projectile
        projectile = Projectile(
            start_pos=self.pos,
            target_pos=target_pos,
            speed=self.effective_projectile_speed,
            damage=self.effective_damage,
            target_type="enemy"
        )
        
        self.projectile_group.add(projectile)
    
    def draw(self, surface):
        """Draw turret"""
        if self.state == BuildState.CONSTRUCTING:
            # Draw construction state
            alpha = int(128 + 127 * (self.progress / self.BUILD_TIME))
            if self.base_image:
                temp_image = self.base_image.copy()
                temp_image.set_alpha(alpha)
                surface.blit(temp_image, self.rect)
            return
        
        if self.state != BuildState.ACTIVE:
            return
        
        # Draw base
        if self.base_image:
            surface.blit(self.base_image, self.rect)
        
        # Draw turret (rotated)
        if self.is_animated and self.animation_list:
            turret_frame = self.animation_list[self.frame_index]
        elif self.sprite_sheet:
            turret_frame = self.sprite_sheet
        else:
            return
        
        # Rotate turret to face target angle
        rotated_turret = pygame.transform.rotate(turret_frame, -self.angle)
        turret_rect = rotated_turret.get_rect(center=self.rect.center)
        surface.blit(rotated_turret, turret_rect)
        
        # Draw selection highlight
        if self.selected:
            pygame.draw.rect(surface, (255, 255, 0), self.rect, 2)

