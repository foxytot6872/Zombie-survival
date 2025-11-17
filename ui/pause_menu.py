"""
Pause menu UI.
"""
import pygame
from typing import Optional, Callable

class PauseMenu:
    """Pause menu UI"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080, font_large=None, font_medium=None):
        """
        Initialize pause menu.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            font_large: Optional pygame.font.Font for large text (defaults to system font)
            font_medium: Optional pygame.font.Font for medium text (defaults to system font)
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = font_large if font_large else pygame.font.Font(None, 72)
        self.font_medium = font_medium if font_medium else pygame.font.Font(None, 48)
        self.font_selected = self.font_medium
        
        self.is_visible = False
        self.selected_option = 0
        self.options = [
            "Restart",
            "Quit"
        ]
        
        self.on_restart: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
        self.on_resume: Optional[Callable] = None  # For ESC key to resume
        
        # Optional 9-slice panel renderer (uses 32x32 tiles in asset/hud)
        try:
            from ui.panel import NineSlicePanel
            self.panel_renderer = NineSlicePanel()
        except Exception:
            self.panel_renderer = None
    
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
    
    def draw(self, surface: pygame.Surface, show_ui_rectangles: bool = False):
        """Draw pause menu"""
        if not self.is_visible:
            return
        # Dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # DEBUG: Draw overlay rectangle for pause menu panel (~600x400, center)
        if show_ui_rectangles:
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
        
        # Draw panel using 9-slice tiles if available (snapped to 32px grid)
        menu_width, menu_height = 544, 384  # multiples of 32 for crisp tiling
        menu_x = (self.screen_width - menu_width) // 2
        menu_y = (self.screen_height - menu_height) // 2
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        if self.panel_renderer and self.panel_renderer.is_ready():
            self.panel_renderer.draw(surface, menu_rect)
        else:
            # Basic rectangle fallback
            pygame.draw.rect(surface, (30, 30, 30), menu_rect)
            pygame.draw.rect(surface, (200, 200, 200), menu_rect, 3)
        
        # Draw title centered on the panel
        title_surface = self.font_large.render("PAUSED", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(menu_rect.centerx, menu_rect.y + 60))
        surface.blit(title_surface, title_rect)
        
        # Draw options
        y_offset = menu_rect.centery - 50
        option_height = 60
        
        for i, option in enumerate(self.options):
            is_selected = (i == self.selected_option)
            option_font = self.font_selected if is_selected and self.font_selected else self.font_medium
            if is_selected:
                # Draw selection indicator
                indicator_rect = pygame.Rect(
                    self.screen_width // 2 - 150,
                    y_offset - 5,
                    300,
                    option_height
                )
                pygame.draw.rect(surface, (100, 100, 100, 128), indicator_rect)
            color = (255, 255, 255)
            
            option_surface = option_font.render(option, True, color)
            option_rect = option_surface.get_rect(center=(self.screen_width // 2, y_offset))
            surface.blit(option_surface, option_rect)
            y_offset += option_height
        
        # Draw instructions
        inst_text = "Press ESC to Resume | Arrow Keys to Navigate | Enter to Select"
        inst_surface = self.font_medium.render(inst_text, True, (200, 200, 200))
        inst_rect = inst_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 200))
        surface.blit(inst_surface, inst_rect)

