"""
Debug system for development and testing.
"""
import math
from collections import deque
from typing import Dict, List, Optional, Tuple

import pygame

class DebugSystem:
    """Debug system for game development"""
    
    def __init__(self):
        self.active = False
        self.font = pygame.font.Font(None, 20)
        self.debug_info = {}
        self.sections: Dict[str, Dict[str, str]] = {}
        self.section_order: List[str] = []
        self.show_cursor_pos = True
        self.show_fps = True
        self.show_counts = True
        self.show_footprints = False  # Toggle for showing building footprints
        self.show_ui_rectangles = False  # Toggle for showing UI element rectangles
        self.toggle_states: Dict[str, bool] = {}
        self.recent_events = deque(maxlen=5)
        
        # Debug actions (key -> function)
        self.actions = {}
        self.virtual_actions: List[Dict[str, str]] = []
    
    def toggle(self):
        """Toggle debug mode on/off"""
        self.active = not self.active
        return self.active
    
    def is_active(self) -> bool:
        """Check if debug mode is active"""
        return self.active
    
    def register_action(
        self,
        key: int,
        action_name: str,
        callback,
        *,
        display_key: Optional[str] = None,
        category: str = "General",
        show_in_help: bool = True,
    ):
        """Register a debug action"""
        key_label = display_key
        if key_label is None:
            try:
                key_label = pygame.key.name(key).upper()
            except pygame.error:
                key_label = f"Key {key}"
        self.actions[key] = {
            'name': action_name,
            'callback': callback,
            'display_key': key_label,
            'category': category,
            'show_in_help': show_in_help,
        }
    
    def register_virtual_action(self, label: str, description: str, category: str = "General"):
        """Register a virtual action for help UI (no callback)."""
        self.virtual_actions.append({
            'display_key': label,
            'name': description,
            'category': category,
        })
    
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
        self.update_section("General", key, value)
    
    def begin_frame(self):
        """Reset per-frame sections and info."""
        self.debug_info.clear()
        self.sections.clear()
        self.section_order.clear()
    
    def update_section(self, section: str, key: str, value):
        """Update info within a named section."""
        if section not in self.sections:
            self.sections[section] = {}
            self.section_order.append(section)
        self.sections[section][key] = str(value)
    
    def set_toggle_state(self, label: str, enabled: bool):
        """Expose toggle state for UI badges."""
        self.toggle_states[label] = bool(enabled)
    
    def log_event(self, message: str):
        """Record a short, recent debug event."""
        if not message:
            return
        self.recent_events.appendleft(message)
    
    def _get_action_help_entries(self) -> List[Dict[str, str]]:
        """Return all help entries including virtual actions."""
        entries: List[Dict[str, str]] = []
        for data in self.actions.values():
            if data.get('show_in_help', True):
                entries.append({
                    'display_key': data.get('display_key', '??'),
                    'name': data.get('name', ''),
                    'category': data.get('category', 'General'),
                })
        entries.extend(self.virtual_actions)
        # Sort by category then label for readability
        return sorted(entries, key=lambda item: (item['category'], item['display_key']))
    
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
        
        # Calculate how much space we need dynamically
        total_lines = 1  # Title
        if self.show_cursor_pos:
            total_lines += 1
        if self.show_fps:
            total_lines += 1
        if self.toggle_states:
            total_lines += 1  # Toggles header
            toggle_lines = math.ceil(len(self.toggle_states) / 2)
            total_lines += toggle_lines
        if self.section_order:
            for section in self.section_order:
                entries = self.sections.get(section, {})
                if entries:
                    total_lines += 1  # section header
                    total_lines += len(entries)
        if self.recent_events:
            total_lines += 1 + len(self.recent_events)
        action_entries = self._get_action_help_entries()
        if action_entries:
            total_lines += 1  # Actions header
            action_lines = math.ceil(len(action_entries) / 2)
            total_lines += action_lines
        
        estimated_height = total_lines * line_height + padding * 4
        
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
        
        # Toggle status badges
        if self.toggle_states:
            toggle_title = small_font.render("Toggles:", True, (255, 255, 0))
            surface.blit(toggle_title, (x_offset, y_offset))
            y_offset += line_height
            
            toggles_per_line = 2
            toggle_items = list(self.toggle_states.items())
            for i in range(0, len(toggle_items), toggles_per_line):
                line_items = toggle_items[i:i + toggles_per_line]
                line_text = "   ".join(
                    f"{name}: {'ON' if state else 'OFF'}"
                    for name, state in line_items
                )
                toggle_text = small_font.render(line_text, True, (180, 180, 180))
                surface.blit(toggle_text, (x_offset, y_offset))
                y_offset += line_height
        
        # Section-based info
        for section in self.section_order:
            entries = self.sections.get(section, {})
            if not entries:
                continue
            section_title = small_font.render(f"{section}:", True, (255, 255, 0))
            surface.blit(section_title, (x_offset, y_offset))
            y_offset += line_height
            for key, value in entries.items():
                value_str = str(value)
                if len(value_str) > 28:
                    value_str = value_str[:25] + "..."
                info_text = small_font.render(f"{key}: {value_str}", True, (200, 200, 200))
                surface.blit(info_text, (x_offset + 8, y_offset))
                y_offset += line_height
                if y_offset >= panel_y + panel_height - line_height * 4:
                    break
        
        # Recent events log
        if self.recent_events:
            events_title = small_font.render("Recent:", True, (255, 255, 0))
            surface.blit(events_title, (x_offset, y_offset))
            y_offset += line_height
            for message in self.recent_events:
                event_text = small_font.render(f"- {message}", True, (180, 180, 180))
                surface.blit(event_text, (x_offset + 8, y_offset))
                y_offset += line_height
                if y_offset >= panel_y + panel_height - line_height * 3:
                    break
        
        # Debug actions help
        if action_entries:
            help_title = small_font.render("Actions:", True, (255, 255, 0))
            surface.blit(help_title, (x_offset, y_offset))
            y_offset += line_height
            
            col_width = 150
            col1_x = x_offset
            col2_x = x_offset + col_width + 10
            col1_y = y_offset
            col2_y = y_offset
            
            mid_point = math.ceil(len(action_entries) / 2)
            
            for i, entry in enumerate(action_entries):
                text = f"{entry['display_key']}: {entry['name']}"
                help_text = small_font.render(text, True, (150, 150, 150))
                if i < mid_point:
                    surface.blit(help_text, (col1_x, col1_y))
                    col1_y += line_height
                else:
                    surface.blit(help_text, (col2_x, col2_y))
                    col2_y += line_height

