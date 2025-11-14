"""
Research button UI component.
"""
import pygame
import os

class ResearchButton:
    """Button to open the research panel."""
    
    def __init__(self, x: int, y: int, width: int, height: int, callback):
        """
        Initialize research button.
        Args:
            x: X position
            y: Y position
            width: Button width (ignored if image loaded)
            height: Button height (ignored if image loaded)
            callback: Function to call when clicked
        """
        self.callback = callback
        self.image = None
        
        # Try to load research_button.png
        image_paths = [
            'asset/research_button.png',
            'asset/Research_button.png',
            'asset/Research_Button.png'
        ]
        
        for path in image_paths:
            if os.path.exists(path):
                try:
                    self.image = pygame.image.load(path).convert_alpha()
                    # Use image size for rect
                    img_width, img_height = self.image.get_size()
                    self.rect = pygame.Rect(x, y, img_width, img_height)
                    break
                except Exception as e:
                    print(f"Warning: Could not load {path}: {e}")
                    continue
        
        # Fallback: create placeholder if image not found
        if self.image is None:
            print("Warning: research_button.png not found, using placeholder")
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            self.image.fill((60, 60, 60))
            pygame.draw.rect(self.image, (200, 200, 200), (0, 0, width, height), 2)
            # Draw text on placeholder
            font = pygame.font.Font(None, 32)
            label = font.render("Research", True, (255, 255, 255))
            label_rect = label.get_rect(center=(width // 2, height // 2))
            self.image.blit(label, label_rect)
            self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, screen: pygame.Surface):
        """Draw the research button."""
        if self.image:
            screen.blit(self.image, self.rect)
    
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

