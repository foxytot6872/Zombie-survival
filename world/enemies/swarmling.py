"""
Swarmling zombie enemy - tiny HP, very fast.
"""
import pygame
from world.enemy import Enemy
from typing import Tuple, Optional

class SwarmlingZombie(Enemy):
    """Swarmling zombie - very fast but very weak."""
    TYPE_ID = "swarmling"
    BASE_HP = 10
    SPEED = 80.0  # pixels per second - very fast
    DAMAGE = 2
    ATTACK_RANGE = 24.0  # pixels - small reach
    ATTACK_COOLDOWN = 0.5  # seconds - very fast attacks
    
    # Class-level sprite sheet (set from main.py after loading)
    sprite_sheet = None
    
    # Animation frame ranges (0-indexed, same as other zombies)
    IDLE_FRAMES = (0, 3)      # Frames 1-4 (0-3)
    WALK_FRAMES = (4, 9)       # Frames 5-10 (4-9)
    ATTACK_FRAMES = (10, 18)  # Frames 11-19 (10-18)
    HURT_FRAMES = (19, 22)    # Frames 20-23 (19-22)
    DEATH_FRAMES = (23, 31)   # Frames 24-32 (23-31)
    
    # Scale factor for swarmling (0.8 = 80% size)
    SCALE_FACTOR = 0.8
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None, sprite_sheet=None):
        super().__init__(pos, hp)
        
        # Use provided sprite_sheet or class-level sprite_sheet
        self.sprite_sheet = sprite_sheet if sprite_sheet is not None else SwarmlingZombie.sprite_sheet
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
        
        # Load animation frames if sprite sheet provided
        if self.sprite_sheet:
            self.load_animation_frames()
            # Update image size to scaled 48x48 (38x38 at 0.8 scale)
            scaled_size = int(48 * self.SCALE_FACTOR)
            self.image = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=self.pos)
        else:
            # Fallback to simple drawing if no sprite sheet
            self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=self.pos)
        
        # Default to moving down if no buildings found
        self.set_direction((0, 1))
    
    def load_animation_frames(self):
        """Load all animation frames from sprite sheet and scale them down"""
        if not self.sprite_sheet:
            return
        
        frame_size = 48  # Original frame size is 48x48 pixels
        sheet_width = self.sprite_sheet.get_width()
        num_frames = sheet_width // frame_size  # Should be 32 frames
        
        self.animation_frames = []
        scaled_size = int(frame_size * self.SCALE_FACTOR)  # Scale to 0.8 (38x38)
        
        for i in range(num_frames):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            frame = self.sprite_sheet.subsurface(frame_rect)
            # Scale frame down to 0.8
            scaled_frame = pygame.transform.scale(frame, (scaled_size, scaled_size))
            self.animation_frames.append(scaled_frame)
    
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
        """Update swarmling zombie with animation"""
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
        
        # If zombie just died, start death animation
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
        """Draw swarmling zombie body using sprite sheet"""
        self.image.fill((0, 0, 0, 0))
        
        if not self.animation_frames:
            # Fallback to simple drawing if no sprite sheet
            if self.alive:
                pygame.draw.rect(self.image, (120, 100, 80), (4, 6, 12, 10))
                pygame.draw.circle(self.image, (100, 80, 60), (10, 7), 3)
                pygame.draw.circle(self.image, (150, 0, 0), (9, 6), 1)
                pygame.draw.circle(self.image, (150, 0, 0), (11, 6), 1)
                pygame.draw.rect(self.image, (80, 60, 40), (4, 6, 12, 10), 1)
            else:
                pygame.draw.rect(self.image, (60, 60, 60), (4, 6, 12, 10))
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
        """Draw the swarmling zombie - override to allow drawing dead zombies during death animation"""
        # Update rect position
        self.rect.center = self.pos
        
        # Draw zombie body (even if dead, to show death animation)
        self.draw_body(surface)
        
        # Only draw HP bar if alive and damaged
        if self.alive and self.hp < self.max_hp:
            self.draw_hp_bar(surface)

