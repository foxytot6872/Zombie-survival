"""
Warrior Skeleton enemy - melee fighter with blocking ability.
"""
import pygame
import random
from world.enemy import Enemy, EnemyAssets
from typing import Tuple, Optional

class WarriorSkeleton(Enemy):
    """Warrior skeleton enemy - melee fighter that can block incoming attacks."""
    TYPE_ID = "warrior_skeleton"
    BASE_HP = 80
    SPEED = 30.0  # pixels per second
    DAMAGE = 8
    ATTACK_RANGE = 32.0  # pixels - range for attacking buildings
    ATTACK_COOLDOWN = 1.3  # seconds - time between attacks
    BLOCK_CHANCE = 0.3  # 30% chance to block incoming damage
    BLOCK_DAMAGE_REDUCTION = 0.5  # Block reduces damage by 50%
    
    # Animation frame ranges (0-indexed)
    IDLE_FRAMES = (0, 7)      # Frames 1-8 (0-7)
    WALK_FRAMES = (8, 15)      # Frames 9-16 (8-15)
    ATTACK_FRAMES = (16, 27)   # Frames 17-28 (16-27)
    BLOCK_FRAMES = (28, 33)    # Frames 29-34 (28-33)
    HURT_FRAMES = (34, 37)     # Frames 35-38 (34-37)
    DEATH_FRAMES = (38, 45)    # Frames 39-46 (38-45)
    
    # Frame size and scale
    FRAME_SIZE = 48
    SPRITE_SCALE = 1.2  # Warrior skeleton is bigger
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None, sprite_sheet=None):
        super().__init__(pos, hp)
        
        # Use cached sprite sheet from EnemyAssets
        self.sprite_sheet = EnemyAssets.warrior_skeleton_sprite_sheet
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
        self.is_blocking = False
        self.block_timer = 0.0
        self.block_duration = 0.5
        self.death_animation_complete = False
        self.sprite_scale = self.SPRITE_SCALE
        
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
        self.is_blocking = False
        self.block_timer = 0.0
        self.death_animation_complete = False
        self.set_direction((0, 1))
    
    def load_animation_frames(self):
        """Legacy method - now uses cached frames from EnemyAssets"""
        pass
    
    def get_current_frame_range(self):
        """Get the frame range for current animation state"""
        if not self.alive:
            return self.DEATH_FRAMES
        elif self.is_blocking and self.block_timer > 0:
            return self.BLOCK_FRAMES
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
        
        # Update block timer
        if self.is_blocking:
            self.block_timer -= dt
            if self.block_timer <= 0:
                self.is_blocking = False
        
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
            
            # Loop animation (except death and block which play once)
            if self.current_state == "death":
                if self.frame_index > frame_end:
                    self.frame_index = frame_end
                    self.death_animation_complete = True
            elif self.current_state == "block":
                # Block animation loops while blocking
                if self.frame_index > frame_end:
                    self.frame_index = frame_start
            else:
                if self.frame_index > frame_end:
                    self.frame_index = frame_start
        
        # Clamp frame index to valid range
        if self.frame_index < frame_start:
            self.frame_index = frame_start
        elif self.frame_index > frame_end:
            self.frame_index = frame_end
    
    def update(self, dt: float, world=None):
        """Update warrior skeleton with animation"""
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
        elif self.is_blocking and self.block_timer > 0:
            self.current_state = "block"
        elif self.is_attacking:
            self.current_state = "attack"
        elif self.velocity.length() > 0:
            self.current_state = "walk"
        else:
            self.current_state = "idle"
        
        # Reset frame index if state changed (unless in block or hurt animation)
        if previous_state != self.current_state and not (self.is_blocking and self.block_timer > 0) and not (self.is_hurt and self.hurt_timer > 0):
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
        """Apply damage with chance to block"""
        if not self.alive:
            return
        
        # Check if warrior skeleton blocks the attack
        if random.random() < self.BLOCK_CHANCE:
            # Block successful - reduce damage
            blocked_amount = int(amount * self.BLOCK_DAMAGE_REDUCTION)
            actual_damage = amount - blocked_amount
            
            # Trigger block animation
            self.is_blocking = True
            self.block_timer = self.block_duration
            frame_start, _ = self.BLOCK_FRAMES
            self.frame_index = frame_start
            self.animation_timer = 0.0
            
            # Apply reduced damage
            if actual_damage > 0:
                self.hp -= actual_damage
                if self.hp <= 0:
                    self.hp = 0
                    self.alive = False
                    # Release attack slot on death
                    if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                        self.target_building.release_attack_slot()
                    # Clear survivor target
                    self.target_survivor = None
                    self.on_death()
                    # Start death animation
                    self.frame_index = self.DEATH_FRAMES[0]
                    self.animation_timer = 0.0
                    self.death_animation_complete = False
        else:
            # Block failed - take full damage
            # Store old alive state
            was_alive = self.alive
            
            self.hp -= amount
            if self.hp <= 0:
                self.hp = 0
                self.alive = False
                # Release attack slot on death
                if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                    self.target_building.release_attack_slot()
                # Clear survivor target
                self.target_survivor = None
                self.on_death()
            
            # If warrior skeleton just died, start death animation
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
        """Draw warrior skeleton body using sprite sheet"""
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
            
            # Scale frame
            if hasattr(self, 'sprite_scale') and self.sprite_scale != 1.0:
                scaled_size = (int(current_frame.get_width() * self.sprite_scale), 
                              int(current_frame.get_height() * self.sprite_scale))
                current_frame = pygame.transform.smoothscale(current_frame, scaled_size)
            
            # Draw frame centered in image
            frame_rect = current_frame.get_rect()
            frame_rect.center = (self.image.get_width() // 2, self.image.get_height() // 2)
            self.image.blit(current_frame, frame_rect)
        
        surface.blit(self.image, self.rect)
    
    def draw(self, surface: pygame.Surface):
        """Draw the warrior skeleton - override to allow drawing dead skeletons during death animation"""
        # Update rect position
        self.rect.center = self.pos
        
        # Draw warrior skeleton body (even if dead, to show death animation)
        self.draw_body(surface)
        
        # Only draw HP bar if alive and damaged
        if self.alive and self.hp < self.max_hp:
            self.draw_hp_bar(surface)

