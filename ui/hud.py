"""
HUD (Heads-Up Display) for game information.
"""
import pygame
import re
from typing import Optional, Dict

class HUD:
    """HUD for displaying game information"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080, daycounter_frames=None, red_number_frames=None, blue_number_frames=None, yellow_number_frames=None, font_large=None, font_medium=None, font_small=None, hq_health_bar_frames=None):
        """
        Initialize HUD.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            daycounter_frames: List of pygame.Surface frames for animated day counter (6 frames, 256x128 each)
            red_number_frames: List of pygame.Surface frames for red numbers (10 frames, 42x74 each, 0-9)
            blue_number_frames: List of pygame.Surface frames for blue numbers (10 frames, 42x74 each, 0-9)
            font_large: Optional pygame.font.Font for large text (defaults to system font)
            font_medium: Optional pygame.font.Font for medium text (defaults to system font)
            font_small: Optional pygame.font.Font for small text (defaults to system font)
            hq_health_bar_frames: List of pygame.Surface frames for HQ health bar (21 frames, 550x28 each)
                Frame 0 = 100% health, Frame 20 = 0% health (death)
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = font_large if font_large else pygame.font.Font(None, 48)
        self.font_medium = font_medium if font_medium else pygame.font.Font(None, 32)
        self.font_small = font_small if font_small else pygame.font.Font(None, 24)
        
        # Day counter animation
        self.daycounter_frames = daycounter_frames if daycounter_frames else []
        self.daycounter_animation_timer = 0.0
        self.daycounter_animation_duration = 0.5  # Blinking animation duration (0.5 seconds)
        self.daycounter_current_frame = 0
        self.previous_state = None  # Track previous game state to detect transitions
        self.is_transitioning = False  # Whether we're currently in a transition animation
        self.transition_animation_timer = 0.0
        
        # Number sprite frames (0-9) - large HUD numbers (42x74)
        self.red_number_frames = red_number_frames if red_number_frames else []
        self.blue_number_frames = blue_number_frames if blue_number_frames else []
        # Small number font frames (17x22) for UI elements
        self.yellow_number_frames = yellow_number_frames if yellow_number_frames else []
        
        # HQ health bar sprite frames (21 frames: Frame 0 = 100%, Frame 20 = 0%)
        self.hq_health_bar_frames = hq_health_bar_frames if hq_health_bar_frames else []
        
        # HUD elements
        self.day = 1
        self.night = 1
        self.state = "DAY"
        self.wave_info: Dict = {}
        self.hq_hp = 0
        self.hq_max_hp = 2000
        
        # Event popup
        self.event_text = ""
        self.event_title = ""  # Separate title for event popup
        self.event_description = ""  # Event description
        self.event_effects = []  # List of effect strings
        self.event_type = "neutral"  # "positive", "mixed", "negative", or "neutral"
        self.event_timer = 0.0
        self.event_duration = 4.0  # Default duration ~4 seconds
        self.event_visible = False
        self.event_fade_alpha = 0  # For fade-in/fade-out animation
        
        # Game mode info
        self.mode_label: str = ""
        self.mode_target_nights: Optional[int] = None
        
        # Day/night counter pulse animation
        self.day_night_pulse_anim = None  # PulseAnimation for day/night transitions
        self.previous_day = None
        self.previous_night = None
    
    def update(self, dt: float, day: int, night: int, state: str, wave_info: Dict, hq_hp: int = 0, hq_max_hp: int = 2000):
        """Update HUD information"""
        self.day = day
        self.night = night
        self.state = state
        self.wave_info = wave_info
        self.hq_hp = hq_hp
        self.hq_max_hp = hq_max_hp
        
        # Detect day/night transitions for pulse animation
        from core.animation_timer import PulseAnimation
        if self.previous_day is None:
            self.previous_day = day
            self.previous_night = night
        else:
            # Check if day or night changed
            if day != self.previous_day or night != self.previous_night:
                # Start pulse animation (1.0 -> 1.15 -> 1.0, 120ms)
                self.day_night_pulse_anim = PulseAnimation(duration=0.12, max_scale=1.15)
                self.day_night_pulse_anim.start()
            self.previous_day = day
            self.previous_night = night
        
        # Update pulse animation
        if self.day_night_pulse_anim:
            pulse_scale = self.day_night_pulse_anim.get_scale()
            if pulse_scale == 1.0 and self.day_night_pulse_anim.is_active == False:
                self.day_night_pulse_anim = None  # Clean up when complete
        
        # Update day counter animation
        if self.daycounter_frames:
            # Detect state transitions
            if self.previous_state is not None and self.previous_state != self.state:
                # State changed - start transition animation
                self.is_transitioning = True
                self.transition_animation_timer = 0.0
                # Start from appropriate frame range
                if self.state == "DAY":
                    self.daycounter_current_frame = 0  # Start day animation (frames 0-2)
                elif self.state == "NIGHT":
                    self.daycounter_current_frame = 3  # Start night animation (frames 3-5)
            
            # Update transition animation if transitioning
            if self.is_transitioning:
                self.transition_animation_timer += dt
                
                if self.state == "DAY":
                    # Day animation: frames 0-2 (1-3 in 1-indexed)
                    frame_time = self.daycounter_animation_duration / 3  # 3 frames for day
                    frame_index = int(self.transition_animation_timer / frame_time)
                    if frame_index >= 3:
                        frame_index = 2  # Stay on last frame of animation
                        self.is_transitioning = False  # Animation complete
                    self.daycounter_current_frame = frame_index
                elif self.state == "NIGHT":
                    # Night animation: frames 3-5 (4-6 in 1-indexed)
                    frame_time = self.daycounter_animation_duration / 3  # 3 frames for night
                    frame_index = int(self.transition_animation_timer / frame_time)
                    if frame_index >= 3:
                        frame_index = 2  # Stay on last frame of animation
                        self.is_transitioning = False  # Animation complete
                    self.daycounter_current_frame = 3 + frame_index  # Offset by 3 for night frames
            else:
                # Not transitioning - show static frame based on state
                if self.state == "DAY":
                    self.daycounter_current_frame = 0  # Frame 1 (day static)
                elif self.state == "NIGHT":
                    self.daycounter_current_frame = 3  # Frame 4 (night static)
                else:
                    # Default to day frame
                    self.daycounter_current_frame = 0
            
            # Update previous state
            self.previous_state = self.state
            
            # Clamp to valid frame index
            if self.daycounter_current_frame >= len(self.daycounter_frames):
                self.daycounter_current_frame = len(self.daycounter_frames) - 1
        
        # Update event popup (with fade-in/fade-out animation)
        if self.event_visible:
            self.event_timer -= dt
            
            # Fade-in: first 0.3 seconds
            fade_in_duration = 0.3
            # Fade-out: last 0.5 seconds
            fade_out_duration = 0.5
            
            if self.event_timer > self.event_duration - fade_in_duration:
                # Fading in
                fade_progress = (self.event_duration - self.event_timer) / fade_in_duration
                self.event_fade_alpha = int(255 * fade_progress)
            elif self.event_timer < fade_out_duration:
                # Fading out
                fade_progress = self.event_timer / fade_out_duration
                self.event_fade_alpha = int(255 * fade_progress)
            else:
                # Fully visible
                self.event_fade_alpha = 255
            
            if self.event_timer <= 0:
                self.event_visible = False
                self.event_fade_alpha = 0
    
    def show_event(
        self,
        text: str,
        duration: float = 4.0,
        title: str = "",
        description: str = "",
        effects: list = None,
        event_type: str = "neutral",
    ):
        """
        Show event popup with improved formatting.
        
        Args:
            text: Full event text (for backward compatibility)
            duration: How long to display (default 4 seconds)
            title: Event title (e.g., "Lucky Day")
            description: Event description (e.g., "Gathering yields +50% resources today.")
            effects: List of effect strings (e.g., ["+50% Resource Production", "+2 Bonus Trees"])
        """
        self.event_text = text
        
        # Parse text if title/description/effects not provided (backward compatibility)
        if not title and ":" in text:
            parts = text.split(":", 1)
            title = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else text
        elif not title:
            title = "Event"
            description = text
        
        self.event_title = title
        self.event_description = description
        self.event_effects = effects if effects else []
        self.event_type = event_type or "neutral"
        
        self.event_timer = duration
        self.event_duration = duration
        self.event_visible = True
        self.event_fade_alpha = 0  # Start faded in (will fade in from 0)
    
    def show_starting_defenses_hint(self):
        """Show 'Starting Defenses' hint on Day 1"""
        self.show_event("Starting Defenses: Wall, Gate, and Turrets", duration=5.0)
    
    def set_game_mode_info(self, label: str, target_nights: Optional[int]):
        """Update HUD with the current game mode details."""
        self.mode_label = label or ""
        self.mode_target_nights = target_nights
    
    def draw_number(self, surface: pygame.Surface, number: int, x: int, y: int, use_red: bool = True):
        """
        Draw a number using sprite frames (large HUD numbers 42x74).
        Args:
            surface: Surface to draw on
            number: Number to draw (0-9, or multi-digit)
            x: X position (left edge)
            y: Y position (top edge)
            use_red: If True, use red numbers; if False, use blue numbers
        """
        number_frames = self.red_number_frames if use_red else self.blue_number_frames
        if not number_frames or len(number_frames) < 10:
            return
        
        # Convert number to string to get individual digits
        number_str = str(number)
        current_x = x
        
        for digit_char in number_str:
            digit = int(digit_char)
            if 0 <= digit <= 9:
                digit_frame = number_frames[digit]
                surface.blit(digit_frame, (current_x, y))
                # Move to next digit position
                digit_width = digit_frame.get_width()
                current_x += digit_width - 0 #increase gap by 0 (more number = more gap)
    
    def draw_small_number(self, surface: pygame.Surface, number: int, x: int, y: int, color: str = "yellow"):
        """
        Draw a small number using sprite frames (17x22 UI numbers).
        Args:
            surface: Surface to draw on
            number: Number to draw (0-9, or multi-digit)
            x: X position (left edge)
            y: Y position (top edge)
            color: Color to use - "yellow", "red", or "blue" (default: "yellow")
        """
        # Use yellow_number_frames for small UI numbers (17x22)
        # Note: red/blue_number_frames are large HUD numbers (42x74)
        number_frames = self.yellow_number_frames
        
        if not number_frames or len(number_frames) < 10:
            return
        
        # Convert number to string to get individual digits
        number_str = str(number)
        current_x = x
        
        for digit_char in number_str:
            digit = int(digit_char)
            if 0 <= digit <= 9:
                digit_frame = number_frames[digit]
                surface.blit(digit_frame, (current_x, y))
                # Move to next digit position (17 pixels per digit)
                current_x += digit_frame.get_width()
    
    def _render_text_with_numbers(self, text: str, font, color: tuple, number_color: str = "yellow", scale_to_font: bool = True):
        """
        Render text with numbers using number sprite sheets.
        Args:
            text: Text to render (may contain numbers)
            font: Font to use for text (pygame.font.Font or CustomFont)
            color: Color tuple for text
            number_color: Color of number sprites ("yellow", "red", "blue")
            scale_to_font: If True, scale numbers to match font height
        Returns:
            pygame.Surface with rendered text and numbers
        """
        
        # Get font height
        if hasattr(font, 'letter_height'):
            font_height = font.letter_height  # CustomFont
        elif hasattr(font, 'get_height'):
            font_height = font.get_height()  # pygame.font.Font
        else:
            font_height = 32  # Fallback
        
        # Choose number frames
        if number_color == "red":
            number_frames = self.red_number_frames if hasattr(self, 'red_number_frames') else []
        elif number_color == "blue":
            number_frames = self.blue_number_frames if hasattr(self, 'blue_number_frames') else []
        else:
            number_frames = self.yellow_number_frames if hasattr(self, 'yellow_number_frames') else []
        
        if not number_frames or len(number_frames) < 10:
            # Fallback to regular font rendering
            if hasattr(font, 'render'):
                return font.render(text, True, color)
            else:
                return pygame.Surface((0, 0), pygame.SRCALPHA)
        
        # Calculate scale factor
        scale_factor = (font_height / 22.0) if scale_to_font and 22 > 0 else 1.0
        
        # Split text into parts (text and numbers)
        parts = re.split(r'(\d+)', text)  # Split on numbers, keeping them
        
        # Calculate total width
        total_width = 0
        for part in parts:
            if part.isdigit():
                # Number part
                scaled_width = int((17 - 2) * scale_factor) * len(part)  # Reduced gap between digits
                total_width += scaled_width
            else:
                # Text part
                if hasattr(font, 'render'):
                    text_surface = font.render(part, True, color)
                    total_width += text_surface.get_width()
                else:
                    total_width += len(part) * 10  # Fallback estimate
        
        # Create output surface
        output = pygame.Surface((total_width, font_height), pygame.SRCALPHA)
        
        # Render parts
        current_x = 0
        for part in parts:
            if part.isdigit():
                # Render number using sprite sheets
                for digit_char in part:
                    digit = int(digit_char)
                    if 0 <= digit <= 9:
                        digit_frame = number_frames[digit]
                        if scale_to_font:
                            scaled_width = int(digit_frame.get_width() * scale_factor)
                            scaled_height = int(digit_frame.get_height() * scale_factor)
                            scaled_frame = pygame.transform.scale(digit_frame, (scaled_width, scaled_height))
                        else:
                            scaled_frame = digit_frame
                        
                        # Center vertically
                        y_offset = (font_height - scaled_frame.get_height()) // 2
                        output.blit(scaled_frame, (current_x, y_offset))
                        current_x += scaled_frame.get_width() - 2  # Reduced gap
            else:
                # Render text
                if part:  # Skip empty strings
                    if hasattr(font, 'render'):
                        text_surface = font.render(part, True, color)
                        # Center vertically
                        y_offset = (font_height - text_surface.get_height()) // 2
                        output.blit(text_surface, (current_x, y_offset))
                        current_x += text_surface.get_width()
        
        return output
    
    def _draw_scaled_number(self, surface: pygame.Surface, number: int, x: int, y: int, scale_factor: float):
        """
        Draw a number scaled to match font size.
        Args:
            surface: Surface to draw on
            number: Number to draw
            x: X position
            y: Y position
            scale_factor: Scale factor to apply (e.g., font_height / 22.0)
        """
        number_frames = self.yellow_number_frames
        if not number_frames or len(number_frames) < 10:
            return
        
        number_str = str(number)
        current_x = x
        for digit_char in number_str:
            digit = int(digit_char)
            if 0 <= digit <= 9:
                digit_frame = number_frames[digit]
                
                # Scale the frame
                if scale_factor != 1.0:
                    scaled_width = int(digit_frame.get_width() * scale_factor)
                    scaled_height = int(digit_frame.get_height() * scale_factor)
                    digit_frame = pygame.transform.scale(digit_frame, (scaled_width, scaled_height))
                
                surface.blit(digit_frame, (current_x, y))
                # Reduce gap between digits by using actual width minus 2px overlap
                current_x += digit_frame.get_width() - 2
    
    def draw(self, surface: pygame.Surface, show_ui_rectangles: bool = False):
        """Draw HUD"""
        # Day/Night indicator area (top-right) - use animated sprite if available
        if self.daycounter_frames and len(self.daycounter_frames) > 0:
            # Draw animated day counter sprite with pulse animation
            current_frame = self.daycounter_frames[self.daycounter_current_frame]
            
            # Apply pulse scale if active
            pulse_scale = 1.0
            if self.day_night_pulse_anim:
                pulse_scale = self.day_night_pulse_anim.get_scale()
            
            # Scale frame if pulse animation is active
            if pulse_scale != 1.0:
                scaled_width = int(current_frame.get_width() * pulse_scale)
                scaled_height = int(current_frame.get_height() * pulse_scale)
                scaled_frame = pygame.transform.scale(current_frame, (scaled_width, scaled_height))
                daycounter_rect = scaled_frame.get_rect(topright=(self.screen_width - 10, 10))
            else:
                daycounter_rect = current_frame.get_rect(topright=(self.screen_width - 10, 10))
                scaled_frame = current_frame
            
            # DEBUG: Draw overlay rectangle for day counter (256x128)
            if show_ui_rectangles:
                overlay = pygame.Surface((256, 128), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 80))  # Red overlay
                surface.blit(overlay, (self.screen_width - 266, 10))
            surface.blit(scaled_frame, daycounter_rect)
            
            # Draw day or night number on top of the day counter sprite
            # Only show one number at a time based on current state
            if self.state == "DAY":
                # Day time: show day number using blue numbers at (155, 43)
                day_number_x = daycounter_rect.x + 155
                day_number_y = daycounter_rect.y + 43
                self.draw_number(surface, self.day, day_number_x, day_number_y, use_red=False)
            elif self.state == "NIGHT":
                # Night time: show night number using red numbers at (200, 43)
                # Night number is the same as day number (night comes after day)
                night_number_x = daycounter_rect.x + 183
                night_number_y = daycounter_rect.y + 43
                self.draw_number(surface, self.day, night_number_x, night_number_y, use_red=True)
        else:
            # Fallback to text if sprite not available
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
            state_rect = state_surface.get_rect(topright=(self.screen_width - 10, 10))
            # Overlay rectangle for day/night indicator (estimated ~300x50)
            if show_ui_rectangles:
                overlay = pygame.Surface((300, 50), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 80))  # Red overlay
                surface.blit(overlay, (self.screen_width - 310, 10))
            surface.blit(state_surface, state_rect)
        
        # Draw HQ HP (top-center, important!) - Visual health bar only, no text (show don't tell)
        hq_hp_pct = self.hq_hp / self.hq_max_hp if self.hq_max_hp > 0 else 0.0
        # Clamp HP percentage to [0.0, 1.0]
        hq_hp_pct = max(0.0, min(1.0, hq_hp_pct))
        
        # Color based on HP percentage (for fallback rectangle only)
        if hq_hp_pct > 0.6:
            hq_color = (0, 255, 0)  # Green
        elif hq_hp_pct > 0.3:
            hq_color = (255, 255, 0)  # Yellow
        else:
            hq_color = (255, 0, 0)  # Red
        
        # Draw HQ health bar sprite (no text - visual representation only)
        if self.hq_health_bar_frames and len(self.hq_health_bar_frames) >= 21:
            # Calculate frame index: Frame 0 = 100%, Frame 20 = 0%
            # Formula: frame_index = int((1.0 - hq_hp_pct) * 20)
            frame_index = int((1.0 - hq_hp_pct) * 20)
            # Clamp to valid range [0, 20]
            frame_index = max(0, min(20, frame_index))
            
            # Get the health bar frame
            health_bar_frame = self.hq_health_bar_frames[frame_index]
            original_width, original_height = health_bar_frame.get_size()
            
            # Scale health bar to 1.5x size
            scale_factor = 1.5
            bar_width = int(original_width * scale_factor)
            bar_height = int(original_height * scale_factor)
            scaled_health_bar = pygame.transform.scale(health_bar_frame, (bar_width, bar_height))
            
            # Position health bar at top-center (visual representation only, no text)
            bar_x = self.screen_width // 2 - bar_width // 2
            bar_y = 20  # Top of screen, centered
            
            # Overlay rectangle for HP bar (for debug)
            if show_ui_rectangles:
                overlay = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
                overlay.fill((0, 0, 255, 80))  # Blue overlay
                surface.blit(overlay, (bar_x, bar_y))
            
            # Draw the scaled health bar sprite
            surface.blit(scaled_health_bar, (bar_x, bar_y))
        else:
            # Fallback: Draw simple rectangle bar if sprite frames not available
            bar_width = 300
            bar_height = 20
            bar_x = self.screen_width // 2 - bar_width // 2
            bar_y = 20  # Top of screen, centered
            # Overlay rectangle for HP bar (300x20)
            if show_ui_rectangles:
                overlay = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
                overlay.fill((0, 0, 255, 80))  # Blue overlay
                surface.blit(overlay, (bar_x, bar_y))
            # Background bar
            pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # HP bar
            hp_bar_width = int(bar_width * hq_hp_pct)
            pygame.draw.rect(surface, hq_color, (bar_x, bar_y, hp_bar_width, bar_height))
            # Border
            pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Draw wave info (top-right, below day counter)
        if self.wave_info:
            label_text = "Zombies: "
            label_surface = self.font_medium.render(label_text, True, (255, 255, 255))
            label_x = 1515
            label_y = 1040
            
            enemies_spawned = self.wave_info.get('enemies_spawned', 0)
            total_to_spawn = self.wave_info.get('total_to_spawn', 0)
            
            if hasattr(self.font_medium, 'letter_height'):
                font_height = self.font_medium.letter_height  # CustomFont
            elif hasattr(self.font_medium, 'get_height'):
                font_height = self.font_medium.get_height()  # pygame.font.Font
            else:
                font_height = 32  # Fallback
            
            scale_factor = font_height / 22.0 if 22 > 0 else 1.0
            scaled_number_width = int((17 - 2) * scale_factor)
            
            number_y = label_y + (font_height - font_height) // 2
            number_start_x = label_x + label_surface.get_width()
            
            self._draw_scaled_number(surface, enemies_spawned, number_start_x, number_y, scale_factor)
            
            separator_text = " / "
            separator_surface = self.font_medium.render(separator_text, True, (255, 255, 255))
            separator_x = number_start_x + len(str(enemies_spawned)) * scaled_number_width
            surface.blit(separator_surface, (separator_x, label_y))
            
            second_number_x = separator_x + separator_surface.get_width()
            self._draw_scaled_number(surface, total_to_spawn, second_number_x, number_y, scale_factor)
            
            surface.blit(label_surface, (label_x, label_y))
            
            if show_ui_rectangles:
                overlay = pygame.Surface((250, 30), pygame.SRCALPHA)
                overlay.fill((255, 255, 0, 80))  # Yellow overlay
                surface.blit(overlay, (label_x - 10, label_y - 5))
        
        # Draw event popup panel (top-center, with overlay and fade animation)
        if self.event_visible and self.event_fade_alpha > 0:
            # Draw semi-transparent dark overlay behind popup
            overlay_alpha = int(self.event_fade_alpha * 0.6)  # 60% opacity overlay
            dark_overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, overlay_alpha))
            surface.blit(dark_overlay, (0, 0))
            
            # Calculate popup panel dimensions
            panel_padding = 20
            # Increased width to better accommodate text
            popup_width = 700
            popup_x = (self.screen_width - popup_width) // 2
            popup_y = 150  # Top-center position
            
            # Prepare text content
            title_text = self.event_title
            desc_text = self.event_description
            
            # Choose colors based on event type
            if self.event_type == "positive":
                title_color = (210, 255, 210)
                border_base = (80, 200, 120)
            elif self.event_type == "negative":
                title_color = (255, 210, 210)
                border_base = (230, 100, 100)
            elif self.event_type == "mixed":
                title_color = (255, 245, 200)
                border_base = (230, 210, 120)
            else:
                title_color = (255, 255, 200)
                border_base = (107, 199, 255)

            # Render title (large font) - wrap if needed
            # Calculate maximum width for title text
            max_title_width = popup_width - (panel_padding * 2)
            title_surface = self._render_text_with_numbers(title_text, self.font_large, title_color, "yellow", True)
            # Check if title needs wrapping
            if title_surface.get_width() > max_title_width:
                # Word wrap title if too long
                words = title_text.split(' ')
                wrapped_title_lines = []
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    test_surface = self._render_text_with_numbers(test_line, self.font_large, title_color, "yellow", True)
                    if test_surface.get_width() <= max_title_width:
                        current_line = test_line
                    else:
                        if current_line:
                            wrapped_title_lines.append(current_line)
                        current_line = word
                if current_line:
                    wrapped_title_lines.append(current_line)
            else:
                wrapped_title_lines = [title_text]
            
            # Render wrapped title lines
            title_surfaces = []
            for line in wrapped_title_lines:
                title_surface = self._render_text_with_numbers(line, self.font_large, title_color, "yellow", True)
                title_surface.set_alpha(self.event_fade_alpha)
                title_surfaces.append(title_surface)
            
            # Render description (medium font, wrap text if needed)
            # Calculate maximum width for text (accounting for padding)
            max_text_width = popup_width - (panel_padding * 2)
            
            # Word wrap description text
            wrapped_desc_lines = []
            if desc_text:
                words = desc_text.split(' ')
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    test_surface = self._render_text_with_numbers(test_line, self.font_medium, (255, 255, 255), "yellow", True)
                    if test_surface.get_width() <= max_text_width:
                        current_line = test_line
                    else:
                        if current_line:
                            wrapped_desc_lines.append(current_line)
                        current_line = word
                if current_line:
                    wrapped_desc_lines.append(current_line)
            else:
                wrapped_desc_lines = [desc_text]
            
            # Render wrapped description lines
            desc_surfaces = []
            for line in wrapped_desc_lines:
                desc_surface = self._render_text_with_numbers(line, self.font_medium, (255, 255, 255), "yellow", True)
                desc_surface.set_alpha(self.event_fade_alpha)
                desc_surfaces.append(desc_surface)
            
            # Render effects if any (small font)
            effect_surfaces = []
            if self.event_effects:
                for effect in self.event_effects:
                    effect_surface = self._render_text_with_numbers(f"• {effect}", self.font_small, (200, 255, 200), "yellow", True)  # Light green
                    effect_surface.set_alpha(self.event_fade_alpha)
                    effect_surfaces.append(effect_surface)
            
            # Calculate panel height based on content
            line_spacing = 8
            title_height = sum(s.get_height() + line_spacing for s in title_surfaces) if title_surfaces else 0
            desc_height = sum(s.get_height() + line_spacing for s in desc_surfaces) if desc_surfaces else 0
            effects_height = sum(s.get_height() + line_spacing for s in effect_surfaces) if effect_surfaces else 0
            
            popup_height = (panel_padding * 2 + 
                           title_height + line_spacing * 2 +
                           desc_height + line_spacing +
                           effects_height)
            
            # Draw popup panel background
            popup_bg = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
            popup_bg.fill((40, 45, 55, int(self.event_fade_alpha * 0.95)))  # Dark semi-transparent background
            # Draw border (color-coded by event type)
            border_color = (*border_base, self.event_fade_alpha)
            pygame.draw.rect(popup_bg, border_color, popup_bg.get_rect(), width=3, border_radius=8)
            
            # Apply border radius effect (simple approach)
            popup_bg_rect = pygame.Rect(0, 0, popup_width, popup_height)
            popup_bg.set_alpha(int(self.event_fade_alpha * 0.95))
            surface.blit(popup_bg, (popup_x, popup_y))
            
            # Draw title (wrapped lines if needed)
            title_y = popup_y + panel_padding
            last_title_rect = None
            for title_surface in title_surfaces:
                title_rect = title_surface.get_rect(centerx=popup_x + popup_width // 2, y=title_y)
                surface.blit(title_surface, title_rect)
                title_y += title_surface.get_height() + line_spacing
                last_title_rect = title_rect
            
            # Draw description (wrapped lines)
            desc_y = last_title_rect.bottom + line_spacing * 2 if last_title_rect else popup_y + panel_padding
            last_desc_rect = None
            for desc_surface in desc_surfaces:
                desc_rect = desc_surface.get_rect(centerx=popup_x + popup_width // 2, y=desc_y)
                surface.blit(desc_surface, desc_rect)
                desc_y += desc_surface.get_height() + line_spacing
                last_desc_rect = desc_rect
            
            # Draw effects
            effect_y = last_desc_rect.bottom + line_spacing * 2 if last_desc_rect else title_rect.bottom + line_spacing * 2
            for effect_surface in effect_surfaces:
                effect_rect = effect_surface.get_rect(x=popup_x + panel_padding + 20, y=effect_y)
                surface.blit(effect_surface, effect_rect)
                effect_y += effect_surface.get_height() + line_spacing
            
            # DEBUG: Draw overlay rectangle for event popup
            if show_ui_rectangles:
                debug_overlay = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
                debug_overlay.fill((255, 0, 255, 80))  # Magenta overlay
                surface.blit(debug_overlay, (popup_x, popup_y))

