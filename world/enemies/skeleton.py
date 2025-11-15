"""
Skeleton enemy - basic skeleton type.
"""
import pygame
from world.enemy import Enemy, EnemyAssets
from typing import Tuple, Optional

class Skeleton(Enemy):
    """Basic skeleton enemy - targets and attacks buildings and survivors."""
    TYPE_ID = "skeleton"
    BASE_HP = 60
    SPEED = 35.0  # pixels per second
    DAMAGE = 6
    ATTACK_RANGE = 32.0  # pixels - range for attacking buildings
    ATTACK_COOLDOWN = 1.2  # seconds - time between attacks
    
    # Animation frame ranges (0-indexed)
    IDLE_FRAMES = (0, 7)      # Frames 1-8 (0-7)
    WALK_FRAMES = (8, 15)      # Frames 9-16 (8-15)
    ATTACK_FRAMES = (16, 27)   # Frames 17-28 (16-27)
    HURT_FRAMES = (28, 31)     # Frames 29-32 (28-31)
    DEATH_FRAMES = (32, 39)    # Frames 33-40 (32-39)
    
    # Frame size for this enemy type
    FRAME_SIZE = 48
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None, sprite_sheet=None):
        super().__init__(pos, hp)
        
        # Use cached sprite sheet from EnemyAssets
        self.sprite_sheet = EnemyAssets.skeleton_sprite_sheet
        if sprite_sheet is not None:
            self.sprite_sheet = sprite_sheet
        
        # Load animation frames from cache
        if self.sprite_sheet:
            self.animation_frames = EnemyAssets.load_frames(self.sprite_sheet, self.FRAME_SIZE)
            self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=self.pos)
        else:
            self.animation_frames = []
        
        # Animation state
        self.current_state = "idle"
        self.frame_index = self.IDLE_FRAMES[0]
        self.animation_timer = 0.0
        self.animation_delay = 0.15
        self.facing_right = True
        self.is_hurt = False
        self.hurt_timer = 0.0
        self.hurt_duration = 0.3
        self.death_animation_complete = False
        
        # Default to moving down if no buildings found
        self.set_direction((0, 1))
    
    def on_reset(self):
        """Reset animation state for reuse"""
        self.current_state = "idle"
        self.frame_index = self.IDLE_FRAMES[0]
        self.animation_timer = 0.0
        self.facing_right = True
        self.is_hurt = False
        self.hurt_timer = 0.0
        self.death_animation_complete = False
        self.set_direction((0, 1))
    
    def load_animation_frames(self):
        """Legacy method - now uses cached frames from EnemyAssets"""
        pass
    
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
        """Update skeleton with animation"""
        # Store previous state to detect changes
        previous_state = self.current_state
        
        # Determine facing direction based on velocity
        if self.velocity.length() > 0:
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
        
        # If skeleton just died, start death animation
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
    
    def draw_body(self, surface: pygame.Surface):
        """Draw skeleton body using sprite sheet"""
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
        """Draw the skeleton - override to allow drawing dead skeletons during death animation"""
        # Update rect position
        self.rect.center = self.pos
        
        # Draw skeleton body (even if dead, to show death animation)
        self.draw_body(surface)
        
        # Only draw HP bar if alive and damaged
        if self.alive and self.hp < self.max_hp:
            self.draw_hp_bar(surface)

