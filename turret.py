import pygame 
import constants as c

class Turret(pygame.sprite.Sprite):
    def __init__(self, position, sprite_sheet, base_image):
        self.cooldown = 1500
        self.range = 90
        pygame.sprite.Sprite.__init__(self)
        self.angle = 0
        self.base_image = base_image
        self.selected = False
        
        #animation
        self.sprite_sheet = sprite_sheet
        self.animation_list = self.load_image()
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.last_shot = pygame.time.get_ticks()
        
        # Store the current turret image
        self.turret_image = self.animation_list[self.frame_index]
        
        # Set up rect using base image for positioning/collision
        base_rect = self.base_image.get_rect()
        turret_rect = self.turret_image.get_rect()
        # Use the larger dimensions for collision rect
        self.rect = pygame.Rect(0, 0, max(base_rect.width, turret_rect.width), max(base_rect.height, turret_rect.height))
        self.rect.center = position
        
        # Create range circle after rect is set
        self.create_range_circle()

    def create_range_circle(self):
        """Create a semi-transparent circle to show turret range"""
        # Create a surface for the range circle
        self.range_image = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        # Draw a circle (x, y, radius) - center it on the surface
        pygame.draw.circle(self.range_image, (100, 100, 100, 100), (self.range, self.range), self.range)
        # Set up rect for positioning
        self.range_rect = self.range_image.get_rect()
        self.range_rect.center = self.rect.center
    
    def update_range_position(self):
        """Update range circle position to match turret position"""
        self.range_rect.center = self.rect.center

    def load_image(self):
        size = self.sprite_sheet.get_height()
        animation_list = []
        for x in range (c.ANIMATION_STEPS):
            temp_img = self.sprite_sheet.subsurface(x*size, 0 , size, size)
            animation_list.append(temp_img)
        return animation_list

    def play_animation(self):
        # Update which frame we're using
        if pygame.time.get_ticks() - self.update_time > c.ANIMATION_DELAY:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            if self.frame_index >= len(self.animation_list):
                self.frame_index = 0
                self.last_shot = pygame.time.get_ticks()
        
        # Update the stored turret image
        self.turret_image = self.animation_list[self.frame_index]

    def get_rotated_turret(self):
        """Get the current turret frame rotated by self.angle"""
        current_frame = self.animation_list[self.frame_index]
        rotated_image = pygame.transform.rotate(current_frame, -self.angle)
        return rotated_image

    def draw(self, screen):
        """Draw the base and rotated turret separately"""
        # Update range circle position
        self.update_range_position()
        
        # Draw range circle first (if selected) - behind everything
        if self.selected:
            screen.blit(self.range_image, self.range_rect)
        
        # Get the rotated turret image
        rotated_turret = self.get_rotated_turret()
        
        # Get rects for positioning
        base_rect = self.base_image.get_rect()
        turret_rect = rotated_turret.get_rect()
        
        # Center both rects on self.rect.center
        base_rect.center = self.rect.center
        turret_rect.center = self.rect.center
        
        # Draw base first (bottom layer)
        screen.blit(self.base_image, base_rect)
        
        # Draw rotated turret on top
        screen.blit(rotated_turret, turret_rect)

    def update(self):
        if pygame.time.get_ticks() - self.last_shot > self.cooldown:
            self.play_animation()

    @staticmethod
    def create_turret(position, sprite_sheet, base_image, turret_group):
        turret = Turret(position, sprite_sheet, base_image)
        turret_group.add(turret)
        return turret