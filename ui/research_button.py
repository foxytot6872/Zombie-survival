"""
Research button UI component.
"""
import pygame

class ResearchButton:
    """Button to open the research panel."""
    
    def __init__(self, x: int, y: int, width: int, height: int, callback):
        """
        Initialize research button.
        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            callback: Function to call when clicked
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback
        self.text = "Research"
        self.font = pygame.font.Font(None, 32)
    
    def draw(self, screen: pygame.Surface):
        """Draw the research button."""
        # Draw button background
        pygame.draw.rect(screen, (60, 60, 60), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        
        # Draw text
        label = self.font.render(self.text, True, (255, 255, 255))
        label_rect = label.get_rect(center=self.rect.center)
        screen.blit(label, label_rect)
    
    def handle_click(self, mouse_pos: tuple) -> bool:
        """
        Handle mouse click on button.
        Args:
            mouse_pos: Mouse position (x, y)
        Returns:
            True if button was clicked, False otherwise
        """
        if self.rect.collidepoint(mouse_pos):
            self.callback()
            return True
        return False

