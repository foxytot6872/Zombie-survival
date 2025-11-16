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
    ALLOW_MAX_TIER_PROGRESS = True
    
    def __init__(self, grid_pos, sprite_sheets, base_images, tier=1, uid=None, world=None):
        super().__init__(grid_pos, tier=tier, uid=uid, world=world)
        
        # Piercer-specific attributes
        self.base_cooldown = 2000  # milliseconds - slow firing
        self.cooldown = self.base_cooldown  # Will be modified by day events
        self.base_range = 250  # pixels - longer range
        self.range = self.base_range  # Will be modified by day events
        self.damage = 25  # damage per shot - high damage
        self.effective_damage = self.damage  # Will be modified by research/day events
        self.projectile_speed = 600.0  # pixels per second - very fast projectiles
        self.noise_value = 5  # Noise value for spawn attraction (Railgun = 5)
        self.effective_projectile_speed = self.projectile_speed  # Will be modified by research/day events
        self.pierce = True  # Pierces through enemies
        self.pierce_count = 3  # Number of enemies to pierce
        self.angle = 0
        self.target_angle = 0
        self.rotation_speed = 120  # degrees per second - slower rotation
        self.base_images = self._normalize_base_images(base_images)
        self.base_image = self._get_base_image_for_tier(self.tier)
        self.sprite_sheets = self._normalize_sprite_sheets(sprite_sheets)
        self.sprite_sheet = self._get_sprite_sheet_for_tier(self.tier)
        self.selected = False
        
        # Animation state
        self.animation_list = self.load_image()
        self.frame_index = 0
        self.animation_delay = 200  # milliseconds per frame - slower for railgun (was 150)
        self.update_time = pygame.time.get_ticks()
        self.last_shot = pygame.time.get_ticks()
        self.is_shooting = False
        self.animation_playing = False
        self.projectile_fired = False  # Track if projectile was fired this animation cycle
        self.target_enemy = None
        self.pending_target = None  # Target to fire at when animation reaches last frame
        
        self.turret_image = self.animation_list[self.frame_index]
        
        # Update rect to match base image size
        self._refresh_rect()
        
        self.create_range_circle()
        self.projectile_group = None
        self.enemy_group = None
        
        # Target check cooldown - only retarget every 0.25 seconds
        self.last_target_check = 0.0
        self.target_check_interval = 0.25  # seconds
    
    def create_range_circle(self):
        """Create range circle"""
        self.range_image = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.range_image, (150, 100, 100, 100), (self.range, self.range), self.range)
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center
    
    def load_image(self):
        """Load animation frames - railgun has 8 frames, 64x64 each"""
        frame_size = self.sprite_sheet.get_height()  # 64 for railgun
        sheet_width = self.sprite_sheet.get_width()
        num_frames = sheet_width // frame_size  # Calculate frames from sheet width (8 frames)
        animation_list = []
        for x in range(num_frames):
            temp_img = self.sprite_sheet.subsurface(x * frame_size, 0, frame_size, frame_size)
            animation_list.append(temp_img)
        return animation_list
    
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
        """Start shooting animation - projectile will fire on last frame"""
        if target_enemy and target_enemy.alive:
            current_time = pygame.time.get_ticks()
            self.is_shooting = True
            self.animation_playing = True
            self.frame_index = 0
            self.projectile_fired = False  # Reset flag for new animation cycle
            self.update_time = current_time
            self.last_shot = current_time
            # Store target for when we fire on last frame
            self.pending_target = target_enemy
    
    def play_shooting_animation(self, dt):
        """Play shooting animation - fire projectile on last frame"""
        if not self.is_shooting or not self.animation_playing:
            return
        
        current_time = pygame.time.get_ticks()
        if current_time - self.update_time >= self.animation_delay:
            self.update_time = current_time
            self.frame_index += 1
            
            # Fire projectile exactly when we reach the last frame
            if self.frame_index == len(self.animation_list) - 1 and not self.projectile_fired:
                # We just advanced to the last frame, fire the projectile
                if hasattr(self, 'pending_target') and self.pending_target and self.pending_target.alive:
                    if self.projectile_group is not None:
                        # Use effective damage and speed (modified by research/day events)
                        effective_damage = getattr(self, 'effective_damage', self.damage)
                        effective_speed = getattr(self, 'effective_projectile_speed', self.projectile_speed)
                        projectile = PiercingProjectile(
                            start_pos=(self.pos.x, self.pos.y),
                            target_pos=(self.pending_target.pos.x, self.pending_target.pos.y),
                            speed=effective_speed,
                            damage=effective_damage,
                            pierce_count=self.pierce_count,
                            enemy_group=self.enemy_group
                        )
                        # Set world reference for modifiers (armor pierce, etc.)
                        world_ref = getattr(self, 'world', None)
                        if world_ref:
                            projectile.world = world_ref
                        self.projectile_group.add(projectile)
                    self.projectile_fired = True
            
            # Animation completed - reset to first frame
            if self.frame_index >= len(self.animation_list):
                self.frame_index = 0
                self.animation_playing = False
                self.pending_target = None  # Clear pending target after animation completes
        
        self.frame_index = min(self.frame_index, len(self.animation_list) - 1)
        self.turret_image = self.animation_list[self.frame_index]
    
    def get_rotated_turret(self):
        """Get rotated turret image"""
        current_frame = self.animation_list[self.frame_index]
        rotated_image = pygame.transform.rotate(current_frame, -self.angle)
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
                pygame.draw.circle(self.range_image, (150, 100, 100, 100), (self.range, self.range), self.range)
                self.range_rect = self.range_image.get_rect()
                self.range_rect.center = self.rect.center  # Update position to match turret
            
            # Apply turret damage modifier (calculate effective damage)
            damage_mult = world.modifiers.get("turret_damage_mult", 1.0)
            self.effective_damage = int(25 * damage_mult)  # Base damage is 25
            
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
                self.enemy_group = enemy_group
            if world and hasattr(world, 'projectile_group'):
                self.projectile_group = world.projectile_group
            
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

    @staticmethod
    def _placeholder_base():
        """Create a placeholder base image"""
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        surface.fill((120, 100, 100))
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

    def _get_base_image_for_tier(self, tier: int):
        """Get the base image for the given tier (1-indexed)."""
        index = max(0, min(tier - 1, len(self.base_images) - 1))
        return self.base_images[index]

    @staticmethod
    def _placeholder_sprite_sheet():
        """Create a placeholder animation sheet with 8 frames, 64x64 each."""
        frame_size = 64  # Railgun turret uses 64x64 frames
        width = frame_size * c.ANIMATION_STEPS  # 8 frames * 64 = 512
        surface = pygame.Surface((width, frame_size), pygame.SRCALPHA)
        for i in range(c.ANIMATION_STEPS):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            color = (150, 100, 100, 255) if i % 2 == 0 else (100, 70, 70, 255)
            surface.fill(color, frame_rect)
        return surface

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

    def _get_sprite_sheet_for_tier(self, tier: int):
        """Get the sprite sheet for the given tier (1-indexed)."""
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
        """Handle tier upgrades - swap base texture and sprite sheet when available."""
        super().on_upgrade()
        self.base_image = self._get_base_image_for_tier(self.tier)
        self.sprite_sheet = self._get_sprite_sheet_for_tier(self.tier)
        self.animation_list = self.load_image()
        self.frame_index = 0
        self.turret_image = self.animation_list[self.frame_index]
        self._refresh_rect()


# Piercing projectile class
class PiercingProjectile(Projectile):
    """Projectile that pierces through multiple enemies"""
    
    # Class-level sprite sheet (set from main.py after loading)
    sprite_sheet = None
    
    def __init__(self, start_pos, target_pos, speed=400.0, damage=10, pierce_count=3, enemy_group=None):
        # Initialize bullet_frames before calling super() to avoid AttributeError
        self.bullet_frames = []
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.05  # seconds per frame (fast animation)
        
        # Call parent init (which will call draw_projectile, but bullet_frames exists now)
        super().__init__(start_pos, target_pos, speed, damage, target_type="enemy")
        
        # Load bullet frames if sprite sheet provided
        if PiercingProjectile.sprite_sheet:
            self.load_railgun_frames()
            # Update image size to scaled size (19x19)
            scaled_size = int(16 * 1.2)  # 1.2x scale
            self.image = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=self.pos)
        
        # Calculate rotation angle based on velocity direction
        if self.velocity.length() > 0:
            self.angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
        else:
            self.angle = 0.0
        
        # Draw initial bullet (now that frames are loaded)
        self.draw_projectile()
        
        self.pierce_count = pierce_count
        self.pierced_enemies = set()  # Track which enemies have been hit
        self.enemy_group = enemy_group
    
    def load_railgun_frames(self):
        """Load all railgun bullet frames from sprite sheet"""
        if not PiercingProjectile.sprite_sheet:
            return
        
        frame_size = 16  # Each frame is 16x16 pixels
        scaled_size = int(frame_size * 1.2)  # Scale to 1.2x (19 pixels)
        sheet_width = PiercingProjectile.sprite_sheet.get_width()
        num_frames = sheet_width // frame_size  # Should be 4 frames
        
        self.bullet_frames = []
        for i in range(num_frames):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            if frame_rect.right <= sheet_width:
                frame = PiercingProjectile.sprite_sheet.subsurface(frame_rect)
                # Scale the frame to 1.2x size
                scaled_frame = pygame.transform.scale(frame, (scaled_size, scaled_size))
                self.bullet_frames.append(scaled_frame)
            else:
                # Create placeholder if frame doesn't exist
                placeholder = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                placeholder.fill((200, 100, 255, 128))  # Purple placeholder
                self.bullet_frames.append(placeholder)
    
    def draw_projectile(self):
        """Draw the railgun bullet with rotation"""
        self.image.fill((0, 0, 0, 0))
        
        # Check if bullet_frames exists and has frames loaded
        if hasattr(self, 'bullet_frames') and self.bullet_frames and 0 <= self.frame_index < len(self.bullet_frames):
            # Get current bullet frame
            bullet_frame = self.bullet_frames[self.frame_index]
            
            # Update rotation angle based on velocity direction
            if self.velocity.length() > 0:
                self.angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
            
            # Rotate the bullet frame to match trajectory direction
            rotated_bullet = pygame.transform.rotate(bullet_frame, -self.angle)
            
            # Center the rotated bullet in the image
            bullet_rect = rotated_bullet.get_rect()
            bullet_rect.center = (self.image.get_width() // 2, self.image.get_height() // 2)
            self.image.blit(rotated_bullet, bullet_rect)
        else:
            # Fallback: draw simple circle
            pygame.draw.circle(self.image, (200, 100, 255), (9, 9), 4)
            pygame.draw.circle(self.image, (255, 255, 255), (9, 9), 1)
    
    def update(self, dt: float, enemy_group=None, building_group=None):
        """Update piercing projectile"""
        if not self.active:
            return
        
        # Update animation
        if self.bullet_frames:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_delay:
                self.animation_timer = 0.0
                self.frame_index = (self.frame_index + 1) % len(self.bullet_frames)
                # Redraw with new frame (rotation will be recalculated)
                self.draw_projectile()
        
        # Use provided enemy group or stored one
        if enemy_group is None:
            enemy_group = self.enemy_group
        
        # Move projectile
        self.pos += self.velocity * dt
        # Update rect center to match position (after rotation, rect size may have changed)
        self.rect = self.image.get_rect(center=self.pos)
        
        # Check collision with enemies (piercing)
        if enemy_group:
            for enemy in enemy_group:
                if enemy.alive and enemy not in self.pierced_enemies:
                    if self.rect.colliderect(enemy.rect):
                        # Hit enemy
                        # Apply armor pierce modifier if available (for railgun projectiles)
                        world = getattr(self, 'world', None)
                        effective_damage = self.damage
                        if world and hasattr(world, 'modifiers'):
                            armor_pierce_mult = world.modifiers.get("enemy_armor_pierce_mult", 1.0)
                            # Apply armor pierce (increases damage against armored enemies)
                            effective_damage = int(self.damage * armor_pierce_mult)
                        enemy.take_damage(effective_damage)
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

