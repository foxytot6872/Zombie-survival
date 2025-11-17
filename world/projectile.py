"""
Projectile system for turrets and other weapons.
"""
from __future__ import annotations
import pygame
import math
from typing import Tuple, Optional

class Projectile(pygame.sprite.Sprite):
    """Base projectile class"""
    
    # Class-level sprite sheet (set from main.py after loading)
    sprite_sheet = None
    
    def __init__(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float], 
                 speed: float = 400.0, damage: int = 10, target_type: str = "enemy"):
        super().__init__()
        self.start_pos = pygame.Vector2(start_pos)
        self.target_pos = pygame.Vector2(target_pos)
        self.pos = pygame.Vector2(start_pos)
        self.speed = speed  # pixels per second
        self.damage = damage
        self.target_type = target_type  # "enemy" or "building"
        
        # Calculate direction to target
        direction = (self.target_pos - self.start_pos)
        if direction.length() > 0:
            self.velocity = direction.normalize() * self.speed
        else:
            self.velocity = pygame.Vector2(0, 0)
        
        # Animation state (for sprite-based projectiles)
        self.bullet_frames = []
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.05  # seconds per frame (fast animation)
        
        # Calculate rotation angle based on velocity direction
        if self.velocity.length() > 0:
            self.angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
        else:
            self.angle = 0.0
        
        # Rendering - use scaled size (19x19) if sprite sheet available, otherwise 8x8
        frame_size = int(16 * 1.2) if Projectile.sprite_sheet else 8  # 1.2x scale = 19 pixels
        self.image = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        
        # State
        self.active = True
        self.hit = False
        
        # Load bullet frames if sprite sheet provided
        if Projectile.sprite_sheet:
            self.load_bullet_frames()
        
        # Draw projectile
        self.draw_projectile()
    
    def load_bullet_frames(self):
        """Load all bullet frames from sprite sheet"""
        if not Projectile.sprite_sheet:
            return
        
        frame_size = 16  # Each frame is 16x16 pixels
        scaled_size = int(frame_size * 1.2)  # Scale to 1.2x (19.2 -> 19 pixels)
        sheet_width = Projectile.sprite_sheet.get_width()
        num_frames = sheet_width // frame_size  # Should be 4 frames
        
        self.bullet_frames = []
        for i in range(num_frames):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            if frame_rect.right <= sheet_width:
                frame = Projectile.sprite_sheet.subsurface(frame_rect)
                # Scale the frame to 1.2x size
                scaled_frame = pygame.transform.scale(frame, (scaled_size, scaled_size))
                self.bullet_frames.append(scaled_frame)
            else:
                # Create placeholder if frame doesn't exist
                placeholder = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                placeholder.fill((255, 200, 0, 128))  # Yellow/orange placeholder
                self.bullet_frames.append(placeholder)
    
    def draw_projectile(self):
        """Draw the projectile"""
        self.image.fill((0, 0, 0, 0))
        
        # Use sprite frames if available
        if self.bullet_frames and 0 <= self.frame_index < len(self.bullet_frames):
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
            # Fallback: draw simple circle (yellow/orange bullet)
            pygame.draw.circle(self.image, (255, 200, 0), (4, 4), 3)
            pygame.draw.circle(self.image, (255, 255, 255), (4, 4), 1)
    
    def update(self, dt: float, enemy_group=None, building_group=None):
        """Update projectile position and check collisions"""
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
        
        # Move projectile
        self.pos += self.velocity * dt
        # Update rect center to match position (after rotation, rect size may have changed)
        self.rect = self.image.get_rect(center=self.pos)
        
        # Check collision based on target type
        if self.target_type == "enemy":
            # Check collision with enemies (turret projectiles)
            if enemy_group:
                for enemy in enemy_group:
                    if enemy.alive and self.rect.colliderect(enemy.rect):
                        # Hit enemy
                        # Apply armor pierce modifier if available (for railgun projectiles)
                        world = getattr(self, 'world', None)
                        effective_damage = self.damage
                        if world and hasattr(world, 'modifiers'):
                            armor_pierce_mult = world.modifiers.get("enemy_armor_pierce_mult", 1.0)
                            # Apply armor pierce (increases damage against armored enemies)
                            effective_damage = int(self.damage * armor_pierce_mult)
                        
                        # SwarmlingZombie takes double damage (handled in enemy.take_damage, but apply here too for consistency)
                        from world.enemies.swarmling import SwarmlingZombie
                        if isinstance(enemy, SwarmlingZombie):
                            effective_damage *= 2
                        
                        enemy.take_damage(effective_damage)
                        self.hit = True
                        self.active = False
                        return
        elif self.target_type == "building":
            # Check collision with buildings (enemy projectiles, e.g., spitter)
            if building_group:
                for building in building_group:
                    if (hasattr(building, 'state') and 
                        building.state != "destroyed" and
                        self.rect.colliderect(building.rect)):
                        # Hit building
                        if hasattr(building, 'take_damage'):
                            # Pass world for damage modifiers
                            world = getattr(self, 'world', None)
                            building.take_damage(self.damage, world)
                        self.hit = True
                        self.active = False
                        return
        
        # Check if projectile has traveled too far (despawn after range)
        distance_traveled = (self.pos - self.start_pos).length()
        if distance_traveled > 500:  # Max range
            self.active = False
        
        # Check if out of bounds
        if self.pos.x < 0 or self.pos.x > 1920 or self.pos.y < 0 or self.pos.y > 1080:
            self.active = False
    
    def draw(self, surface: pygame.Surface):
        """Draw the projectile"""
        if self.active:
            surface.blit(self.image, self.rect)


class GatlingBullet(Projectile):
    """Gatling turret bullet with sprite animation"""
    
    # Class-level sprite sheet (set from main.py after loading)
    sprite_sheet = None
    
    def __init__(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float], 
                 speed: float = 400.0, damage: int = 10, target_type: str = "enemy"):
        # Initialize bullet_frames before calling super() to avoid AttributeError
        self.bullet_frames = []
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.05  # seconds per frame (fast animation)
        
        # Call parent init (which will call draw_projectile, but bullet_frames exists now)
        super().__init__(start_pos, target_pos, speed, damage, target_type)
        
        # Load bullet frames if sprite sheet provided
        if GatlingBullet.sprite_sheet:
            self.load_gatling_frames()
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
    
    def load_gatling_frames(self):
        """Load all gatling bullet frames from sprite sheet"""
        if not GatlingBullet.sprite_sheet:
            return
        
        frame_size = 16  # Each frame is 16x16 pixels
        scaled_size = int(frame_size * 1.2)  # Scale to 1.2x (19 pixels)
        sheet_width = GatlingBullet.sprite_sheet.get_width()
        num_frames = sheet_width // frame_size  # Should be 4 frames
        
        self.bullet_frames = []
        for i in range(num_frames):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            if frame_rect.right <= sheet_width:
                frame = GatlingBullet.sprite_sheet.subsurface(frame_rect)
                # Scale the frame to 1.2x size
                scaled_frame = pygame.transform.scale(frame, (scaled_size, scaled_size))
                self.bullet_frames.append(scaled_frame)
            else:
                # Create placeholder if frame doesn't exist
                placeholder = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                placeholder.fill((255, 150, 0, 128))  # Orange placeholder
                self.bullet_frames.append(placeholder)
    
    def draw_projectile(self):
        """Draw the gatling bullet with rotation"""
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
            pygame.draw.circle(self.image, (255, 150, 0), (9, 9), 4)
            pygame.draw.circle(self.image, (255, 255, 255), (9, 9), 1)
    
    def update(self, dt: float, enemy_group=None, building_group=None):
        """Update gatling bullet position and check collisions"""
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
        
        # Move projectile
        self.pos += self.velocity * dt
        # Update rect center to match position (after rotation, rect size may have changed)
        self.rect = self.image.get_rect(center=self.pos)
        
        # Check collision based on target type
        if self.target_type == "enemy":
            # Check collision with enemies (turret projectiles)
            if enemy_group:
                for enemy in enemy_group:
                    if enemy.alive and self.rect.colliderect(enemy.rect):
                        # Hit enemy
                        world = getattr(self, 'world', None)
                        effective_damage = self.damage
                        if world and hasattr(world, 'modifiers'):
                            armor_pierce_mult = world.modifiers.get("enemy_armor_pierce_mult", 1.0)
                            effective_damage = int(self.damage * armor_pierce_mult)
                        enemy.take_damage(effective_damage)
                        self.hit = True
                        self.active = False
                        return
        
        # Check if projectile has traveled too far (despawn after range)
        distance_traveled = (self.pos - self.start_pos).length()
        if distance_traveled > 500:  # Max range
            self.active = False
        
        # Check if out of bounds
        if self.pos.x < 0 or self.pos.x > 1920 or self.pos.y < 0 or self.pos.y > 1080:
            self.active = False


class ZombieBullet(Projectile):
    """Zombie enemy bullet with sprite animation (for spitter zombies)"""
    
    # Class-level sprite sheet (set from main.py after loading)
    sprite_sheet = None
    
    def __init__(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float], 
                 speed: float = 200.0, damage: int = 12, target_type: str = "building"):
        # Initialize bullet_frames before calling super() to avoid AttributeError
        self.bullet_frames = []
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.05  # seconds per frame (fast animation)
        
        # Call parent init (which will call draw_projectile, but bullet_frames exists now)
        super().__init__(start_pos, target_pos, speed, damage, target_type)
        
        # Load bullet frames if sprite sheet provided
        if ZombieBullet.sprite_sheet:
            self.load_zombie_frames()
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
    
    def load_zombie_frames(self):
        """Load all zombie bullet frames from sprite sheet"""
        if not ZombieBullet.sprite_sheet:
            return
        
        frame_size = 16  # Each frame is 16x16 pixels
        scaled_size = int(frame_size * 1.2)  # Scale to 1.2x (19 pixels)
        sheet_width = ZombieBullet.sprite_sheet.get_width()
        num_frames = sheet_width // frame_size  # Should be 4 frames
        
        self.bullet_frames = []
        for i in range(num_frames):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            if frame_rect.right <= sheet_width:
                frame = ZombieBullet.sprite_sheet.subsurface(frame_rect)
                # Scale the frame to 1.2x size
                scaled_frame = pygame.transform.scale(frame, (scaled_size, scaled_size))
                self.bullet_frames.append(scaled_frame)
            else:
                # Create placeholder if frame doesn't exist
                placeholder = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                placeholder.fill((150, 50, 50, 128))  # Red placeholder
                self.bullet_frames.append(placeholder)
    
    def draw_projectile(self):
        """Draw the zombie bullet with rotation"""
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
            pygame.draw.circle(self.image, (150, 50, 50), (9, 9), 4)
            pygame.draw.circle(self.image, (255, 255, 255), (9, 9), 1)
    
    def update(self, dt: float, enemy_group=None, building_group=None):
        """Update zombie bullet position and check collisions"""
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
        
        # Move projectile
        self.pos += self.velocity * dt
        # Update rect center to match position (after rotation, rect size may have changed)
        self.rect = self.image.get_rect(center=self.pos)
        
        # Check collision based on target type (zombie bullets target buildings)
        if self.target_type == "building":
            # Check collision with buildings
            if building_group:
                for building in building_group:
                    if (hasattr(building, 'state') and 
                        building.state != "destroyed" and
                        self.rect.colliderect(building.rect)):
                        # Hit building
                        if hasattr(building, 'take_damage'):
                            world = getattr(self, 'world', None)
                            building.take_damage(self.damage, world)
                        self.hit = True
                        self.active = False
                        return
        
        # Check if projectile has traveled too far (despawn after range)
        distance_traveled = (self.pos - self.start_pos).length()
        if distance_traveled > 500:  # Max range
            self.active = False
        
        # Check if out of bounds
        if self.pos.x < 0 or self.pos.x > 1920 or self.pos.y < 0 or self.pos.y > 1080:
            self.active = False


class ArrowProjectile(Projectile):
    """Arrow projectile with sprite animation"""
    
    # Class-level sprite sheet (set from main.py after loading)
    sprite_sheet = None
    
    def __init__(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float], 
                 speed: float = 300.0, damage: int = 8, target_type: str = "building"):
        # Initialize arrow_frames before calling super() to avoid AttributeError
        # when parent's draw_projectile() is called
        self.arrow_frames = []
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.1  # seconds per frame
        
        # Call parent init (which will call draw_projectile, but arrow_frames exists now)
        super().__init__(start_pos, target_pos, speed, damage, target_type)
        
        # Load arrow frames if sprite sheet provided
        if ArrowProjectile.sprite_sheet:
            self.load_arrow_frames()
            # Update image size to 16x16
            self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=self.pos)
        
        # Calculate rotation angle based on velocity direction
        if self.velocity.length() > 0:
            self.angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
        else:
            self.angle = 0.0
        
        # Draw initial arrow (now that frames are loaded)
        self.draw_projectile()
    
    def load_arrow_frames(self):
        """Load all arrow frames from sprite sheet"""
        if not ArrowProjectile.sprite_sheet:
            return
        
        frame_size = 16  # Each frame is 16x16 pixels
        sheet_width = ArrowProjectile.sprite_sheet.get_width()
        num_frames = sheet_width // frame_size  # Should be 4 frames
        
        self.arrow_frames = []
        for i in range(num_frames):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            if frame_rect.right <= sheet_width:
                frame = ArrowProjectile.sprite_sheet.subsurface(frame_rect)
                self.arrow_frames.append(frame)
            else:
                # Create placeholder if frame doesn't exist
                placeholder = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
                placeholder.fill((255, 255, 0, 128))  # Yellow placeholder
                self.arrow_frames.append(placeholder)
    
    def draw_projectile(self):
        """Draw the arrow projectile with rotation"""
        # Ensure image exists and is the right size
        if not hasattr(self, 'image') or self.image is None:
            self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        
        # Check if arrow_frames exists and has frames loaded
        if hasattr(self, 'arrow_frames') and self.arrow_frames and 0 <= self.frame_index < len(self.arrow_frames):
            # Get current arrow frame
            arrow_frame = self.arrow_frames[self.frame_index]
            
            # Rotate arrow based on velocity direction
            if self.velocity.length() > 0:
                self.angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
            
            # Rotate the arrow frame
            rotated_arrow = pygame.transform.rotate(arrow_frame, -self.angle)
            
            # Center the rotated arrow in the image
            arrow_rect = rotated_arrow.get_rect()
            arrow_rect.center = (self.image.get_width() // 2, self.image.get_height() // 2)
            self.image.blit(rotated_arrow, arrow_rect)
        else:
            # Fallback: draw simple arrow shape
            # Draw arrow pointing right (will be rotated)
            pygame.draw.polygon(self.image, (150, 100, 50), [
                (12, 8),  # Tip
                (4, 4),   # Top corner
                (4, 12),  # Bottom corner
            ])
            pygame.draw.line(self.image, (100, 50, 0), (4, 8), (0, 8), 2)  # Shaft
            
            # Rotate if needed
            if self.velocity.length() > 0:
                self.angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
                self.image = pygame.transform.rotate(self.image, -self.angle)
                # Re-center after rotation
                self.rect = self.image.get_rect(center=self.pos)
    
    def update(self, dt: float, enemy_group=None, building_group=None, survivor_group=None):
        """Update arrow projectile position and check collisions"""
        if not self.active:
            return
        
        # Update animation
        if self.arrow_frames:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_delay:
                self.animation_timer = 0.0
                self.frame_index = (self.frame_index + 1) % len(self.arrow_frames)
                # Redraw with new frame
                self.draw_projectile()
        
        # Move projectile
        self.pos += self.velocity * dt
        self.rect.center = self.pos
        
        # Check collision based on target type
        if self.target_type == "enemy":
            # Check collision with enemies
            if enemy_group:
                for enemy in enemy_group:
                    if enemy.alive and self.rect.colliderect(enemy.rect):
                        enemy.take_damage(self.damage)
                        self.hit = True
                        self.active = False
                        return
        elif self.target_type == "building":
            # Check collision with buildings
            if building_group:
                for building in building_group:
                    if (hasattr(building, 'state') and 
                        building.state != "destroyed" and
                        self.rect.colliderect(building.rect)):
                        if hasattr(building, 'take_damage'):
                            world = getattr(self, 'world', None)
                            building.take_damage(self.damage, world)
                        self.hit = True
                        self.active = False
                        return
        elif self.target_type == "survivor":
            # Check collision with survivors
            if survivor_group:
                for survivor in survivor_group:
                    if survivor.alive and self.rect.colliderect(survivor.rect):
                        survivor.take_damage(self.damage)
                        self.hit = True
                        self.active = False
                        return
        
        # Check if projectile has traveled too far (despawn after range)
        distance_traveled = (self.pos - self.start_pos).length()
        if distance_traveled > 500:  # Max range
            self.active = False
        
        # Check if out of bounds
        if self.pos.x < 0 or self.pos.x > 1920 or self.pos.y < 0 or self.pos.y > 1080:
            self.active = False


class FlameBullet(Projectile):
    """Flame projectile with sprite animation for flamethrower turret"""
    
    # Class-level sprite sheet (set from main.py after loading)
    sprite_sheet = None
    
    def __init__(self, start_pos: Tuple[float, float], target_pos: Tuple[float, float], 
                 speed: float = 300.0, damage: int = 8, target_type: str = "enemy"):
        # Initialize bullet_frames before calling super() to avoid AttributeError
        self.bullet_frames = []
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.05  # seconds per frame (fast animation)
        
        # Call parent init (which will call draw_projectile, but bullet_frames exists now)
        super().__init__(start_pos, target_pos, speed, damage, target_type)
        
        # Load bullet frames if sprite sheet provided
        if FlameBullet.sprite_sheet:
            self.load_flame_frames()
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
    
    def load_flame_frames(self):
        """Load all flame bullet frames from sprite sheet"""
        if not FlameBullet.sprite_sheet:
            return
        
        frame_size = 16  # Each frame is 16x16 pixels
        scaled_size = int(frame_size * 1.2)  # Scale to 1.2x (19 pixels)
        sheet_width = FlameBullet.sprite_sheet.get_width()
        num_frames = sheet_width // frame_size  # Should be 4 frames
        
        self.bullet_frames = []
        for i in range(num_frames):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            if frame_rect.right <= sheet_width:
                frame = FlameBullet.sprite_sheet.subsurface(frame_rect)
                # Scale the frame to 1.2x size
                scaled_frame = pygame.transform.scale(frame, (scaled_size, scaled_size))
                self.bullet_frames.append(scaled_frame)
            else:
                # Create placeholder if frame doesn't exist
                placeholder = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                placeholder.fill((255, 100, 0, 128))  # Orange/red placeholder
                self.bullet_frames.append(placeholder)
    
    def draw_projectile(self):
        """Draw the flame bullet with rotation"""
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
            pygame.draw.circle(self.image, (255, 100, 0), (9, 9), 4)
            pygame.draw.circle(self.image, (255, 200, 0), (9, 9), 2)
    
    def update(self, dt: float, enemy_group=None, building_group=None):
        """Update flame bullet position and check collisions"""
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
        
        # Move projectile
        self.pos += self.velocity * dt
        # Update rect center to match position (after rotation, rect size may have changed)
        self.rect = self.image.get_rect(center=self.pos)
        
        # Check collision based on target type
        if self.target_type == "enemy":
            # Check collision with enemies (turret projectiles)
            if enemy_group:
                for enemy in enemy_group:
                    if enemy.alive and self.rect.colliderect(enemy.rect):
                        # Hit enemy
                        world = getattr(self, 'world', None)
                        effective_damage = self.damage
                        if world and hasattr(world, 'modifiers'):
                            armor_pierce_mult = world.modifiers.get("enemy_armor_pierce_mult", 1.0)
                            effective_damage = int(self.damage * armor_pierce_mult)
                        enemy.take_damage(effective_damage)
                        self.hit = True
                        self.active = False
                        return
        
        # Check if projectile has traveled too far (despawn after range)
        distance_traveled = (self.pos - self.start_pos).length()
        if distance_traveled > 500:  # Max range
            self.active = False
        
        # Check if out of bounds
        if self.pos.x < 0 or self.pos.x > 1920 or self.pos.y < 0 or self.pos.y > 1080:
            self.active = False
