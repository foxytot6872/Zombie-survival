"""
Flamethrower turret - short range, area damage, continuous fire.
"""
import pygame
import math
import constants as c
from world.building import Building, Cost, BuildState
from world.projectile import FlameBullet

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
        self.animation_state = "idle"  # "idle", "windup", "firing"
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.08  # seconds per frame
        self.animation_list = []  # All frames from sprite sheet
        self.windup_frames = []  # Frames 1-6 (indices 0-5)
        self.firing_frames = []  # Frames 7-8 (indices 6-7)
        self.current_frames = []  # Points to current frame set (windup or firing)
        self.is_animated = False
        self.windup_complete = False
        
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
        
        # Range circle for selection display
        self.create_range_circle()
        
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
        
        # Set up windup/firing frames from animation_list (slices, not copies)
        if len(self.animation_list) >= 8:
            self.windup_frames = self.animation_list[0:6]  # Frames 1-6 (indices 0-5)
            self.firing_frames = self.animation_list[6:8]   # Frames 7-8 (indices 6-7)
        elif len(self.animation_list) >= 6:
            self.windup_frames = self.animation_list[0:6]
            self.firing_frames = self.animation_list[5:] if len(self.animation_list) > 6 else [self.animation_list[-1]]
        else:
            # Fallback: use all frames for both
            self.windup_frames = self.animation_list
            self.firing_frames = self.animation_list
        
        if self.animation_list:
            self.is_animated = True
            # Initialize to idle state
            self.current_frames = [self.animation_list[0]] if self.animation_list else []
            self.frame_index = 0
    
    def _refresh_rect(self):
        """Update rect to match base image size"""
        if self.base_image:
            self.rect = self.base_image.get_rect(center=self.pos)
        else:
            self.rect = pygame.Rect(0, 0, 32, 32)
            self.rect.center = self.pos
    
    def create_range_circle(self):
        """Create range circle for display when selected"""
        self.range_image = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.range_image, (255, 100, 0, 100), (self.range, self.range), self.range)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center
    
    def update_range_position(self):
        """Update range circle position"""
        self.range_rect.center = self.rect.center
    
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
    
    def update_animation(self, dt, is_firing):
        """Update animation based on firing state (similar to gatling turret)"""
        if not self.is_animated or not self.animation_list:
            return
        
        # Update animation timer
        self.animation_timer += dt
        
        # State transitions
        if is_firing:
            if self.animation_state == "idle":
                # Start windup
                self.animation_state = "windup"
                self.current_frames = self.windup_frames
                self.frame_index = 0
                self.animation_timer = 0.0
                self.windup_complete = False
            elif self.animation_state == "windup":
                # Check if windup complete
                if self.frame_index >= len(self.windup_frames) - 1:
                    # Transition to firing
                    self.animation_state = "firing"
                    self.current_frames = self.firing_frames
                    self.frame_index = 0
                    self.animation_timer = 0.0
                    self.windup_complete = True
            elif self.animation_state == "firing":
                # Continue firing - loop frames 7-8
                pass  # Keep firing
        else:
            # Not firing
            if self.animation_state == "firing":
                # Stop firing, go back to idle
                self.animation_state = "idle"
                self.current_frames = [self.animation_list[0]] if self.animation_list else []
                self.frame_index = 0
                self.animation_timer = 0.0
                self.windup_complete = False
            elif self.animation_state == "windup":
                # Interrupt windup - go to idle
                self.animation_state = "idle"
                self.current_frames = [self.animation_list[0]] if self.animation_list else []
                self.frame_index = 0
                self.animation_timer = 0.0
                self.windup_complete = False
            elif self.animation_state == "idle":
                # Stay idle - use first frame
                if not self.current_frames and self.animation_list:
                    self.current_frames = [self.animation_list[0]]
                    self.frame_index = 0
        
        # Update frame index
        if self.animation_timer >= self.animation_delay and self.current_frames:
            self.animation_timer = 0.0
            
            if self.animation_state == "firing":
                # Loop firing frames 7-8
                self.frame_index = (self.frame_index + 1) % len(self.current_frames)
            elif self.animation_state == "windup":
                # Play windup forward (1-6)
                if self.frame_index < len(self.current_frames) - 1:
                    self.frame_index += 1
                else:
                    # Already at end, will transition to firing
                    pass
        
        # Ensure frame_index is valid
        if self.current_frames and len(self.current_frames) > 0:
            if self.frame_index >= len(self.current_frames):
                self.frame_index = len(self.current_frames) - 1
        elif self.animation_list and len(self.animation_list) > 0:
            # Fallback to first frame if current_frames is empty
            self.current_frames = [self.animation_list[0]]
            self.frame_index = 0
    
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
        old_range = self.range
        if world and hasattr(world, 'modifiers'):
            range_mult = world.modifiers.get("turret_range_mult", 1.0)
            self.range = int(self.base_range * range_mult)
            damage_mult = world.modifiers.get("turret_damage_mult", 1.0)
            self.effective_damage = int(self.damage * damage_mult)
            fire_rate_mult = world.modifiers.get("turret_fire_rate_mult", 1.0)
            self.cooldown = int(self.base_cooldown / fire_rate_mult)
        
        # Recreate range circle if range changed
        if old_range != self.range:
            self.create_range_circle()
            self.update_range_position()
        
        if not enemy_group:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Check for targets periodically
        if current_time - (self.last_target_check * 1000) >= self.target_check_interval * 1000:
            self.target_enemy = self.find_nearest_enemy(enemy_group, spatial_grid)
            self.last_target_check = current_time / 1000.0
        
        # Rotate toward target
        if self.target_enemy and hasattr(self.target_enemy, 'pos'):
            target_angle = self.calculate_angle_to_target(self.target_enemy.pos)
            self.target_angle = target_angle
            self.rotate_toward_target(dt, target_angle)
        else:
            self.target_enemy = None
        
        # Fire at target
        is_firing = False
        if self.target_enemy and hasattr(self.target_enemy, 'pos'):
            distance = (self.pos - self.target_enemy.pos).length()
            if distance <= self.range:
                is_firing = True
                # Fire continuously while in firing state
                if self.animation_state == "firing" and current_time - self.last_shot >= self.cooldown:
                    self.fire(self.target_enemy.pos)
                    self.last_shot = current_time
                    self.is_shooting = True
            else:
                self.target_enemy = None
                self.is_shooting = False
        else:
            self.is_shooting = False
        
        # Update animation (similar to gatling turret)
        self.update_animation(dt, is_firing)
    
    def fire(self, target_pos):
        """Fire a flame projectile at target"""
        if not self.projectile_group:
            return
        
        # Create flame projectile
        projectile = FlameBullet(
            start_pos=self.pos,
            target_pos=target_pos,
            speed=self.effective_projectile_speed,
            damage=self.effective_damage,
            target_type="enemy"
        )
        
        # Set world reference for modifiers
        world_ref = getattr(self, 'world', None)
        if world_ref:
            projectile.world = world_ref
        
        self.projectile_group.add(projectile)
    
    def get_rotated_turret(self):
        """Get rotated turret image"""
        current_frame = None
        
        # Use current_frames if available (like gatling turret)
        if self.current_frames and len(self.current_frames) > 0:
            if 0 <= self.frame_index < len(self.current_frames):
                current_frame = self.current_frames[self.frame_index]
            else:
                current_frame = self.current_frames[0] if self.current_frames else None
        elif self.is_animated and self.animation_list:
            # Fallback to animation_list
            if 0 <= self.frame_index < len(self.animation_list):
                current_frame = self.animation_list[self.frame_index]
            else:
                current_frame = self.animation_list[0] if self.animation_list else None
        elif self.sprite_sheet:
            current_frame = self.sprite_sheet
        
        if current_frame is None:
            return None
        
        rotated_image = pygame.transform.rotate(current_frame, -self.angle)
        return rotated_image
    
    def on_upgrade(self):
        """Handle tier upgrades - swap base texture and sprite sheet when available"""
        super().on_upgrade()
        
        # Update base image and sprite sheet for new tier
        if hasattr(self, 'base_images') and self.base_images:
            self.base_image = self._get_base_image_for_tier(self.tier)
        
        if hasattr(self, 'sprite_sheets') and self.sprite_sheets:
            self.sprite_sheet = self._get_sprite_sheet_for_tier(self.tier)
            # Reload animation frames from new sprite sheet
            if self.sprite_sheet:
                self._load_animation_frames()
        
        # Update rect
        self._refresh_rect()
        
        # Recreate range circle (range might change with tier)
        self.create_range_circle()
        self.update_range_position()
    
    def draw(self, surface):
        """Draw turret"""
        # Draw range circle if selected (behind base)
        if self.selected and self.state == BuildState.ACTIVE:
            self.update_range_position()
            surface.blit(self.range_image, self.range_rect)
        
        if self.state == BuildState.CONSTRUCTING:
            # Draw construction overlay
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
            
            # Draw base with alpha
            alpha = int(128 + 127 * pct)
            if self.base_image:
                temp_image = self.base_image.copy()
                temp_image.set_alpha(alpha)
                surface.blit(temp_image, self.rect)
            return
        
        if self.state != BuildState.ACTIVE:
            return
        
        # Draw base
        if self.base_image:
            base_rect = self.base_image.get_rect(center=self.pos)
            surface.blit(self.base_image, base_rect)
        
        # Draw turret (rotated)
        rotated_turret = self.get_rotated_turret()
        if rotated_turret:
            turret_rect = rotated_turret.get_rect(center=self.rect.center)
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
        
        # Draw selection highlight
        if self.selected:
            pygame.draw.rect(surface, (255, 255, 0), self.rect, 2)

