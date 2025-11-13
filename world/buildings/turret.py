"""Ballistic Turret building."""
import pygame
import math
import constants as c
from world.building import Building, Cost, BuildState
from world.projectile import Projectile

class BallisticTurret(Building):
    """Ballistic turret that inherits from Building but keeps firing logic."""
    TYPE_ID = "turret_ballistic"
    BASE_HP = 220
    BUILD_TIME = 2.5
    COST = Cost(wood=40, iron=30)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    
    def __init__(self, grid_pos, sprite_sheets, base_images, tier=1, uid=None):
        # Initialize building first
        super().__init__(grid_pos, tier=tier, uid=uid)
        
        # Turret-specific attributes
        # ===== COOLDOWN ADJUSTMENT =====
        # Animation length is derived from the frame count and ANIMATION_DELAY.
        # Adjust timing by tweaking ANIMATION_DELAY (animation speed) or shot_delay (pause between shots).
        self.shot_delay = 500  # milliseconds - delay after animation before next shot (0.5 seconds)
        self.cooldown = 0  # placeholder until animation frames are loaded
        self.range = 200  # pixels - increased for better gameplay
        self.damage = 10  # damage per shot
        self.projectile_speed = 400.0  # pixels per second
        self.angle = 0  # Current rotation angle in degrees
        self.target_angle = 0  # Target angle to rotate toward
        self.rotation_speed = 180  # degrees per second - how fast turret rotates
        self.base_images = self._normalize_base_images(base_images)
        self.base_image = self._get_base_image_for_tier(self.tier)
        self.sprite_sheets = self._normalize_sprite_sheets(sprite_sheets)
        self.sprite_sheet = self._get_sprite_sheet_for_tier(self.tier)
        self.selected = False
        
        # Animation state
        self.animation_list = self.load_image()
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.last_shot = pygame.time.get_ticks()
        self.is_shooting = False  # Only True when actively shooting
        self.animation_playing = False  # Track if animation is playing
        
        # Store the current turret image
        self.turret_image = self.animation_list[self.frame_index]
        self.animation_duration = len(self.animation_list) * c.ANIMATION_DELAY
        self.cooldown = self.animation_duration + self.shot_delay  # milliseconds - animation + delay
        
        # Current target enemy
        self.target_enemy = None
        
        # Projectile group (will be set by world)
        self.projectile_group = None
        
        # Update rect to match base image size
        self._refresh_rect()
    
    def create_range_circle(self):
        """Create a semi-transparent circle to show turret range"""
        self.range_image = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.range_image, (100, 100, 100, 100), (self.range, self.range), self.range)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center
    
    def update_range_position(self):
        """Update range circle position to match turret position"""
        self.range_rect.center = self.rect.center
    
    def load_image(self):
        """Load animation frames from sprite sheet"""
        size = self.sprite_sheet.get_height()
        animation_list = []
        for x in range(c.ANIMATION_STEPS):
            temp_img = self.sprite_sheet.subsurface(x*size, 0, size, size)
            animation_list.append(temp_img)
        return animation_list
    
    def find_nearest_enemy(self, enemy_group):
        """Find the nearest enemy within range"""
        if not enemy_group:
            return None
        
        nearest_enemy = None
        nearest_distance = float('inf')
        
        for enemy in enemy_group:
            if not enemy.alive:
                continue
            
            # Calculate distance to enemy
            distance = math.sqrt(
                (enemy.pos.x - self.pos.x) ** 2 + 
                (enemy.pos.y - self.pos.y) ** 2
            )
            
            # Check if enemy is in range
            if distance <= self.range and distance < nearest_distance:
                nearest_distance = distance
                nearest_enemy = enemy
        
        return nearest_enemy
    
    def calculate_angle_to_target(self, target_pos):
        """Calculate angle to target position in degrees"""
        dx = target_pos.x - self.pos.x
        dy = target_pos.y - self.pos.y
        
        # Calculate angle in radians, then convert to degrees
        # atan2 returns angle from positive x-axis
        # atan2(dy, dx) gives: 0° = right, 90° = down, -90° = up, 180° = left
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # ===== ROTATION OFFSET ADJUSTMENT =====
        # If rotation is -90° off (pointing wrong direction):
        # - If sprite points up by default and should point right: add 90°
        # - If sprite points right by default and should point up: subtract 90°
        # 
        # Common sprite orientations:
        # - Sprite points right (east) by default: offset = 0
        # - Sprite points up (north) by default: offset = 90
        # - Sprite points down (south) by default: offset = -90
        # - Sprite points left (west) by default: offset = 180
        # 
        # Since rotation is -90° off, we need to add 90° to correct it
        rotation_offset = 90  # Adjust this value to fix rotation offset
        
        angle_deg += rotation_offset
        
        return angle_deg
    
    def rotate_toward_target(self, dt, target_angle):
        """Smoothly rotate turret toward target angle"""
        # Normalize angles to 0-360 range
        while self.angle < 0:
            self.angle += 360
        while self.angle >= 360:
            self.angle -= 360
        while target_angle < 0:
            target_angle += 360
        while target_angle >= 360:
            target_angle -= 360
        
        # Calculate shortest rotation path
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
        
        # Normalize angle again
        while self.angle < 0:
            self.angle += 360
        while self.angle >= 360:
            self.angle -= 360
    
    def is_aimed_at_target(self, target_angle, tolerance=5.0):
        """Check if turret is aimed at target (within tolerance)"""
        angle_diff = abs(self.angle - target_angle)
        # Handle wrap-around
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        return angle_diff <= tolerance
    
    def shoot(self, target_enemy):
        """Shoot at target enemy - spawns projectile"""
        if target_enemy and target_enemy.alive:
            # Start shooting animation
            current_time = pygame.time.get_ticks()
            self.is_shooting = True
            self.animation_playing = True
            self.frame_index = 0  # Start animation from first frame (idle -> shooting)
            self.update_time = current_time
            self.last_shot = current_time  # Reset cooldown timer
            
            # Spawn projectile at target (projectile will deal damage on hit)
            if self.projectile_group is not None:
                projectile = Projectile(
                    start_pos=(self.pos.x, self.pos.y),
                    target_pos=(target_enemy.pos.x, target_enemy.pos.y),
                    speed=self.projectile_speed,
                    damage=self.damage,
                    target_type="enemy"  # Target enemies
                )
                self.projectile_group.add(projectile)
    
    def play_shooting_animation(self, dt):
        """Play shooting animation - only called when shooting"""
        if not self.is_shooting or not self.animation_playing:
            return
        
        current_time = pygame.time.get_ticks()
        
        if current_time - self.update_time >= c.ANIMATION_DELAY:
            self.update_time = current_time
            self.frame_index += 1
            
            # Animation completed all 8 frames (frame 7 was the last firing frame)
            if self.frame_index >= len(self.animation_list):
                # Animation cycle complete - stop animation and return to idle
                self.frame_index = 0  # Return to idle frame
                self.animation_playing = False
                # Note: is_shooting can stay True if target still exists
                # Next shot will be triggered when cooldown is ready
        
        # Update the stored turret image (clamp frame index to valid range)
        self.frame_index = min(self.frame_index, len(self.animation_list) - 1)
        self.turret_image = self.animation_list[self.frame_index]
    
    def get_rotated_turret(self):
        """Get the current turret frame rotated by self.angle"""
        current_frame = self.animation_list[self.frame_index]
        # ===== ROTATION DIRECTION NOTE =====
        # pygame.transform.rotate rotates COUNTERCLOCKWISE
        # Using -self.angle makes it rotate CLOCKWISE
        # If rotation direction is wrong, remove the negative sign
        rotated_image = pygame.transform.rotate(current_frame, -self.angle)
        return rotated_image
    
    def update(self, dt: float, world=None):
        """Update turret - building logic first, then turret-specific logic"""
        # Call parent update for construction/production
        super().update(dt, world)
        
        # Only update turret-specific logic when active
        if self.state == BuildState.ACTIVE:
            # Get enemy group and projectile group from world
            enemy_group = None
            if world and hasattr(world, 'enemy_group'):
                enemy_group = world.enemy_group
            if world and hasattr(world, 'projectile_group'):
                self.projectile_group = world.projectile_group
            
            if enemy_group:
                # Find nearest enemy
                nearest_enemy = self.find_nearest_enemy(enemy_group)
                
                if nearest_enemy and nearest_enemy.alive:
                    # Calculate angle to target
                    target_angle = self.calculate_angle_to_target(nearest_enemy.pos)
                    self.target_angle = target_angle
                    self.target_enemy = nearest_enemy
                    
                    # Rotate toward target
                    self.rotate_toward_target(dt, target_angle)
                    
                    # Check if we can shoot (cooldown ready, aimed, and animation finished)
                    current_time = pygame.time.get_ticks()
                    time_since_last_shot = current_time - self.last_shot
                    can_shoot = time_since_last_shot >= self.cooldown
                    is_aimed = self.is_aimed_at_target(target_angle, tolerance=10.0)
                    
                    # Shooting logic:
                    # 1. Only shoot if cooldown is ready, aimed, and animation is not playing
                    # 2. This ensures previous animation completes before next shot
                    # 3. Animation plays during shooting, then stops when complete
                    if can_shoot and is_aimed and not self.animation_playing:
                        # Shoot at enemy (starts animation and resets cooldown)
                        self.shoot(nearest_enemy)
                    elif not self.animation_playing and time_since_last_shot >= self.cooldown:
                        # Animation finished and cooldown ready - ready for next shot
                        # Keep is_shooting True if we have a target (allows continuous shooting)
                        # If no target or not aimed, it will be reset below
                        pass
                else:
                    # No target found
                    self.target_enemy = None
                    # If animation is not playing, reset to idle
                    if not self.animation_playing:
                        self.is_shooting = False
                        # Reset to first frame (idle frame) when not shooting
                        self.frame_index = 0
                        self.turret_image = self.animation_list[self.frame_index]
            
            # Play shooting animation ONLY when actively shooting
            # Animation plays through all 8 frames, then stops
            if self.is_shooting and self.animation_playing:
                self.play_shooting_animation(dt)
            else:
                # Not shooting - ensure we're on idle frame (frame 0)
                if not self.is_shooting:
                    self.frame_index = 0
                    self.turret_image = self.animation_list[self.frame_index]
    
    def draw(self, surface: pygame.Surface):
        """Draw the turret - base first, then head when active"""
        # Update range circle position
        self.update_range_position()
        
        # Draw range circle first (if selected) - behind everything
        if self.selected and self.state == BuildState.ACTIVE:
            surface.blit(self.range_image, self.range_rect)
        
        # Draw base image FIRST (always visible, even during construction)
        base_rect = self.base_image.get_rect()
        base_rect.center = self.rect.center
        surface.blit(self.base_image, base_rect)
        
        # Draw construction progress overlay on top of base (if constructing)
        if self.state == BuildState.CONSTRUCTING:
            w, h = self.FOOTPRINT
            overlay = pygame.Surface((w*32, h*32), pygame.SRCALPHA)
            overlay.fill((100, 100, 100, 100))  # Semi-transparent grey
            # Build progress bar
            pct = self.progress / self.BUILD_TIME if self.BUILD_TIME > 0 else 1.0
            pygame.draw.rect(overlay, (200, 220, 80), (2, h*32-6, int((w*32-4)*pct), 4))
            overlay_rect = overlay.get_rect(center=self.rect.center)
            surface.blit(overlay, overlay_rect)
        
        # Draw rotated turret head LAST (only when active)
        if self.state == BuildState.ACTIVE:
            rotated_turret = self.get_rotated_turret()
            turret_rect = rotated_turret.get_rect()
            turret_rect.center = self.rect.center
            surface.blit(rotated_turret, turret_rect)
            
            # Debug: Draw line to target (optional, can be removed)
            # if self.target_enemy and self.target_enemy.alive:
            #     pygame.draw.line(surface, (255, 0, 0), self.pos, self.target_enemy.pos, 2)
    
    @staticmethod
    def create_turret(grid_pos, sprite_sheets, base_images, turret_group, tier=1):
        """Create a new turret at the given grid position"""
        turret = BallisticTurret(grid_pos, sprite_sheets, base_images, tier=tier)
        turret_group.add(turret)
        return turret

    @staticmethod
    def _placeholder_base():
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        surface.fill((110, 110, 110))
        return surface

    def _normalize_base_images(self, base_images):
        """Ensure we have a list of base images for each tier."""
        placeholder = self._placeholder_base()

        if isinstance(base_images, pygame.Surface):
            bases = [base_images]
        elif isinstance(base_images, dict):
            bases = []
            for tier in range(1, self.TIER_MAX + 1):
                candidate = base_images.get(tier) or base_images.get(str(tier)) or base_images.get(f"tier_{tier}")
                bases.append(candidate if isinstance(candidate, pygame.Surface) else placeholder)
        elif isinstance(base_images, (list, tuple)):
            bases = [img if isinstance(img, pygame.Surface) else placeholder for img in base_images]
        else:
            bases = []
            if base_images:
                bases.append(base_images if isinstance(base_images, pygame.Surface) else placeholder)

        if not bases:
            bases = [placeholder]

        while len(bases) < self.TIER_MAX:
            bases.append(bases[-1])

        return bases

    def _normalize_sprite_sheets(self, sprite_sheets):
        """Ensure we have a list of sprite sheets per tier."""
        placeholder = self._placeholder_sprite_sheet()

        if isinstance(sprite_sheets, pygame.Surface):
            sheets = [sprite_sheets]
        elif isinstance(sprite_sheets, dict):
            sheets = []
            for tier in range(1, self.TIER_MAX + 1):
                candidate = (sprite_sheets.get(tier) or sprite_sheets.get(str(tier))
                             or sprite_sheets.get(f"tier_{tier}"))
                sheets.append(candidate if isinstance(candidate, pygame.Surface) else placeholder)
        elif isinstance(sprite_sheets, (list, tuple)):
            sheets = [sheet if isinstance(sheet, pygame.Surface) else placeholder for sheet in sprite_sheets]
        else:
            sheets = []
            if isinstance(sprite_sheets, pygame.Surface):
                sheets.append(sprite_sheets)

        if not sheets:
            sheets = [placeholder]

        while len(sheets) < self.TIER_MAX:
            sheets.append(sheets[-1])

        return sheets

    @staticmethod
    def _placeholder_sprite_sheet():
        """Create a placeholder animation sheet with 4 frames."""
        width = 32 * max(1, c.ANIMATION_STEPS)
        surface = pygame.Surface((width, 32), pygame.SRCALPHA)
        for i in range(c.ANIMATION_STEPS):
            frame_rect = pygame.Rect(i * 32, 0, 32, 32)
            color = (140, 140, 140, 255) if i % 2 == 0 else (90, 90, 90, 255)
            surface.fill(color, frame_rect)
        return surface

    def _get_base_image_for_tier(self, tier: int):
        index = max(0, min(tier - 1, len(self.base_images) - 1))
        return self.base_images[index]

    def _get_sprite_sheet_for_tier(self, tier: int):
        index = max(0, min(tier - 1, len(self.sprite_sheets) - 1))
        return self.sprite_sheets[index]

    def _refresh_rect(self):
        """Recalculate rect dimensions based on current base/turret images."""
        base_rect = self.base_image.get_rect()
        turret_rect = self.turret_image.get_rect()
        center = self.rect.center if hasattr(self, "rect") else self.pos
        self.rect = pygame.Rect(0, 0, max(base_rect.width, turret_rect.width),
                                max(base_rect.height, turret_rect.height))
        self.rect.center = center
        self.create_range_circle()

    def on_upgrade(self):
        """Handle tier upgrades - swap base texture when available."""
        super().on_upgrade()
        self.base_image = self._get_base_image_for_tier(self.tier)
        self.sprite_sheet = self._get_sprite_sheet_for_tier(self.tier)
        self.animation_list = self.load_image()
        self.frame_index = 0
        self.turret_image = self.animation_list[self.frame_index]
        self.animation_duration = len(self.animation_list) * c.ANIMATION_DELAY
        self.cooldown = self.animation_duration + self.shot_delay
        self._refresh_rect()
