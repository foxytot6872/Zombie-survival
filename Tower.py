import pygame as pg
import math
import os

class Tower(pg.sprite.Sprite):
    # Class variables to store loaded images (dictionary by tier)
    base_images = {}  # {1: image, 2: image, 3: image}
    head_images = {}  # {1: image, 2: image, 3: image}
    
    @classmethod
    def load_images(cls, tier=1):
        """Load tower images for a specific tier"""
        if tier in cls.base_images and tier in cls.head_images:
            return  # Already loaded
        
        try:
            # Try to load PNG exports for the tier
            base_path = os.path.join("asset", f"Base_lv{tier}.png")
            head_path = os.path.join("asset", f"Turret_lv{tier}.png")
            
            # Load base image
            if os.path.exists(base_path):
                cls.base_images[tier] = pg.image.load(base_path).convert_alpha()
            else:
                # Fallback: use lv1 base if available, otherwise create simple base
                if 1 in cls.base_images:
                    cls.base_images[tier] = cls.base_images[1].copy()
                elif tier == 1:
                    cls.base_images[tier] = pg.Surface((40, 40), pg.SRCALPHA)
                    pg.draw.circle(cls.base_images[tier], (100, 100, 100), (20, 20), 18)
                    pg.draw.circle(cls.base_images[tier], (80, 80, 80), (20, 20), 15)
                else:
                    # For higher tiers, try to load lv1 first
                    lv1_base_path = os.path.join("asset", "Base_lv1.png")
                    if os.path.exists(lv1_base_path):
                        cls.base_images[1] = pg.image.load(lv1_base_path).convert_alpha()
                        cls.base_images[tier] = cls.base_images[1].copy()
                    else:
                        cls.base_images[tier] = pg.Surface((40, 40), pg.SRCALPHA)
                        pg.draw.circle(cls.base_images[tier], (100, 100, 100), (20, 20), 18)
                        pg.draw.circle(cls.base_images[tier], (80, 80, 80), (20, 20), 15)
            
            # Load head image
            if os.path.exists(head_path):
                cls.head_images[tier] = pg.image.load(head_path).convert_alpha()
            else:
                # Fallback: use lower tier if available, otherwise create simple turret head
                if 1 in cls.head_images:
                    cls.head_images[tier] = cls.head_images[1].copy()
                elif tier == 1:
                    cls.head_images[tier] = pg.Surface((30, 30), pg.SRCALPHA)
                    pg.draw.circle(cls.head_images[tier], (150, 150, 150), (15, 15), 12)
                    pg.draw.rect(cls.head_images[tier], (200, 200, 200), (12, 0, 6, 15))
                else:
                    # For higher tiers, try to load lv1 first
                    lv1_head_path = os.path.join("asset", "Turret_lv1.png")
                    if os.path.exists(lv1_head_path):
                        cls.head_images[1] = pg.image.load(lv1_head_path).convert_alpha()
                        cls.head_images[tier] = cls.head_images[1].copy()
                    else:
                        cls.head_images[tier] = pg.Surface((30, 30), pg.SRCALPHA)
                        pg.draw.circle(cls.head_images[tier], (150, 150, 150), (15, 15), 12)
                        pg.draw.rect(cls.head_images[tier], (200, 200, 200), (12, 0, 6, 15))
        except Exception as e:
            print(f"Error loading tower images for tier {tier}: {e}")
            # Create fallback images
            if tier not in cls.base_images:
                cls.base_images[tier] = pg.Surface((40, 40), pg.SRCALPHA)
                pg.draw.circle(cls.base_images[tier], (100, 100, 100), (20, 20), 18)
            if tier not in cls.head_images:
                cls.head_images[tier] = pg.Surface((30, 30), pg.SRCALPHA)
                pg.draw.circle(cls.head_images[tier], (150, 150, 150), (15, 15), 12)
    
    def __init__(self, pos, damage=25, range=150, fire_rate=30, cost=50, tier=1):
        pg.sprite.Sprite.__init__(self)
        
        self.tier = tier
        
        # Load images for this tier if not already loaded
        Tower.load_images(tier)
        
        # Get images for this tier (fallback to tier 1 if not available)
        if tier in Tower.base_images:
            self.base_img = Tower.base_images[tier]
        elif 1 in Tower.base_images:
            self.base_img = Tower.base_images[1]
        else:
            # Should not happen, but create fallback
            self.base_img = pg.Surface((40, 40), pg.SRCALPHA)
            pg.draw.circle(self.base_img, (100, 100, 100), (20, 20), 18)
        
        if tier in Tower.head_images:
            self.head_img_original = Tower.head_images[tier]
        elif 1 in Tower.head_images:
            self.head_img_original = Tower.head_images[1]
        else:
            # Should not happen, but create fallback
            self.head_img_original = pg.Surface((30, 30), pg.SRCALPHA)
            pg.draw.circle(self.head_img_original, (150, 150, 150), (15, 15), 12)
        
        # Create a surface for the combined tower (base + head)
        # Use the larger dimension to ensure head fits when rotated
        max_size = max(self.base_img.get_width(), self.base_img.get_height(),
                      self.head_img_original.get_width(), self.head_img_original.get_height())
        self.image = pg.Surface((max_size * 2, max_size * 2), pg.SRCALPHA)
        
        self.rect = self.image.get_rect()
        self.rect.center = pos
        
        # Store the center offset for drawing
        self.image_center = (max_size, max_size)
        
        self.damage = damage
        self.range = range
        self.fire_rate = fire_rate  # Frames between shots
        self.fire_timer = fire_rate  # Start ready to fire
        self.cost = cost
        self.target = None
        self.angle = 0  # Current rotation angle in degrees
        # Offset to account for turret image's default orientation
        # Common values: 0 (points right), 90 (points up), -90 (points down), 180 (points left)
        # Adjust this value to match your turret image's default pointing direction
        self.angle_offset = 90  # Assuming turret points up by default
        self.rotation_direction = -1  # 1 for normal rotation, -1 to reverse (try both if needed)
    
    def update(self, enemies):
        # Increment fire timer
        self.fire_timer += 1
        
        # Find closest enemy in range
        closest_enemy = None
        closest_distance = self.range
        
        for enemy in enemies:
            dx = enemy.rect.centerx - self.rect.centerx
            dy = enemy.rect.centery - self.rect.centery
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < closest_distance:
                closest_distance = distance
                closest_enemy = enemy
        
        self.target = closest_enemy
        
        # Update rotation angle to face target
        if self.target:
            # Calculate vector from tower to enemy
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            
            # Calculate angle using atan2 (handles all quadrants correctly)
            # atan2(dy, dx) returns angle in radians
            # In pygame coordinates (y increases downward):
            #   0° = right (east), 90° = down (south), -90° = up (north), ±180° = left (west)
            angle_rad = math.atan2(dy, dx)
            
            # Convert to degrees
            angle_deg = math.degrees(angle_rad)
            
            # Account for turret image's default orientation
            # If image points right (0°) by default: use angle_deg directly
            # If image points up (-90° in atan2) by default: subtract -90° = add 90°
            # The offset allows fine-tuning based on actual image orientation
            self.angle = angle_deg + self.angle_offset
        
        # Fire at target if ready
        if self.target and self.fire_timer >= self.fire_rate:
            self.fire_timer = 0
            return True  # Signal to create bullet
        
        return False
    
    def draw(self, screen):
        """Custom draw method to render base and rotating head"""
        # Clear the image
        self.image.fill((0, 0, 0, 0))
        
        # Draw base (static, centered)
        base_rect = self.base_img.get_rect(center=self.image_center)
        self.image.blit(self.base_img, base_rect)
        
        # Rotate head to face target
        if self.target:
            # Rotate the head image to face the target
            # pygame.transform.rotate rotates counter-clockwise
            # Apply rotation with direction multiplier (allows easy reversal if needed)
            rotation_angle = self.angle * self.rotation_direction
            rotated_head = pg.transform.rotate(self.head_img_original, rotation_angle)
            
            # Get the rect of the rotated image and center it
            # This is important because rotated images can have different dimensions
            head_rect = rotated_head.get_rect(center=self.image_center)
            self.image.blit(rotated_head, head_rect)
        else:
            # Draw head at default angle if no target
            head_rect = self.head_img_original.get_rect(center=self.image_center)
            self.image.blit(self.head_img_original, head_rect)
        
        # Draw to screen
        screen.blit(self.image, self.rect)
    
    def get_angle_to_target(self):
        """Get angle to current target in radians"""
        if not self.target:
            return 0
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        return math.atan2(dy, dx)
    
    def draw_range(self, screen):
        """Draw range circle (for debugging/placement)"""
        pg.draw.circle(screen, (255, 255, 255, 50), self.rect.center, self.range, 1)

