"""
Spitter zombie enemy - ranged attacker.
"""
import pygame
from world.enemy import Enemy, EnemyAssets
from world.projectile import ZombieBullet
from typing import Tuple, Optional

class SpitterZombie(Enemy):
    """Spitter zombie - ranged attacker with projectile."""
    TYPE_ID = "spitter"
    BASE_HP = 40
    SPEED = 25.0  # pixels per second - slower than basic zombie
    DAMAGE = 8  # Melee damage if close
    ATTACK_RANGE = 150.0  # pixels - ranged attack
    ATTACK_COOLDOWN = 2.0  # seconds - slower ranged attacks
    RANGED_DAMAGE = 12  # Ranged damage
    PROJECTILE_SPEED = 200.0  # pixels per second
    
    # Animation frame ranges (0-indexed)
    IDLE_FRAMES = (0, 3)      # Frames 1-4 (0-3)
    WALK_FRAMES = (4, 9)       # Frames 5-10 (4-9)
    ATTACK_FRAMES = (10, 19)  # Frames 11-20 (10-19) - projectile on last frame (19)
    HURT_FRAMES = (20, 23)    # Frames 21-24 (20-23)
    DEATH_FRAMES = (23, 30)   # Frames 24-31 (23-30) - overlaps with hurt at frame 24
    
    # Frame size for this enemy type
    FRAME_SIZE = 64  # Spitter uses larger frames
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None, sprite_sheet=None):
        super().__init__(pos, hp)
        self.ranged = True
        self.range_damage = self.RANGED_DAMAGE
        self.projectile_speed = self.PROJECTILE_SPEED
        
        # Use cached sprite sheet from EnemyAssets
        self.sprite_sheet = EnemyAssets.spitter_sprite_sheet
        if sprite_sheet is not None:
            self.sprite_sheet = sprite_sheet
        
        # Load animation frames from cache
        if self.sprite_sheet:
            self.animation_frames = EnemyAssets.load_frames(self.sprite_sheet, self.FRAME_SIZE)
            self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
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
        self.projectile_fired = False
        
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
        self.projectile_fired = False
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
            
            # Fire projectile on last frame of attack animation
            if self.is_attacking and self.frame_index == self.ATTACK_FRAMES[1] and not self.projectile_fired:
                # Last frame of attack (frame 19, index 19) - fire projectile
                self.fire_projectile()
                self.projectile_fired = True
            
            # Loop animation (except death which plays once)
            if self.current_state == "death":
                if self.frame_index > frame_end:
                    self.frame_index = frame_end
                    self.death_animation_complete = True
            else:
                if self.frame_index > frame_end:
                    self.frame_index = frame_start
                    # Reset projectile fired flag when attack animation loops
                    if self.current_state == "attack":
                        self.projectile_fired = False
        
        # Clamp frame index to valid range
        if self.frame_index < frame_start:
            self.frame_index = frame_start
        elif self.frame_index > frame_end:
            self.frame_index = frame_end
    
    def fire_projectile(self):
        """Fire projectile at current target building"""
        if not hasattr(self, 'target_building') or not self.target_building:
            return
        
        building = self.target_building
        if not building or not hasattr(building, 'take_damage'):
            return
        
        distance = (self.pos - building.pos).length()
        
        # Only fire if in ranged attack range
        if distance > 50 and self.ranged and distance <= self.attack_range:
            # Spawn projectile (if projectile group exists)
            if hasattr(self, 'projectile_group') and self.projectile_group is not None:
                # Create enemy projectile (targets buildings) - uses ZombieBullet sprite
                projectile = ZombieBullet(
                    start_pos=(self.pos.x, self.pos.y),
                    target_pos=(building.pos.x, building.pos.y),
                    speed=self.projectile_speed,
                    damage=self.range_damage,
                    target_type="building"  # Target buildings, not enemies
                )
                self.projectile_group.add(projectile)
    
    def update(self, dt: float, world=None):
        """Update spitter zombie with animation"""
        # Store previous state to detect changes
        previous_state = self.current_state
        
        # Determine facing direction based on velocity or target
        if hasattr(self, 'target_building') and self.target_building:
            # Face target building
            target_dir = self.target_building.pos - self.pos
            if target_dir.length() > 0:
                self.facing_right = target_dir.x >= 0
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
            # Reset projectile fired flag when state changes
            if previous_state == "attack":
                self.projectile_fired = False
        
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
        """Draw spitter zombie body using sprite sheet"""
        self.image.fill((0, 0, 0, 0))
        
        if not self.animation_frames:
            # Fallback to simple drawing if no sprite sheet
            if self.alive:
                pygame.draw.rect(self.image, (100, 50, 150), (5, 9, 22, 18))
                pygame.draw.circle(self.image, (80, 40, 130), (16, 11), 6)
                pygame.draw.circle(self.image, (0, 255, 0), (14, 10), 1)
                pygame.draw.circle(self.image, (0, 255, 0), (18, 10), 1)
                pygame.draw.ellipse(self.image, (50, 150, 50), (14, 13, 4, 3))
                pygame.draw.rect(self.image, (70, 30, 120), (5, 9, 22, 18), 2)
            else:
                pygame.draw.rect(self.image, (70, 70, 70), (5, 9, 22, 18))
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
        """Draw the spitter zombie - override to allow drawing dead zombies during death animation"""
        # Update rect position
        self.rect.center = self.pos
        
        # Draw zombie body (even if dead, to show death animation)
        self.draw_body(surface)
        
        # Only draw HP bar if alive and damaged
        if self.alive and self.hp < self.max_hp:
            self.draw_hp_bar(surface)
    
    def attack_building(self, building, world=None):
        """Attack a building - melee if close, ranged handled by animation"""
        if not building or not hasattr(building, 'take_damage'):
            return
        
        distance = (self.pos - building.pos).length()
        
        # Store target building for projectile firing
        self.target_building = building
        
        # Melee attack if close (ranged attack is handled by animation)
        if distance <= 32:  # Close range - melee attack
            # Melee attack if close
            # Pass world for damage modifiers
            if world is None:
                world = getattr(self, 'world', None)
            building.take_damage(self.damage, world)
        
        self.on_attack(building)

