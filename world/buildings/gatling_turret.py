"""
Gatling turret - high rate of fire, low damage, short range.
"""
import pygame
import math
import constants as c
from world.building import Building, Cost, BuildState
from world.projectile import GatlingBullet

class GatlingTurret(Building):
    """Gatling turret - high ROF, low damage, short range"""
    TYPE_ID = "turret_gatling"
    BASE_HP = 150
    BUILD_TIME = 2.0
    COST = Cost(wood=30, iron=20)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    ALLOW_MAX_TIER_PROGRESS = True
    
    def __init__(self, grid_pos, sprite_sheets=None, base_images=None, tier=1, uid=None, turret_sheet=None, turret_image=None, base_image=None):
        """
        Initialize Gatling turret.
        
        Accepts either:
        - sprite_sheets (list) and base_images (list) for multi-tier support (new way)
        - turret_sheet and base_image for single tier (old way, for backward compatibility)
        - turret_image and base_image for old static turret (deprecated)
        """
        super().__init__(grid_pos, tier=tier, uid=uid)
        
        # Gatling-specific attributes
        self.base_cooldown = 300  # milliseconds - very fast firing
        self.cooldown = self.base_cooldown  # Will be modified by day events
        self.base_range = 150  # pixels - shorter range
        self.range = self.base_range  # Will be modified by day events
        self.damage = 5  # damage per shot - low damage
        self.effective_damage = self.damage  # Will be modified by research/day events
        self.projectile_speed = 500.0  # pixels per second - fast projectiles
        self.noise_value = 3  # Noise value for spawn attraction (Gatling = 3)
        self.effective_projectile_speed = self.projectile_speed  # Will be modified by research/day events
        self.angle = 0
        self.target_angle = 0
        self.rotation_speed = 240  # degrees per second - fast rotation
        self.selected = False
        
        # Handle multi-tier support (new way) or single tier (old way)
        if sprite_sheets is not None and base_images is not None:
            # New way: lists of sprite sheets and base images for multiple tiers
            self.sprite_sheets = self._normalize_sprite_sheets(sprite_sheets)
            self.base_images = self._normalize_base_images(base_images)
            # Load base animation for tier 3 (if it's a sprite sheet)
            self._load_base_animation_for_tier(self.tier)
            self.base_image = self._get_base_image_for_tier(self.tier)
            # Set current sprite sheet for this tier (like other turrets do)
            # IMPORTANT: Always get the sprite sheet for the current tier
            self.sprite_sheet = self._get_sprite_sheet_for_tier(self.tier)
            turret_sheet = self.sprite_sheet
        elif base_image is not None:
            # Old way: single base image
            self.base_images = [base_image]
            self.base_image = base_image
        else:
            # Create placeholder
            placeholder_base = pygame.Surface((32, 32))
            placeholder_base.fill((120, 100, 80))
            self.base_images = [placeholder_base]
            self.base_image = placeholder_base
        
        # Turret animation state
        self.animation_state = "idle"  # "idle", "windup", "firing", "winddown"
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.1  # seconds per frame
        self.animation_list = []  # All frames from sprite sheet (like other turrets)
        self.windup_frames = []  # frames 1-4 (0-3)
        self.firing_frames = []  # frames 5-9 (4-8)
        self.winddown_frames = []  # frames 4-1 reverse (3-0)
        self.animation_frames = []  # Alias for animation_list
        self.is_animated = False
        
        # Base animation state (for lv3)
        self.base_animation_frames = []  # 4 frames for lv3 base
        self.base_frame_index = 0
        self.base_animation_timer = 0.0
        self.base_animation_delay = 0.1  # seconds per frame
        self.base_is_animated = False
        
        # Load animation frames from sprite sheet (same logic as other turrets)
        # Make sure we use the correct tier's sprite sheet
        if hasattr(self, 'sprite_sheets') and self.sprite_sheets:
            # Always ensure sprite_sheet is set to the correct tier before loading
            self.sprite_sheet = self._get_sprite_sheet_for_tier(self.tier)
            if self.sprite_sheet is not None:
                self.animation_list = self.load_image()
                # Set up windup/firing/winddown frames from animation_list
                if len(self.animation_list) >= 9:
                    self.animation_frames = self.animation_list
                    self.windup_frames = self.animation_list[0:4]
                    self.firing_frames = self.animation_list[4:9]
                    self.winddown_frames = self.animation_list[3::-1]
                    self.is_animated = True
                    # Initialize animation state to idle with first frame (same as tier 1)
                    self.animation_state = "idle"
                    self.frame_index = 0
                    self.animation_timer = 0.0
                    self.turret_image = self.animation_list[0] if self.animation_list else None
                    self.current_frames = [self.animation_list[0]] if self.animation_list else []
                    print(f"Gatling turret (tier {self.tier}) loaded {len(self.animation_list)} animation frames with windup/winddown")
                else:
                    print(f"Warning: Gatling turret (tier {self.tier}) expected 9 frames but got {len(self.animation_list)}")
            else:
                print(f"Warning: Gatling turret (tier {self.tier}) sprite_sheet is None")
        elif hasattr(self, 'sprite_sheet') and self.sprite_sheet is not None:
            # Fallback: if sprite_sheet is set directly (old way)
            self.animation_list = self.load_image()
            # Set up windup/firing/winddown frames from animation_list
            if len(self.animation_list) >= 9:
                self.animation_frames = self.animation_list
                self.windup_frames = self.animation_list[0:4]
                self.firing_frames = self.animation_list[4:9]
                self.winddown_frames = self.animation_list[3::-1]
                self.is_animated = True
                # Initialize animation state to idle with first frame (same as tier 1)
                self.animation_state = "idle"
                self.frame_index = 0
                self.animation_timer = 0.0
                self.turret_image = self.animation_list[0] if self.animation_list else None
                self.current_frames = [self.animation_list[0]] if self.animation_list else []
        elif turret_sheet is not None:
            # Old way: load from turret_sheet parameter
            sheet_width = turret_sheet.get_width()
            sheet_height = turret_sheet.get_height()
            print(f"Loading Gatling turret sprite sheet (tier {tier}): {sheet_width}x{sheet_height}")
            if self._reload_animation_from_sheet(turret_sheet):
                print(f"  Loaded {len(self.animation_frames)} frames: windup={len(self.windup_frames)}, firing={len(self.firing_frames)}, winddown={len(self.winddown_frames)}")
                if self.turret_image:
                    print(f"  Initial turret image size: {self.turret_image.get_size()}")
            else:
                print(f"  Warning: Failed to load animation from sprite sheet")
        else:
            # Static image (old Gatling turret) - scale it up
            if turret_image:
                original_image = turret_image
                # Scale up by 1.5x for bigger appearance
                scale_factor = 1.5
                original_width, original_height = original_image.get_size()
                scaled_width = int(original_width * scale_factor)
                scaled_height = int(original_height * scale_factor)
                self.turret_image = pygame.transform.scale(original_image, (scaled_width, scaled_height))
            else:
                # Fallback placeholder
                self.turret_image = pygame.Surface((32, 32), pygame.SRCALPHA)
                self.turret_image.fill((180, 160, 140))
        
        # Vertical offset to center turret on base
        # No offset - sprite is centered correctly
        self.turret_offset_y = 0
        
        base_rect = self.base_image.get_rect()
        if self.turret_image:
            turret_rect = self.turret_image.get_rect()
            self.rect = pygame.Rect(0, 0, max(base_rect.width, turret_rect.width),
                                    max(base_rect.height, turret_rect.height))
        else:
            # Fallback if turret_image is None (shouldn't happen, but safe)
            self.rect = base_rect.copy()
        self.rect.center = self.pos
        
        self.create_range_circle()
        self.projectile_group = None
        self.target_enemy = None
        self.last_shot = pygame.time.get_ticks()
        
        # Target check cooldown - only retarget every 0.25 seconds
        self.last_target_check = 0.0
        self.target_check_interval = 0.25  # seconds
    
    def create_range_circle(self):
        """Create range circle"""
        self.range_image = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.range_image, (100, 150, 100, 100), (self.range, self.range), self.range)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center
    
    
    def find_nearest_enemy(self, enemy_group, spatial_grid=None):
        """
        Find nearest enemy within range.
        Uses spatial grid for efficient querying if provided.
        """
        if not enemy_group:
            return None
        
        nearest_enemy = None
        nearest_distance = float('inf')
        
        # Use spatial grid if available (much faster than scanning all enemies)
        candidates = []
        if spatial_grid:
            # Get enemies from nearby cells (radius_cells=2 covers ~256 pixels)
            candidates = spatial_grid.get_nearby(self.pos, radius_cells=2)
        else:
            # Fallback: scan all enemies
            candidates = list(enemy_group)
        
        for enemy in candidates:
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
                # Use effective damage and speed (modified by research/day events)
                effective_damage = getattr(self, 'effective_damage', self.damage)
                effective_speed = getattr(self, 'effective_projectile_speed', self.projectile_speed)
                projectile = GatlingBullet(
                    start_pos=(turret_visual_pos.x, turret_visual_pos.y),
                    target_pos=(target_enemy.pos.x, target_enemy.pos.y),
                    speed=effective_speed,
                    damage=effective_damage,
                    target_type="enemy"  # Target enemies
                )
                # Set world reference for modifiers (armor pierce, etc.)
                world_ref = getattr(self, 'world', None)
                if world_ref:
                    projectile.world = world_ref
                self.projectile_group.add(projectile)
    
    def update_animation(self, dt: float, is_firing: bool):
        """Update animation based on firing state"""
        if not self.is_animated or not self.animation_frames:
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
            elif self.animation_state == "windup":
                # Check if windup complete
                if self.frame_index >= len(self.windup_frames) - 1:
                    # Transition to firing
                    self.animation_state = "firing"
                    self.current_frames = self.firing_frames
                    self.frame_index = 0
                    self.animation_timer = 0.0
            elif self.animation_state == "firing":
                # Continue firing - loop frames 5-9
                pass  # Keep firing
            elif self.animation_state == "winddown":
                # Interrupt winddown to start firing again
                self.animation_state = "windup"
                self.current_frames = self.windup_frames
                self.frame_index = 0
                self.animation_timer = 0.0
        else:
            # Not firing
            if self.animation_state == "firing":
                # Start winddown
                self.animation_state = "winddown"
                self.current_frames = self.winddown_frames
                self.frame_index = 0
                self.animation_timer = 0.0
            elif self.animation_state == "winddown":
                # Check if winddown complete
                if self.frame_index >= len(self.winddown_frames) - 1:
                    # Transition to idle
                    self.animation_state = "idle"
                    self.current_frames = [self.animation_frames[0]] if self.animation_frames else []
                    self.frame_index = 0
                    self.animation_timer = 0.0
            elif self.animation_state == "windup":
                # Interrupt windup - go to winddown
                self.animation_state = "winddown"
                self.current_frames = self.winddown_frames
                # Calculate reverse index: if we were at frame 2 of windup (index 1), go to frame 2 of winddown (index 1)
                self.frame_index = min(self.frame_index, len(self.winddown_frames) - 1)
                self.animation_timer = 0.0
            elif self.animation_state == "idle":
                # Stay idle - use first frame
                if not self.current_frames and self.animation_frames:
                    self.current_frames = [self.animation_frames[0]]
                    self.frame_index = 0
        
        # Update frame index
        if self.animation_timer >= self.animation_delay and self.current_frames:
            self.animation_timer = 0.0
            
            if self.animation_state == "firing":
                # Loop firing frames 5-9
                self.frame_index = (self.frame_index + 1) % len(self.current_frames)
            elif self.animation_state == "windup":
                # Play windup forward (1-4)
                if self.frame_index < len(self.current_frames) - 1:
                    self.frame_index += 1
                else:
                    # Already at end, will transition to firing
                    pass
            elif self.animation_state == "winddown":
                # Play winddown (4-1 reverse)
                if self.frame_index < len(self.current_frames) - 1:
                    self.frame_index += 1
                else:
                    # Already at end, will transition to idle
                    pass
        
        # Update current turret image - always ensure it's set
        if self.current_frames and len(self.current_frames) > 0:
            # Ensure frame_index is valid
            if self.frame_index >= len(self.current_frames):
                self.frame_index = len(self.current_frames) - 1
            if self.frame_index < len(self.current_frames):
                self.turret_image = self.current_frames[self.frame_index]
        elif self.animation_frames and len(self.animation_frames) > 0:
            # Fallback to first frame if current_frames is empty
            self.turret_image = self.animation_frames[0]
            if not self.current_frames:
                self.current_frames = [self.animation_frames[0]]
                self.frame_index = 0
    
    def get_rotated_turret(self):
        """Get rotated turret image"""
        if self.turret_image is None:
            return None
        rotated_image = pygame.transform.rotate(self.turret_image, -self.angle)
        return rotated_image
    
    def update(self, dt: float, world=None):
        """Update turret"""
        # Apply turret modifiers from research and day events
        if world and hasattr(world, 'modifiers'):
            fire_rate_mult = world.modifiers.get("turret_fire_rate_mult", 1.0)
            self.cooldown = int(self.base_cooldown * fire_rate_mult)
            
            # Apply turret range modifier
            range_mult = world.modifiers.get("turret_range_mult", 1.0)
            new_range = int(self.base_range * range_mult)
            if new_range != self.range:
                self.range = new_range
                # Recreate range circle if range changed
                self.range_image = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
                pygame.draw.circle(self.range_image, (100, 100, 100, 100), (self.range, self.range), self.range)
                self.range_rect = self.range_image.get_rect()
                self.update_range_position()  # Update position to match turret
            
            # Apply turret damage modifier (calculate effective damage)
            damage_mult = world.modifiers.get("turret_damage_mult", 1.0)
            self.effective_damage = int(5 * damage_mult)  # Base damage is 5
            
            # Apply turret projectile speed modifier
            projectile_speed_mult = world.modifiers.get("turret_projectile_speed_mult", 1.0)
            self.effective_projectile_speed = self.projectile_speed * projectile_speed_mult
        else:
            self.cooldown = self.base_cooldown
            self.range = self.base_range
            self.effective_damage = self.damage
            self.effective_projectile_speed = self.projectile_speed
        
        super().update(dt, world)
        
        if self.state == BuildState.ACTIVE:
            enemy_group = None
            if world and hasattr(world, 'enemy_group'):
                enemy_group = world.enemy_group
            if world and hasattr(world, 'projectile_group'):
                self.projectile_group = world.projectile_group
            
            is_firing = False
            
            if enemy_group:
                # Only retarget if cooldown has passed
                import time
                current_time = time.time()
                should_retarget = (current_time - self.last_target_check) >= self.target_check_interval
                
                # Get spatial grid from world if available
                spatial_grid = None
                if world and hasattr(world, 'spatial_grid'):
                    spatial_grid = world.spatial_grid
                
                if should_retarget:
                    # Find nearest enemy (using spatial grid if available)
                    nearest_enemy = self.find_nearest_enemy(enemy_group, spatial_grid)
                    self.last_target_check = current_time
                    
                    # Update target if found
                    if nearest_enemy and nearest_enemy.alive:
                        self.target_enemy = nearest_enemy
                else:
                    # Use existing target if still alive and in range
                    nearest_enemy = self.target_enemy
                    if nearest_enemy and nearest_enemy.alive:
                        # Check if target is still in range
                        distance = math.sqrt(
                            (nearest_enemy.pos.x - self.pos.x) ** 2 +
                            (nearest_enemy.pos.y - self.pos.y) ** 2
                        )
                        if distance > self.range:
                            # Target out of range - clear it
                            nearest_enemy = None
                            self.target_enemy = None
                
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
                        is_firing = True
                    elif is_aimed and not can_shoot:
                        # Aimed but on cooldown - still "firing" visually
                        is_firing = True
                else:
                    self.target_enemy = None
            
            # Update turret animation
            self.update_animation(dt, is_firing)
            
            # Update base animation (lv3 only, plays while shooting)
            self.update_base_animation(dt, is_firing)
    
    def draw(self, surface: pygame.Surface):
        """Draw turret"""
        # Draw range circle if selected (behind base)
        if self.selected and self.state == BuildState.ACTIVE:
            self.update_range_position()
            surface.blit(self.range_image, self.range_rect)
        
        # Draw base (animated if lv3)
        if self.base_is_animated and self.base_animation_frames and len(self.base_animation_frames) > 0:
            # Draw animated base (lv3)
            base_frame = self.base_animation_frames[self.base_frame_index]
            base_rect = base_frame.get_rect(center=self.pos)
            surface.blit(base_frame, base_rect)
        elif self.base_image:
            # Draw static base (lv1, lv2)
            base_rect = self.base_image.get_rect(center=self.pos)
            surface.blit(self.base_image, base_rect)
        else:
            # Draw placeholder if base image missing
            placeholder = pygame.Surface((32, 32))
            placeholder.fill((120, 100, 80))
            base_rect = placeholder.get_rect(center=self.pos)
            surface.blit(placeholder, base_rect)
        
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
            # Ensure turret_image is set if we have frames but image is None
            if self.turret_image is None and self.is_animated and self.animation_frames and len(self.animation_frames) > 0:
                # Initialize from first frame if missing
                first_frame = self.animation_frames[0]
                self.turret_image = first_frame.copy().convert_alpha()
                self.current_frames = [first_frame]
                self.frame_index = 0
                print(f"Fixed: Initialized turret_image from animation_frames, size: {self.turret_image.get_size()}")
            
            if self.turret_image is not None:
                try:
                    rotated_turret = self.get_rotated_turret()
                    if rotated_turret:
                        img_size = rotated_turret.get_size()
                        if img_size[0] > 0 and img_size[1] > 0:
                            # Center the turret on the base position
                            # For animated turret, center directly on self.pos
                            turret_pos = pygame.Vector2(self.pos.x, self.pos.y + self.turret_offset_y)
                            turret_rect = rotated_turret.get_rect(center=turret_pos)
                            surface.blit(rotated_turret, turret_rect)
                        else:
                            # Invalid size, draw unrotated
                            turret_pos = pygame.Vector2(self.pos.x, self.pos.y + self.turret_offset_y)
                            turret_rect = self.turret_image.get_rect(center=turret_pos)
                            surface.blit(self.turret_image, turret_rect)
                    else:
                        # Fallback: draw unrotated image
                        turret_pos = pygame.Vector2(self.pos.x, self.pos.y + self.turret_offset_y)
                        turret_rect = self.turret_image.get_rect(center=turret_pos)
                        surface.blit(self.turret_image, turret_rect)
                except Exception as e:
                    print(f"Error drawing Gatling turret: {e}")
                    import traceback
                    traceback.print_exc()
                    # Draw debug rectangle
                    debug_rect = pygame.Rect(int(self.pos.x) - 16, int(self.pos.y) - 16, 32, 32)
                    pygame.draw.rect(surface, (255, 255, 0), debug_rect, 2)
            else:
                # Debug: draw placeholder if no image - this should not happen if frames loaded
                print(f"Warning: Gatling turret has no image! is_animated={self.is_animated}, frames={len(self.animation_frames)}, state={self.animation_state}")
                placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
                placeholder.fill((255, 0, 0, 128))  # Red placeholder
                placeholder_rect = placeholder.get_rect(center=self.pos)
                surface.blit(placeholder, placeholder_rect)
            
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
    
    def _normalize_base_images(self, base_images):
        """Normalize base images to a list of at least TIER_MAX items."""
        if not base_images:
            placeholder = pygame.Surface((32, 32))
            placeholder.fill((120, 100, 80))
            base_images = [placeholder]
        
        if isinstance(base_images, pygame.Surface):
            base_images = [base_images]
        elif not isinstance(base_images, (list, tuple)):
            base_images = []
        
        if not base_images:
            placeholder = pygame.Surface((32, 32))
            placeholder.fill((120, 100, 80))
            base_images = [placeholder]
        
        # Extend to TIER_MAX if needed
        while len(base_images) < self.TIER_MAX:
            base_images.append(base_images[-1])
        
        return list(base_images)
    
    def _normalize_sprite_sheets(self, sprite_sheets):
        """Normalize sprite sheets to a list of at least TIER_MAX items."""
        placeholder = self._placeholder_sprite_sheet()
        
        if not sprite_sheets:
            sprite_sheets = [placeholder]
        
        if isinstance(sprite_sheets, pygame.Surface):
            sprite_sheets = [sprite_sheets]
        elif not isinstance(sprite_sheets, (list, tuple)):
            sprite_sheets = []
        
        if not sprite_sheets:
            sprite_sheets = [placeholder]
        
        # Extend to TIER_MAX if needed
        while len(sprite_sheets) < self.TIER_MAX:
            sprite_sheets.append(sprite_sheets[-1])
        
        return list(sprite_sheets)
    
    @staticmethod
    def _placeholder_sprite_sheet():
        """Create a placeholder animation sheet with 9 frames (96x96 each)."""
        frame_width = 96
        frame_height = 96
        width = frame_width * 9  # 9 frames
        surface = pygame.Surface((width, frame_height), pygame.SRCALPHA)
        for i in range(9):
            frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            color = (140, 140, 140, 255) if i % 2 == 0 else (90, 90, 90, 255)
            surface.fill(color, frame_rect)
        return surface
    
    def _get_base_image_for_tier(self, tier: int):
        """Get base image for the given tier."""
        index = max(0, min(tier - 1, len(self.base_images) - 1))
        return self.base_images[index]
    
    def _get_sprite_sheet_for_tier(self, tier: int):
        """Get sprite sheet for the given tier."""
        if not hasattr(self, 'sprite_sheets') or not self.sprite_sheets:
            return None
        index = max(0, min(tier - 1, len(self.sprite_sheets) - 1))
        sprite_sheet = self.sprite_sheets[index]
        if sprite_sheet is None:
            print(f"Warning: Gatling turret tier {tier} sprite sheet at index {index} is None (total sheets: {len(self.sprite_sheets)})")
        return sprite_sheet
    
    def load_image(self):
        """Load animation frames from sprite sheet (same pattern as other turrets, 96x96 per frame, 9 frames total)"""
        if not hasattr(self, 'sprite_sheet') or self.sprite_sheet is None:
            return []
        
        size = 96  # Gatling turret frame size is 96x96
        animation_list = []
        # Extract 9 frames (96x96 each)
        for x in range(9):
            x_pos = x * size
            if x_pos + size <= self.sprite_sheet.get_width():
                try:
                    temp_img = self.sprite_sheet.subsurface(x_pos, 0, size, size)
                    animation_list.append(temp_img)
                except Exception as e:
                    print(f"Error extracting frame {x+1}: {e}")
        return animation_list
    
    def _reload_animation_from_sheet(self, turret_sheet):
        """Reload animation frames from a sprite sheet (96x96 per frame, 9 frames total)."""
        if turret_sheet is None:
            return False
        
        self.is_animated = True
        self.animation_frames = []
        frame_width = 96
        frame_height = 96
        sheet_width = turret_sheet.get_width()
        sheet_height = turret_sheet.get_height()
        
        # Extract all 9 frames (96x96 each)
        for i in range(9):
            x_pos = i * frame_width
            if x_pos + frame_width <= sheet_width:
                try:
                    frame_rect = pygame.Rect(x_pos, 0, frame_width, frame_height)
                    frame = turret_sheet.subsurface(frame_rect).copy()
                    self.animation_frames.append(frame)
                except Exception as e:
                    print(f"  Error extracting frame {i+1}: {e}")
        
        # Set up animation frame groups (windup: 1-4, firing: 5-9, winddown: 4-1 reverse)
        if len(self.animation_frames) >= 9:
            # Clear old frame groups
            self.windup_frames = []
            self.firing_frames = []
            self.winddown_frames = []
            # Set up new frame groups from reloaded frames
            self.windup_frames = self.animation_frames[0:4]
            self.firing_frames = self.animation_frames[4:9]
            self.winddown_frames = self.animation_frames[3::-1]
            print(f"  Set up animation groups: windup={len(self.windup_frames)}, firing={len(self.firing_frames)}, winddown={len(self.winddown_frames)}")
        else:
            print(f"  Warning: Expected 9 frames but got {len(self.animation_frames)}")
        
        # Initialize turret_image from first frame
        if self.animation_frames:
            self.turret_image = self.animation_frames[0].copy().convert_alpha()
            self.current_frames = [self.animation_frames[0]]
            self.frame_index = 0
            self.animation_state = "idle"
            return True
        return False
    
    def _load_base_animation_for_tier(self, tier):
        """Load base animation frames if tier 3 (sprite sheet with 4 frames)."""
        if tier == 3 and hasattr(self, 'base_images') and len(self.base_images) >= 3:
            base_sheet = self.base_images[2]  # Index 2 = tier 3
            if base_sheet:
                sheet_width = base_sheet.get_width()
                sheet_height = base_sheet.get_height()
                
                # Check if it's a sprite sheet (should be 256x64 for 4 frames of 64x64)
                if sheet_width >= 256 and sheet_height == 64:
                    # Extract 4 frames (64x64 each)
                    frame_width = 64
                    frame_height = 64
                    self.base_animation_frames = []
                    
                    for i in range(4):
                        x_pos = i * frame_width
                        if x_pos + frame_width <= sheet_width:
                            try:
                                frame_rect = pygame.Rect(x_pos, 0, frame_width, frame_height)
                                frame = base_sheet.subsurface(frame_rect).copy()
                                self.base_animation_frames.append(frame)
                            except Exception as e:
                                print(f"Error extracting base frame {i+1}: {e}")
                    
                    if len(self.base_animation_frames) == 4:
                        self.base_is_animated = True
                        self.base_frame_index = 0
                        self.base_animation_timer = 0.0
                        # Use first frame as base_image
                        self.base_image = self.base_animation_frames[0]
                        print(f"Loaded base animation for tier 3: {len(self.base_animation_frames)} frames")
                    else:
                        print(f"Warning: Expected 4 base frames but got {len(self.base_animation_frames)}")
                        self.base_is_animated = False
                        self.base_image = base_sheet
                else:
                    # Not a sprite sheet, use as static image
                    self.base_is_animated = False
                    self.base_image = base_sheet
    
    def update_base_animation(self, dt: float, is_firing: bool):
        """Update base animation (lv3 only) - plays while shooting."""
        if not self.base_is_animated or not self.base_animation_frames:
            return
        
        # Only animate while shooting
        if is_firing:
            self.base_animation_timer += dt
            
            if self.base_animation_timer >= self.base_animation_delay:
                self.base_animation_timer = 0.0
                # Loop through frames 0-3
                self.base_frame_index = (self.base_frame_index + 1) % len(self.base_animation_frames)
        else:
            # Reset to first frame when not shooting
            if self.base_frame_index != 0:
                self.base_frame_index = 0
                self.base_animation_timer = 0.0
    
    def on_upgrade(self):
        """Handle tier upgrades - swap base texture and sprite sheet when available (same logic as other turrets)."""
        super().on_upgrade()
        
        print(f"Gatling turret upgrading to tier {self.tier}")
        
        # Update base image for new tier (reload animation if tier 3)
        if hasattr(self, 'base_images'):
            self._load_base_animation_for_tier(self.tier)
            self.base_image = self._get_base_image_for_tier(self.tier)
        
        # Update sprite sheet and reload animation for new tier (same logic as other turrets)
        if hasattr(self, 'sprite_sheets') and self.sprite_sheets:
            self.sprite_sheet = self._get_sprite_sheet_for_tier(self.tier)
            if self.sprite_sheet is None:
                print(f"Warning: Gatling turret tier {self.tier} sprite_sheet is None after upgrade")
            else:
                # Reload animation frames from new sprite sheet (same as other turrets)
                self.animation_list = self.load_image()
                # Set up windup/firing/winddown frames from animation_list (same as tier 1)
                if len(self.animation_list) >= 9:
                    self.animation_frames = self.animation_list
                    self.windup_frames = self.animation_list[0:4]
                    self.firing_frames = self.animation_list[4:9]
                    self.winddown_frames = self.animation_list[3::-1]
                    self.is_animated = True
                    # Reset animation state to idle with first frame (same as tier 1)
                    self.animation_state = "idle"
                    self.frame_index = 0
                    self.animation_timer = 0.0
                    self.turret_image = self.animation_list[0] if self.animation_list else None
                    self.current_frames = [self.animation_list[0]] if self.animation_list else []
                    print(f"Gatling turret upgraded to tier {self.tier}, loaded {len(self.animation_list)} animation frames with windup/winddown")
                else:
                    print(f"Warning: Gatling turret tier {self.tier} expected 9 frames but got {len(self.animation_list)}")
        else:
            print(f"Warning: Gatling turret tier {self.tier} has no sprite_sheets attribute or sprite_sheets is empty")

