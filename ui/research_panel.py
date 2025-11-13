"""
Research panel UI component.
"""
import pygame
from typing import Optional

class ResearchPanel:
    """Panel for displaying and purchasing research items."""
    
    def __init__(self, world, research_manager, screen_width: int = 1920, screen_height: int = 1080):
        """
        Initialize research panel.
        Args:
            world: World object
            research_manager: ResearchManager instance
            screen_width: Screen width
            screen_height: Screen height
        """
        self.world = world
        self.research = research_manager
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        
        # Panel dimensions
        panel_width = 600
        panel_height = 500
        panel_x = (screen_width - panel_width) // 2
        panel_y = (screen_height - panel_height) // 2
        self.rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 24)
        
        # Store button rects for click detection
        self.button_rects = {}
    
    def toggle(self):
        """Toggle panel visibility."""
        self.visible = not self.visible
    
    def hide(self):
        """Hide the panel."""
        self.visible = False
    
    def draw(self, screen: pygame.Surface):
        """Draw the research panel."""
        if not self.visible:
            return
        
        # Draw semi-transparent background overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Draw panel background
        panel_bg = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel_bg.fill((40, 40, 40, 240))
        screen.blit(panel_bg, self.rect)
        
        # Draw panel border
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 3)
        
        # Draw title
        title = self.font_large.render("Research", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self.rect.centerx, y=self.rect.y + 20)
        screen.blit(title, title_rect)
        
        # Draw coins display
        coins_text = f"Coins: {self.world.resources.coins}"
        coins_surface = self.font_medium.render(coins_text, True, (255, 215, 0))
        screen.blit(coins_surface, (self.rect.x + 20, self.rect.y + 60))
        
        # Draw research items
        y_offset = self.rect.y + 100
        item_spacing = 60
        self.button_rects = {}
        
        for key, data in self.research.research_defs.items():
            name = data.get("name", key)
            cost = data.get("cost_coins", 0)
            
            # Check if this research is already purchased
            is_unlocked = self.research.is_research_purchased(key)
            
            # Determine color based on unlock status
            if is_unlocked:
                text_color = (120, 255, 120)  # Green for unlocked
            elif self.research.can_research(key):
                text_color = (255, 255, 255)  # White if can afford
            else:
                text_color = (150, 150, 150)  # Gray if can't afford
            
            # Draw research name and cost
            text = f"{name} - {cost} coins"
            label = self.font_medium.render(text, True, text_color)
            screen.blit(label, (self.rect.x + 30, y_offset))
            
            # Draw unlock button (if not already unlocked)
            if not is_unlocked:
                btn_rect = pygame.Rect(self.rect.x + 400, y_offset - 5, 120, 35)
                
                # Button color based on affordability
                if self.research.can_research(key):
                    btn_color = (80, 150, 80)  # Green if can afford
                else:
                    btn_color = (80, 80, 80)  # Gray if can't afford
                
                pygame.draw.rect(screen, btn_color, btn_rect)
                pygame.draw.rect(screen, (200, 200, 200), btn_rect, 2)
                
                btn_label = self.font_small.render("Unlock", True, (255, 255, 255))
                btn_label_rect = btn_label.get_rect(center=btn_rect.center)
                screen.blit(btn_label, btn_label_rect)
                
                # Store for click detection
                self.button_rects[key] = btn_rect
            else:
                # Show "Unlocked" text
                unlocked_label = self.font_small.render("Unlocked", True, (120, 255, 120))
                screen.blit(unlocked_label, (self.rect.x + 400, y_offset))
            
            y_offset += item_spacing
        
        # Draw close hint
        close_text = "Press ESC or click outside to close"
        close_surface = self.font_small.render(close_text, True, (150, 150, 150))
        close_rect = close_surface.get_rect(centerx=self.rect.centerx, y=self.rect.bottom - 30)
        screen.blit(close_surface, close_rect)
    
    def handle_click(self, mouse_pos: tuple) -> bool:
        """
        Handle mouse click on panel.
        Args:
            mouse_pos: Mouse position (x, y)
        Returns:
            True if click was handled, False otherwise
        """
        if not self.visible:
            return False
        
        # Check if clicking outside panel (close it)
        if not self.rect.collidepoint(mouse_pos):
            self.hide()
            return True
        
        # Check research unlock buttons
        for key, btn_rect in self.button_rects.items():
            if btn_rect.collidepoint(mouse_pos):
                success = self.research.unlock(key)
                if success:
                    # Research unlocked - trigger button rebuild in main.py
                    # This will be handled by checking if buttons need rebuilding
                    pass
                else:
                    # Could play a sound or show message here
                    pass
                return True
        
        return False
    
    def handle_key(self, key) -> bool:
        """
        Handle keyboard input.
        Args:
            key: Key code (e.g., pygame.K_ESCAPE)
        Returns:
            True if key was handled, False otherwise
        """
        if key == pygame.K_ESCAPE and self.visible:
            self.hide()
            return True
        return False

