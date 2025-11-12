"""
HUD (Heads-Up Display) for game information.
"""
import pygame
from typing import Optional, Dict

class HUD:
    """HUD for displaying game information"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        """
        Initialize HUD.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # HUD elements
        self.day = 1
        self.night = 1
        self.state = "DAY"
        self.wave_info: Dict = {}
        self.hq_hp = 0
        self.hq_max_hp = 2000
        
        # Event banner
        self.event_text = ""
        self.event_timer = 0.0
        self.event_duration = 3.0
        self.event_visible = False
    
    def update(self, dt: float, day: int, night: int, state: str, wave_info: Dict, hq_hp: int = 0, hq_max_hp: int = 2000):
        """Update HUD information"""
        self.day = day
        self.night = night
        self.state = state
        self.wave_info = wave_info
        self.hq_hp = hq_hp
        self.hq_max_hp = hq_max_hp
        
        # Update event banner
        if self.event_visible:
            self.event_timer -= dt
            if self.event_timer <= 0:
                self.event_visible = False
    
    def show_event(self, text: str, duration: float = 3.0):
        """Show event banner"""
        self.event_text = text
        self.event_timer = duration
        self.event_duration = duration
        self.event_visible = True
    
    def show_starting_defenses_hint(self):
        """Show 'Starting Defenses' hint on Day 1"""
        self.show_event("Starting Defenses: Wall, Gate, and Turrets", duration=5.0)
    
    def draw(self, surface: pygame.Surface):
        """Draw HUD"""
        # Draw day/night indicator (top-left)
        state_text = f"Day {self.day} - Night {self.night}"
        if self.state == "DAY":
            state_text += " (Day)"
            state_color = (100, 200, 255)
        elif self.state == "NIGHT":
            state_text += " (Night)"
            state_color = (200, 100, 100)
        else:
            state_text += f" ({self.state})"
            state_color = (200, 200, 200)
        
        state_surface = self.font_large.render(state_text, True, state_color)
        surface.blit(state_surface, (10, 10))
        
        # Draw HQ HP (top-center, important!)
        hq_hp_pct = self.hq_hp / self.hq_max_hp if self.hq_max_hp > 0 else 0.0
        # Color based on HP percentage
        if hq_hp_pct > 0.6:
            hq_color = (0, 255, 0)  # Green
        elif hq_hp_pct > 0.3:
            hq_color = (255, 255, 0)  # Yellow
        else:
            hq_color = (255, 0, 0)  # Red
        
        hq_text = f"HQ HP: {int(self.hq_hp)} / {int(self.hq_max_hp)}"
        hq_surface = self.font_large.render(hq_text, True, hq_color)
        hq_rect = hq_surface.get_rect(center=(self.screen_width // 2, 25))
        surface.blit(hq_surface, hq_rect)
        
        # Draw HP bar below text
        bar_width = 300
        bar_height = 20
        bar_x = self.screen_width // 2 - bar_width // 2
        bar_y = 45
        # Background bar
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # HP bar
        hp_bar_width = int(bar_width * hq_hp_pct)
        pygame.draw.rect(surface, hq_color, (bar_x, bar_y, hp_bar_width, bar_height))
        # Border
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Draw wave info (below day/night)
        if self.wave_info:
            wave_text = f"Enemies: {self.wave_info.get('enemies_spawned', 0)} / {self.wave_info.get('total_to_spawn', 0)}"
            wave_surface = self.font_medium.render(wave_text, True, (255, 255, 255))
            surface.blit(wave_surface, (10, 60))
        
        # Draw event banner (top-center, fades in/out)
        if self.event_visible:
            # Calculate alpha based on timer
            if self.event_timer > self.event_duration * 0.8:
                # Fade in
                alpha = int(255 * (1 - (self.event_timer - self.event_duration * 0.8) / (self.event_duration * 0.2)))
            elif self.event_timer < self.event_duration * 0.2:
                # Fade out
                alpha = int(255 * (self.event_timer / (self.event_duration * 0.2)))
            else:
                alpha = 255
            
            # Draw event banner
            event_surface = self.font_large.render(self.event_text, True, (255, 255, 255))
            event_surface.set_alpha(alpha)
            event_rect = event_surface.get_rect(center=(self.screen_width // 2, 50))
            surface.blit(event_surface, event_rect)

