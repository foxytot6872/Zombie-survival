"""
Archer Skeleton enemy - ranged attacker with arrows.
"""
import pygame
from world.enemy import Enemy
from typing import Tuple, Optional

class ArcherSkeleton(Enemy):
    """Archer skeleton enemy - ranged attacker with arrow projectiles."""
    TYPE_ID = "archer_skeleton"
    BASE_HP = 50
    SPEED = 30.0  # pixels per second
    DAMAGE = 5  # Melee damage if close
    ATTACK_RANGE = 200.0  # pixels - ranged attack range
    ATTACK_COOLDOWN = 1.5  # seconds - time between attacks
    RANGED_DAMAGE = 8  # Ranged damage
    PROJECTILE_SPEED = 300.0  # pixels per second
    
    # Class-level sprite sheet (set from main.py after loading)
    sprite_sheet = None
    
    # Animation frame ranges (0-indexed, so subtract 1 from user's frame numbers)
    IDLE_FRAMES = (0, 7)      # Frames 1-8 (0-7)
    WALK_FRAMES = (8, 15)     # Frames 9-16 (8-15)
    ATTACK_FRAMES = (16, 21)  # Frames 17-22 (16-21)
    HURT_FRAMES = (22, 25)    # Frames 23-26 (22-25)
    DEATH_FRAMES = (26, 33)   # Frames 27-34 (26-33)
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None, sprite_sheet=None):
        super().__init__(pos, hp)
        
        # Use provided sprite_sheet or class-level sprite_sheet
        self.sprite_sheet = sprite_sheet if sprite_sheet is not None else ArcherSkeleton.sprite_sheet
        self.animation_frames = []
        self.current_state = "idle"
        self.frame_index = self.IDLE_FRAMES[0]  # Start at first idle frame
        self.animation_timer = 0.0
        self.animation_delay = 0.15  # seconds per frame
        self.facing_right = True  # Default facing right
        self.is_hurt = False
        self.hurt_timer = 0.0
        self.hurt_duration = 0.3  # seconds to show hurt animation
        self.death_animation_complete = False
        
        # Ranged attack properties
        self.ranged = True
        self.range_damage = self.RANGED_DAMAGE
        self.projectile_speed = self.PROJECTILE_SPEED
        
        # Load animation frames if sprite sheet provided
        if self.sprite_sheet:
            self.load_animation_frames()
            # Update image size to 48x48
            self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=self.pos)
        
        # Default to moving down if no buildings found
        self.set_direction((0, 1))  # Down direction (fallback)
    
    def load_animation_frames(self):
        """Load all animation frames from sprite sheet"""
        if not self.sprite_sheet:
            return
        
        frame_size = 48  # Each frame is 48x48 pixels
        sheet_width = self.sprite_sheet.get_width()
        num_frames = sheet_width // frame_size  # Should be 34 frames
        
        self.animation_frames = []
        for i in range(num_frames):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            if frame_rect.right <= sheet_width:
                frame = self.sprite_sheet.subsurface(frame_rect)
                self.animation_frames.append(frame)
            else:
                # Create placeholder if frame doesn't exist
                placeholder = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
                placeholder.fill((255, 0, 255, 128))  # Magenta placeholder
                self.animation_frames.append(placeholder)
    
    def get_current_frame_range(self):
        """Get the frame range for current animation state"""
        if not self.alive:
            return self.DEATH_FRAMES
        elif self.is_hurt and self.hurt_timer > 0:
            return self.HURT_FRAMES
        elif self.is_attacking:
            return self.ATTACK_FRAMES
        elif self.velocity.length() > 0:
            return self.WALK_FRAMES
        else:
            return self.IDLE_FRAMES
    
    def update_animation(self, dt: float):
        """Update animation frame based on current state"""
        if not self.animation_frames:
            return
        
        # Update hurt timer
        if self.is_hurt:
            self.hurt_timer -= dt
            if self.hurt_timer <= 0:
                self.is_hurt = False
        
        # Get current frame range
        frame_start, frame_end = self.get_current_frame_range()
        
        # Update animation timer
        self.animation_timer += dt
        
        # Check if we need to advance frame
        if self.animation_timer >= self.animation_delay:
            self.animation_timer = 0.0
            self.frame_index += 1
            
            # Loop animation (except death which plays once)
            if self.current_state == "death":
                if self.frame_index > frame_end:
                    self.frame_index = frame_end
                    self.death_animation_complete = True
            else:
                if self.frame_index > frame_end:
                    self.frame_index = frame_start
        
        # Clamp frame index to valid range
        if self.frame_index < frame_start:
            self.frame_index = frame_start
        elif self.frame_index > frame_end:
            self.frame_index = frame_end
    
    def update(self, dt: float, world=None):
        """Update archer skeleton with animation"""
        # Store previous state to detect changes
        previous_state = self.current_state
        
        # Determine facing direction based on velocity or target
        if self.target_survivor and self.target_survivor.alive:
            # Face the target survivor
            direction_to_target = (self.target_survivor.pos - self.pos)
            if direction_to_target.length() > 0:
                self.facing_right = direction_to_target.x >= 0
        elif self.target_building:
            # Face the target building
            direction_to_target = (self.target_building.pos - self.pos)
            if direction_to_target.length() > 0:
                self.facing_right = direction_to_target.x >= 0
        elif self.velocity.length() > 0:
            self.facing_right = self.velocity.x >= 0
        
        # Update current state
        if not self.alive:
            self.current_state = "death"
        elif self.is_attacking:
            self.current_state = "attack"
        elif self.velocity.length() > 0:
            self.current_state = "walk"
        else:
            self.current_state = "idle"
        
        # Reset frame index if state changed (unless in hurt animation)
        if previous_state != self.current_state and not (self.is_hurt and self.hurt_timer > 0):
            frame_start, _ = self.get_current_frame_range()
            self.frame_index = frame_start
            self.animation_timer = 0.0
        
        # Always update animation (even when dead, to play death animation)
        self.update_animation(dt)
        
        # Set projectile_group from world if available
        if world and hasattr(world, 'projectile_group'):
            self.projectile_group = world.projectile_group
        
        # Only call parent update if alive (parent returns early if not alive anyway)
        if self.alive:
            super().update(dt, world)
        # If dead, stop all movement and just update rect for drawing
        else:
            # Stop velocity
            self.velocity = pygame.Vector2(0, 0)
            # Stop attacking
            self.is_attacking = False
            # Keep rect updated for drawing
            self.rect.center = self.pos
    
    def take_damage(self, amount: int):
        """Apply damage and trigger hurt animation"""
        if not self.alive:
            return
        
        # Store old alive state
        was_alive = self.alive
        
        # Call parent take_damage first
        super().take_damage(amount)
        
        # If archer skeleton just died, start death animation
        if was_alive and not self.alive:
            self.frame_index = self.DEATH_FRAMES[0]  # Start death animation
            self.animation_timer = 0.0
            self.death_animation_complete = False
        elif self.alive:
            # Trigger hurt animation if still alive
            self.is_hurt = True
            self.hurt_timer = self.hurt_duration
            self.frame_index = self.HURT_FRAMES[0]  # Start hurt animation
            self.animation_timer = 0.0
    
    def attack_building(self, building, world=None):
        """Attack a building with ranged attack if far, melee if close"""
        if not building or not hasattr(building, 'take_damage'):
            return
        
        distance = (self.pos - building.pos).length()
        
        # For ranged enemies, use full attack_range (not attack_range + radius)
        # Ranged attack if in range (allow attacks from full range, not just close)
        if self.ranged and distance <= self.attack_range:
            # Spawn arrow projectile (if projectile group exists)
            if hasattr(self, 'projectile_group') and self.projectile_group is not None:
                from world.projectile import ArrowProjectile
                # Create arrow projectile (targets buildings)
                arrow = ArrowProjectile(
                    start_pos=(self.pos.x, self.pos.y),
                    target_pos=(building.pos.x, building.pos.y),
                    speed=self.projectile_speed,
                    damage=self.range_damage,
                    target_type="building"  # Target buildings
                )
                self.projectile_group.add(arrow)
                print(f"Archer skeleton shot arrow at building (distance: {distance:.1f}, range: {self.attack_range})")
            else:
                print(f"Archer skeleton: projectile_group not set! hasattr: {hasattr(self, 'projectile_group')}")
        elif distance <= 32:  # Close range - melee attack
            # Melee attack if close
            if world is None:
                world = getattr(self, 'world', None)
            building.take_damage(self.damage, world)
        
        self.on_attack(building)
    
    def attack_survivor(self, survivor, world=None):
        """Attack a survivor with ranged attack if far, melee if close"""
        if not survivor or not survivor.alive or not hasattr(survivor, 'take_damage'):
            return
        
        distance = (self.pos - survivor.pos).length()
        
        # For ranged enemies, use full attack_range (not attack_range + radius)
        # Ranged attack if in range (allow attacks from full range, not just close)
        if self.ranged and distance <= self.attack_range:
            # Spawn arrow projectile (if projectile group exists)
            if hasattr(self, 'projectile_group') and self.projectile_group is not None:
                from world.projectile import ArrowProjectile
                # Create arrow projectile (targets survivors)
                arrow = ArrowProjectile(
                    start_pos=(self.pos.x, self.pos.y),
                    target_pos=(survivor.pos.x, survivor.pos.y),
                    speed=self.projectile_speed,
                    damage=self.range_damage,
                    target_type="survivor"  # Target survivors
                )
                self.projectile_group.add(arrow)
                print(f"Archer skeleton shot arrow at survivor (distance: {distance:.1f}, range: {self.attack_range})")
            else:
                print(f"Archer skeleton: projectile_group not set! hasattr: {hasattr(self, 'projectile_group')}")
        elif distance <= 32:  # Close range - melee attack
            # Melee attack if close
            survivor.take_damage(self.damage)
        
        self.on_attack_survivor(survivor)
    
    def draw_body(self, surface: pygame.Surface):
        """Draw archer skeleton body using sprite sheet"""
        self.image.fill((0, 0, 0, 0))
        
        if not self.animation_frames:
            # Fallback to simple drawing if no sprite sheet
            if self.alive:
                pygame.draw.rect(self.image, (200, 200, 200), (4, 8, 24, 20))
                pygame.draw.circle(self.image, (180, 180, 180), (16, 10), 6)
            else:
                pygame.draw.rect(self.image, (100, 100, 100), (4, 8, 24, 20))
            surface.blit(self.image, self.rect)
            return
        
        # Get current frame
        if 0 <= self.frame_index < len(self.animation_frames):
            current_frame = self.animation_frames[self.frame_index]
            
            # Flip sprite if facing left
            if not self.facing_right:
                current_frame = pygame.transform.flip(current_frame, True, False)
            
            # Draw frame centered in image
            frame_rect = current_frame.get_rect()
            frame_rect.center = (self.image.get_width() // 2, self.image.get_height() // 2)
            self.image.blit(current_frame, frame_rect)
        
        surface.blit(self.image, self.rect)
    
    def draw(self, surface: pygame.Surface):
        """Draw the archer skeleton - override to allow drawing dead skeletons during death animation"""
        # Update rect position
        self.rect.center = self.pos
        
        # Draw archer skeleton body (even if dead, to show death animation)
        self.draw_body(surface)
        
        # Only draw HP bar if alive and damaged
        if self.alive and self.hp < self.max_hp:
            self.draw_hp_bar(surface)

