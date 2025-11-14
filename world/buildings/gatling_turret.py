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
    
    def __init__(self, grid_pos, turret_image=None, base_image=None, tier=1, uid=None, turret_sheet=None):
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
        if self.base_image is None:
            # Create placeholder if base_image not provided
            self.base_image = pygame.Surface((32, 32))
            self.base_image.fill((120, 100, 80))
        self.selected = False
        
        # Animation state
        self.animation_state = "idle"  # "idle", "windup", "firing", "winddown"
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.1  # seconds per frame
        self.windup_frames = []  # frames 1-4 (0-3)
        self.firing_frames = []  # frames 5-9 (4-8)
        self.winddown_frames = []  # frames 4-1 reverse (3-0)
        self.animation_frames = []
        self.is_animated = False
        
        # Check if we have a sprite sheet (tiwtir gun turret)
        if turret_sheet is not None:
            self.is_animated = True
            # Extract frames from sprite sheet (9 frames, 96x96 each)
            frame_width = 96
            frame_height = 96
            sheet_width = turret_sheet.get_width()
            sheet_height = turret_sheet.get_height()
            
            print(f"Loading Gatling turret sprite sheet: {sheet_width}x{sheet_height}, extracting {frame_width}x{frame_height} frames")
            
            # Extract all 9 frames
            for i in range(9):
                x_pos = i * frame_width
                if x_pos + frame_width <= sheet_width:
                    try:
                        frame_rect = pygame.Rect(x_pos, 0, frame_width, frame_height)
                        frame = turret_sheet.subsurface(frame_rect)
                        self.animation_frames.append(frame)
                        print(f"  Extracted frame {i+1}: {frame.get_size()}")
                    except Exception as e:
                        print(f"  Error extracting frame {i+1}: {e}")
                else:
                    print(f"  Frame {i+1} out of bounds: x_pos={x_pos}, width={frame_width}, sheet_width={sheet_width}")
            
            print(f"Total frames extracted: {len(self.animation_frames)}")
            
            # Set up animation frame groups
            if len(self.animation_frames) >= 9:
                # Windup: frames 1-4 (0-3)
                self.windup_frames = self.animation_frames[0:4]
                # Firing: frames 5-9 (4-8)
                self.firing_frames = self.animation_frames[4:9]
                # Winddown: frames 4-1 reverse (3-0)
                self.winddown_frames = self.animation_frames[3::-1]  # Reverse slice from index 3 to 0
                print(f"Animation groups: windup={len(self.windup_frames)}, firing={len(self.firing_frames)}, winddown={len(self.winddown_frames)}")
            else:
                print(f"Warning: Expected 9 frames but got {len(self.animation_frames)}")
            
            # Start with idle (first frame) - use windup frames for idle state
            if self.animation_frames and len(self.animation_frames) > 0:
                # Use first frame as idle
                first_frame = self.animation_frames[0]
                self.current_frames = [first_frame]
                self.frame_index = 0
                # Make sure we have a valid image - convert to ensure it's a proper surface
                self.turret_image = first_frame.copy().convert_alpha() if first_frame else None
                self.animation_state = "idle"
                if self.turret_image:
                    print(f"Initial turret image size: {self.turret_image.get_size()}, is_animated={self.is_animated}")
                else:
                    print(f"Warning: Failed to create turret_image from first frame")
            else:
                self.current_frames = []
                self.frame_index = 0
                self.turret_image = None
                print(f"Warning: No frames extracted, turret_image is None. Frames: {len(self.animation_frames)}")
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
        super().update(dt, world)
        
        if self.state == BuildState.ACTIVE:
            enemy_group = None
            if world and hasattr(world, 'enemy_group'):
                enemy_group = world.enemy_group
            if world and hasattr(world, 'projectile_group'):
                self.projectile_group = world.projectile_group
            
            is_firing = False
            
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
                        is_firing = True
                    elif is_aimed and not can_shoot:
                        # Aimed but on cooldown - still "firing" visually
                        is_firing = True
                else:
                    self.target_enemy = None
            
            # Update animation
            self.update_animation(dt, is_firing)
    
    def draw(self, surface: pygame.Surface):
        """Draw turret"""
        # Draw range circle if selected (behind base)
        if self.selected and self.state == BuildState.ACTIVE:
            self.update_range_position()
            surface.blit(self.range_image, self.range_rect)
        
        # Draw base
        if self.base_image:
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

