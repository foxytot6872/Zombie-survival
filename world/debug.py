"""
Debug system for development and testing.
"""
import pygame
from typing import Dict, Optional, Tuple

class DebugSystem:
    """Debug system for game development"""
    
    def __init__(self):
        self.active = False
        self.font = pygame.font.Font(None, 20)
        self.debug_info = {}
        self.show_cursor_pos = True
        self.show_fps = True
        self.show_counts = True
        
        # Debug actions (key -> function)
        self.actions = {}
    
    def toggle(self):
        """Toggle debug mode on/off"""
        self.active = not self.active
        return self.active
    
    def is_active(self) -> bool:
        """Check if debug mode is active"""
        return self.active
    
    def register_action(self, key: int, action_name: str, callback):
        """Register a debug action"""
        self.actions[key] = {
            'name': action_name,
            'callback': callback
        }
    
    def handle_key(self, key: int, *args, **kwargs):
        """Handle a keypress in debug mode"""
        if not self.active:
            return False
        
        if key in self.actions:
            action = self.actions[key]
            try:
                action['callback'](*args, **kwargs)
                return True
            except Exception as e:
                print(f"Debug action error: {e}")
                return False
        
        return False
    
    def update_info(self, key: str, value):
        """Update debug info to display"""
        self.debug_info[key] = value
    
    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int], fps: float):
        """Draw debug overlay"""
        if not self.active:
            return
        
        # Get screen dimensions
        screen_height = surface.get_height()
        
        # Use smaller font for compact display
        small_font = pygame.font.Font(None, 18)
        line_height = 18
        padding = 10
        
        # Calculate how much space we need
        # Title: 1, Cursor: 1, FPS: 1, Debug info: variable, Actions header: 1, Actions: 14
        # Estimate max debug info items: ~12
        max_info_items = max(len(self.debug_info), 12)
        estimated_height = (1 + 1 + 1 + max_info_items + 1 + 14) * line_height + padding * 6
        
        # Position panel at top-left, ensure it fits on screen
        panel_x = 10
        panel_y = 10
        panel_width = 320
        panel_height = min(estimated_height, screen_height - panel_y - 10)
        
        # Background for debug info
        debug_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        debug_bg.fill((0, 0, 0, 200))
        surface.blit(debug_bg, (panel_x, panel_y))
        
        y_offset = panel_y + padding
        x_offset = panel_x + padding
        
        # Title
        title = self.font.render("DEBUG MODE", True, (255, 255, 0))
        surface.blit(title, (x_offset, y_offset))
        y_offset += line_height + 3
        
        # Cursor position
        if self.show_cursor_pos:
            cursor_text = small_font.render(
                f"Cursor: ({mouse_pos[0]}, {mouse_pos[1]})",
                True, (255, 255, 255)
            )
            surface.blit(cursor_text, (x_offset, y_offset))
            y_offset += line_height
        
        # FPS
        if self.show_fps:
            fps_text = small_font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
            surface.blit(fps_text, (x_offset, y_offset))
            y_offset += line_height
        
        # Debug info (limit to fit on screen)
        if self.debug_info:
            y_offset += 3
            info_items = list(self.debug_info.items())
            max_info_lines = (panel_height - (y_offset - panel_y) - 80) // line_height  # Reserve space for actions
            for i, (key, value) in enumerate(info_items[:max_info_lines]):
                # Truncate long values if needed
                value_str = str(value)
                if len(value_str) > 25:
                    value_str = value_str[:22] + "..."
                info_text = small_font.render(f"{key}: {value_str}", True, (200, 200, 200))
                surface.blit(info_text, (x_offset, y_offset))
                y_offset += line_height
                if y_offset + line_height * 15 > panel_y + panel_height:  # Stop if we're running out of space
                    break
        
        # Debug actions help
        y_offset += 5
        help_title = small_font.render("Actions:", True, (255, 255, 0))
        surface.blit(help_title, (x_offset, y_offset))
        y_offset += line_height
        
        # List available actions (two columns to save space)
        action_list = [
            ("F1", "+100 Res"),
            ("F2", "Instant Build"),
            ("F3", "Spawn @ Mouse"),
            ("F4", "Clear Enemies"),
            ("F5", "Clear Buildings"),
            ("F6", "Toggle Spawner"),
            ("F7", "Kill All"),
            ("F8", "Complete All"),
            ("1", "+100 Coins"),
            ("2", "Unlock Research"),
            ("3", "Roll Event"),
            ("F9", "Skip Night"),
            ("F10", "Skip Summary"),
            ("F11", "Cycle Diff"),
        ]
        
        # Draw in two columns (split list in half)
        col1_x = x_offset
        col2_x = x_offset + 160
        col1_y = y_offset
        col2_y = y_offset
        
        mid_point = (len(action_list) + 1) // 2  # Split roughly in half
        
        for i, (key, desc) in enumerate(action_list):
            if i < mid_point:
                # Left column
                help_text = small_font.render(f"{key}: {desc}", True, (150, 150, 150))
                surface.blit(help_text, (col1_x, col1_y))
                col1_y += line_height
            else:
                # Right column
                help_text = small_font.render(f"{key}: {desc}", True, (150, 150, 150))
                surface.blit(help_text, (col2_x, col2_y))
                col2_y += line_height

