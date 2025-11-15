"""
Game over screen for win/lose conditions.
"""
import pygame
from typing import Optional, Callable
from core.game_state import GameState

class GameOverScreen:
    """Game over screen UI"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080, font_large=None, font_medium=None, font_small=None):
        """
        Initialize game over screen.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            font_large: Optional pygame.font.Font for large text (defaults to system font)
            font_medium: Optional pygame.font.Font for medium text (defaults to system font)
            font_small: Optional pygame.font.Font for small text (defaults to system font)
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = font_large if font_large else pygame.font.Font(None, 72)
        self.font_medium = font_medium if font_medium else pygame.font.Font(None, 48)
        self.font_small = font_small if font_small else pygame.font.Font(None, 32)
        
        self.is_visible = False
        self.game_state = None
        self.stats = {}
        self.on_restart: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
        
    def show(self, game_state: GameState, stats: dict):
        """Show game over screen"""
        self.is_visible = True
        self.game_state = game_state
        self.stats = stats
    
    def hide(self):
        """Hide game over screen"""
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
            if event.key == pygame.K_r:
                # Restart
                if self.on_restart:
                    self.on_restart()
                return True
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                # Quit
                if self.on_quit:
                    self.on_quit()
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface, show_ui_rectangles: bool = False):
        """Draw game over screen"""
        if not self.is_visible:
            return
        
        # Dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # DEBUG: Draw overlay rectangle for game over panel (~800x600, center)
        if show_ui_rectangles:
            panel_width = 800
            panel_height = 600
            panel_x = (self.screen_width - panel_width) // 2
            panel_y = (self.screen_height - panel_height) // 2
            panel_overlay = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            panel_overlay.fill((255, 128, 128, 100))  # Light red overlay
            surface.blit(panel_overlay, (panel_x, panel_y))
        
        # Determine title and color
        if self.game_state == GameState.WIN:
            title = "VICTORY!"
            title_color = (0, 255, 0)
        else:
            title = "GAME OVER"
            title_color = (255, 0, 0)
        
        # Draw title
        title_surface = self.font_large.render(title, True, title_color)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 200))
        surface.blit(title_surface, title_rect)
        
        # Draw stats
        y_offset = self.screen_height // 2 - 100
        line_height = 40
        
        stats_texts = [
            f"Nights Survived: {self.stats.get('nights', 0)}",
            f"Enemies Killed: {self.stats.get('enemies_killed', 0)}",
            f"Buildings Built: {self.stats.get('buildings_built', 0)}",
        ]
        
        for text in stats_texts:
            stat_surface = self.font_medium.render(text, True, (255, 255, 255))
            stat_rect = stat_surface.get_rect(center=(self.screen_width // 2, y_offset))
            surface.blit(stat_surface, stat_rect)
            y_offset += line_height
        
        # Draw instructions
        y_offset += 40
        instructions = [
            "Press R to Restart",
            "Press ESC or Q to Quit"
        ]
        
        for text in instructions:
            inst_surface = self.font_small.render(text, True, (200, 200, 200))
            inst_rect = inst_surface.get_rect(center=(self.screen_width // 2, y_offset))
            surface.blit(inst_surface, inst_rect)
            y_offset += line_height

