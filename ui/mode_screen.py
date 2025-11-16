"""Mode selection screen."""
from __future__ import annotations

import pygame
from typing import Callable, Optional, List
from enum import Enum


class GameMode(Enum):
    """Game mode options."""
    TEN_DAY = "10_day"
    TWENTY_DAY = "20_day"
    ENDLESS = "endless"


class SelectModeScreen:
    """Mode selection screen with sprite-based UI."""

    BUTTON_WIDTH = 500
    BUTTON_HEIGHT = 350
    NUM_FRAMES = 3  # 10 day, 20 day, endless
    
    def __init__(self, screen_width: int, screen_height: int, font_large=None, sound_system=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_visible = False
        self.sound_system = sound_system
        
        # Font for title text
        self.font_large = font_large if font_large else pygame.font.Font(None, 72)

        # Load button sprite sheet and split into frames
        self.button_sprite_sheet = self._load_button_sheet()
        self.button_frames: List[pygame.Surface] = self._split_button_frames()

        # Static background image (same as difficulty screen)
        self.bg_image: Optional[pygame.Surface] = self._load_static_background()

        # Button positions (centered horizontally)
        # Calculate positions: 3 buttons with 80px spacing between them
        total_width = (self.BUTTON_WIDTH * 3) + (80 * 2)  # 3 buttons + 2 gaps
        start_x = (screen_width - total_width) // 2
        button_y = 365  # Similar to difficulty screen
        
        self.button_rects = {
            GameMode.TEN_DAY: pygame.Rect(start_x, button_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT),
            GameMode.TWENTY_DAY: pygame.Rect(start_x + self.BUTTON_WIDTH + 80, button_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT),
            GameMode.ENDLESS: pygame.Rect(start_x + (self.BUTTON_WIDTH + 80) * 2, button_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT),
        }

        self.hover_scale = 1.05

        self.options = list(GameMode)
        self.selected_index = 0
        self.hover_index: Optional[int] = None

        self.on_select: Optional[Callable[[GameMode], None]] = None
        self.on_cancel: Optional[Callable[[], None]] = None

    def _load_button_sheet(self) -> pygame.Surface:
        """Load the mode button sprite sheet."""
        try:
            sheet = pygame.image.load("asset/hud/Modebutton-Sheet.png").convert_alpha()
            return sheet
        except Exception as e:
            print(f"Warning: Failed to load mode button sprite sheet: {e}")
            # Create placeholder
            placeholder = pygame.Surface((self.BUTTON_WIDTH * self.NUM_FRAMES, self.BUTTON_HEIGHT), pygame.SRCALPHA)
            placeholder.fill((50, 50, 50, 255))
            return placeholder

    def _split_button_frames(self) -> List[pygame.Surface]:
        """Split button sprite sheet into individual frames."""
        frames = []
        for i in range(self.NUM_FRAMES):
            x = i * self.BUTTON_WIDTH
            frame = self.button_sprite_sheet.subsurface((x, 0, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)).copy()
            frames.append(frame)
        return frames

    def _load_static_background(self) -> Optional[pygame.Surface]:
        """Load a static background image for the mode screen."""
        import os
        paths = ['asset/gamestar.jpg', 'asset/Gamestart.jpg']
        for p in paths:
            if os.path.exists(p):
                try:
                    return pygame.image.load(p).convert()
                except Exception as e:
                    print(f"Warning: Failed to load {p}: {e}")
        return None

    def show(self):
        """Show mode selection screen."""
        self.is_visible = True
        self.selected_index = 0
        self.hover_index = None

    def hide(self):
        """Hide mode selection screen."""
        self.is_visible = False
        self.hover_index = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self.is_visible:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                old_index = self.selected_index
                self.selected_index = (self.selected_index - 1) % len(self.options)
                self.hover_index = self.selected_index
                # Play hover sound on keyboard navigation
                if old_index != self.selected_index and self.sound_system:
                    self.sound_system.play("sci_fi_hover")
                return True
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                old_index = self.selected_index
                self.selected_index = (self.selected_index + 1) % len(self.options)
                self.hover_index = self.selected_index
                # Play hover sound on keyboard navigation
                if old_index != self.selected_index and self.sound_system:
                    self.sound_system.play("sci_fi_hover")
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm_selection()
                return True
            if event.key == pygame.K_ESCAPE:
                if self.on_cancel:
                    self.on_cancel()
                return True

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._option_index_at(event.pos)
            if idx is not None:
                self.selected_index = idx
                self._confirm_selection()
                return True

        return False

    def _option_index_at(self, pos) -> Optional[int]:
        """Find which mode option is at the given position."""
        for idx, mode in enumerate(self.options):
            if self.button_rects[mode].collidepoint(pos):
                return idx
        return None

    def _update_hover(self, pos):
        """Update hover state based on mouse position."""
        idx = self._option_index_at(pos)
        # Play hover sound if hovering over a new button
        if idx is not None and idx != self.hover_index:
            if self.sound_system:
                self.sound_system.play("sci_fi_hover")
        self.hover_index = idx
        if idx is not None:
            self.selected_index = idx

    def _confirm_selection(self):
        """Confirm the selected mode."""
        mode = self.options[self.selected_index]
        if self.on_select:
            self.on_select(mode)

    def update(self, dt: float):
        """Update screen (no animation needed currently)."""
        pass

    def draw(self, surface: pygame.Surface):
        """Draw mode selection screen."""
        if not self.is_visible:
            return

        # Draw static background if available
        if self.bg_image:
            if self.bg_image.get_size() != (self.screen_width, self.screen_height):
                scaled_bg = pygame.transform.scale(self.bg_image, (self.screen_width, self.screen_height))
                surface.blit(scaled_bg, (0, 0))
            else:
                surface.blit(self.bg_image, (0, 0))
        else:
            # Fallback background
            surface.fill((20, 20, 28))

        # Draw mode buttons
        for idx, mode in enumerate(self.options):
            rect = self.button_rects[mode]
            button_frame = self.button_frames[idx] if idx < len(self.button_frames) else None
            
            if button_frame is None:
                # Fallback: simple colored rect with text
                color = (60, 60, 60)
                pygame.draw.rect(surface, color, rect, border_radius=8)
                label = mode.value.replace("_", " ").title()
                font = pygame.font.Font(None, 48)
                text = font.render(label, True, (255, 255, 255))
                trect = text.get_rect(center=rect.center)
                surface.blit(text, trect)
                continue

            # Determine scale on hover
            if self.hover_index == idx:
                w = int(rect.width * self.hover_scale)
                h = int(rect.height * self.hover_scale)
                scaled = pygame.transform.smoothscale(button_frame, (w, h))
                # Center the scaled image over the rect
                draw_x = rect.centerx - w // 2
                draw_y = rect.centery - h // 2
                surface.blit(scaled, (draw_x, draw_y))
            else:
                scaled = pygame.transform.smoothscale(button_frame, (rect.width, rect.height))
                surface.blit(scaled, rect.topleft)

        # Draw title text at top middle
        title_text = "Survival Mode Select"
        title_surface = self.font_large.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect()
        title_x = (self.screen_width - title_rect.width) // 2
        title_y = 50  # Top margin
        surface.blit(title_surface, (title_x, title_y))

