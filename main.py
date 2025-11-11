import pygame
import constants as c
from turret import Turret
from button import Button

# pygame setup
pygame.init()

FPS = 60

screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
pygame.display.set_caption("Zombie Defense")
clock = pygame.time.Clock()
running = True

###################
# Load images
###################
# Turret images
turret_base = pygame.image.load('asset/Base_lv1.png').convert_alpha()
turret_sheet = pygame.image.load('asset/Turret_lv1.png').convert_alpha()

# Button image
try:
    build_turret_image = pygame.image.load('asset/Build_turret_button.png').convert_alpha()
except:
    # If button image doesn't exist, create a simple colored rectangle
    build_turret_image = pygame.Surface((100, 50))
    build_turret_image.fill((100, 150, 100))
    font = pygame.font.Font(None, 24)
    text = font.render("BUILD", True, (255, 255, 255))
    text_rect = text.get_rect(center=(50, 25))
    build_turret_image.blit(text, text_rect)

###################
# Game state
###################
turret_group = pygame.sprite.Group()
build_mode = False  # True when player wants to build a turret
selected_turret = None  # Currently selected turret

###################
# Create button
###################
turret_button = Button(10, 10, build_turret_image)

###################
# Helper functions
###################
def can_place_turret(position, turret_group):
    """Check if a turret can be placed at the given position"""
    # Check if position is within screen bounds
    if position[0] < 0 or position[0] > c.SCREEN_WIDTH or position[1] < 0 or position[1] > c.SCREEN_HEIGHT:
        return False
    
    # Create a temporary rect to check collisions
    temp_rect = turret_base.get_rect()
    temp_rect.center = position
    
    # Check if it collides with any existing turret
    for turret in turret_group:
        if temp_rect.colliderect(turret.rect):
            return False
    
    return True

def draw_preview(screen, position, can_place):
    """Draw a preview rectangle showing where the turret will be placed"""
    # Get the base image dimensions
    preview_rect = turret_base.get_rect()
    preview_rect.center = position
    
    # Choose color based on whether placement is valid
    if can_place:
        color = (0, 255, 0, 100)  # Green with transparency
    else:
        color = (255, 0, 0, 100)  # Red with transparency
    
    # Create a semi-transparent surface
    preview_surface = pygame.Surface((preview_rect.width, preview_rect.height), pygame.SRCALPHA)
    preview_surface.fill(color)
    
    # Draw the preview
    screen.blit(preview_surface, preview_rect)
    
    if can_place:
        outline_color = (0, 255, 0)
    else:
        outline_color = (255, 0, 0)
    pygame.draw.rect(screen, outline_color, preview_rect, 2)

def select_turret(mouse_pos, turret_group):
    """Select a turret at the mouse position"""
    global selected_turret
    
    # Deselect all turrets first
    for turret in turret_group:
        turret.selected = False
    selected_turret = None
    
    # Check if mouse is over any turret
    for turret in turret_group:
        if turret.rect.collidepoint(mouse_pos):
            turret.selected = True
            selected_turret = turret
            return True
    
    return False

###################
# Main game loop
###################
while running:
    clock.tick(FPS)
    
    # Fill screen with black
    screen.fill((0, 0, 0))
    
    ###################
    # Handle button click
    ###################
    if turret_button.draw(screen):
        build_mode = not build_mode  # Toggle build mode
        # Deselect any selected turret when entering build mode
        if build_mode:
            if selected_turret:
                selected_turret.selected = False
                selected_turret = None
    
    ###################
    # Update and draw turrets
    ###################
    for turret in turret_group:
        turret.play_animation()
        turret.draw(screen)
    
    ###################
    # Draw preview when in build mode
    ###################
    if build_mode:
        mouse_pos = pygame.mouse.get_pos()
        can_place = can_place_turret(mouse_pos, turret_group)
        draw_preview(screen, mouse_pos, can_place)
    
    ###################
    # Handle events
    ###################
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check if clicking on button (handled above)
            if turret_button.rect.collidepoint(mouse_pos):
                continue
            
            # If in build mode, try to place turret
            if build_mode:
                if can_place_turret(mouse_pos, turret_group):
                    Turret.create_turret(mouse_pos, turret_sheet, turret_base, turret_group)
                    build_mode = False  # Exit build mode after placing
            else:
                # Try to select a turret
                select_turret(mouse_pos, turret_group)
        
        # Press ESC to exit build mode or exit game
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if build_mode:
                    build_mode = False  # Exit build mode
                    if selected_turret:
                        selected_turret.selected = False
                        selected_turret = None
                else:
                    running = False  # Exit game
    
    # Update display
    pygame.display.flip()

pygame.quit()
