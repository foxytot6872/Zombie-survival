"""
Pause menu UI.
"""
import pygame
from typing import Optional, Callable

class PauseMenu:
    """Pause menu UI"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        """
        Initialize pause menu.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        
        self.is_visible = False
        self.selected_option = 0
        self.options = [
            "Restart",
            "Quit"
        ]
        
        self.on_restart: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
        self.on_resume: Optional[Callable] = None  # For ESC key to resume
    
    def show(self):
        """Show pause menu"""
        self.is_visible = True
        self.selected_option = 0
    
    def hide(self):
        """Hide pause menu"""
        self.is_visible = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle event.
        Returns:
            True if event was handled, False otherwise
        """
        if not self.is_visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Resume
                if self.on_resume:
                    self.on_resume()
                return True
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                # Move selection up
                self.selected_option = (self.selected_option - 1) % len(self.options)
                return True
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                # Move selection down
                self.selected_option = (self.selected_option + 1) % len(self.options)
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Select option
                option = self.options[self.selected_option]
                if option == "Restart" and self.on_restart:
                    self.on_restart()
                elif option == "Quit" and self.on_quit:
                    self.on_quit()
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface):
        """Draw pause menu"""
        if not self.is_visible:
            return
        
        # Dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # DEBUG: Draw overlay rectangle for pause menu panel (~600x400, center)
        panel_width = 600
        panel_height = 400
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2
        panel_overlay = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_overlay.fill((128, 128, 255, 100))  # Light blue overlay
        surface.blit(panel_overlay, (panel_x, panel_y))
        
        # DEBUG: Draw overlay rectangles for menu buttons (300x60 each)
        y_offset = self.screen_height // 2 - 50
        option_height = 60
        for i, option in enumerate(self.options):
            button_overlay = pygame.Surface((300, option_height), pygame.SRCALPHA)
            button_overlay.fill((255, 200, 0, 100))  # Orange overlay
            surface.blit(button_overlay, (self.screen_width // 2 - 150, y_offset - 5))
            y_offset += option_height
        
        # Draw title
        title_surface = self.font_large.render("PAUSED", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 200))
        surface.blit(title_surface, title_rect)
        
        # Draw options
        y_offset = self.screen_height // 2 - 50
        option_height = 60
        
        for i, option in enumerate(self.options):
            if i == self.selected_option:
                color = (255, 255, 0)
                # Draw selection indicator
                indicator_rect = pygame.Rect(
                    self.screen_width // 2 - 150,
                    y_offset - 5,
                    300,
                    option_height
                )
                pygame.draw.rect(surface, (100, 100, 100, 128), indicator_rect)
            else:
                color = (255, 255, 255)
            
            option_surface = self.font_medium.render(option, True, color)
            option_rect = option_surface.get_rect(center=(self.screen_width // 2, y_offset))
            surface.blit(option_surface, option_rect)
            y_offset += option_height
        
        # Draw instructions
        inst_text = "Press ESC to Resume | Arrow Keys to Navigate | Enter to Select"
        inst_surface = self.font_medium.render(inst_text, True, (200, 200, 200))
        inst_rect = inst_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 150))
        surface.blit(inst_surface, inst_rect)

