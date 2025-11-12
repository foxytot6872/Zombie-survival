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
        
        # Background for debug info
        debug_bg = pygame.Surface((300, 400), pygame.SRCALPHA)
        debug_bg.fill((0, 0, 0, 180))
        surface.blit(debug_bg, (10, 500))
        
        y_offset = 510
        line_height = 22
        
        # Title
        title = self.font.render("DEBUG MODE", True, (255, 255, 0))
        surface.blit(title, (20, y_offset))
        y_offset += line_height + 5
        
        # Cursor position
        if self.show_cursor_pos:
            cursor_text = self.font.render(
                f"Cursor: ({mouse_pos[0]}, {mouse_pos[1]})",
                True, (255, 255, 255)
            )
            surface.blit(cursor_text, (20, y_offset))
            y_offset += line_height
        
        # FPS
        if self.show_fps:
            fps_text = self.font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
            surface.blit(fps_text, (20, y_offset))
            y_offset += line_height
        
        # Debug info
        if self.debug_info:
            y_offset += 5
            for key, value in self.debug_info.items():
                info_text = self.font.render(f"{key}: {value}", True, (200, 200, 200))
                surface.blit(info_text, (20, y_offset))
                y_offset += line_height
        
        # Debug actions help
        y_offset += 10
        help_title = self.font.render("Debug Actions:", True, (255, 255, 0))
        surface.blit(help_title, (20, y_offset))
        y_offset += line_height
        
        # List available actions
        action_list = [
            ("F1", "Add +100 Resources"),
            ("F2", "Instant Build"),
            ("F3", "Spawn Zombie @ Mouse"),
            ("F4", "Clear All Enemies"),
            ("F5", "Clear All Buildings"),
            ("F6", "Toggle Spawner"),
            ("F7", "Kill All Enemies"),
            ("F8", "Complete All Buildings"),
        ]
        
        for key, desc in action_list:
            help_text = self.font.render(f"{key}: {desc}", True, (150, 150, 150))
            surface.blit(help_text, (25, y_offset))
            y_offset += line_height

