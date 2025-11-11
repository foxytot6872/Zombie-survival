import pygame 

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self, surface):
        """Draw the button and return True if clicked"""
        action = False
        mouse_pos = pygame.mouse.get_pos()
        
        # Check if mouse is over button
        if self.rect.collidepoint(mouse_pos):
            # Check if mouse button is pressed
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                action = True
        
        # Reset clicked state when mouse button is released
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # Draw the button
        surface.blit(self.image, self.rect)
        
        return action