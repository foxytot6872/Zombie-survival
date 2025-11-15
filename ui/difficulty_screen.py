"""Difficulty selection screen."""
from __future__ import annotations

import pygame
from typing import Callable, Dict, Optional, List

from difficulty_config import Difficulty, DIFFICULTY_CONFIG, DifficultySettings


class SelectDifficultyScreen:
    """Difficulty selection screen with sprite-based UI."""

    FRAME_WIDTH = 1920
    FRAME_HEIGHT = 1080
    NUM_FRAMES = 5
    
    # Text animation constants
    TEXT_FRAME_WIDTH = 835
    TEXT_FRAME_HEIGHT = 115
    TEXT_NUM_FRAMES = 17
    TEXT_ANIMATION_SPEED = 0.05  # seconds per frame

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_visible = False

        # Load sprite sheet
        self.sprite_sheet = self._load_sprite_sheet()
        self.frames: List[pygame.Surface] = self._split_frames()

        # Load text sprite sheet and frames
        self.text_sprite_sheet = self._load_text_sprite_sheet()
        self.text_frames: List[pygame.Surface] = self._split_text_frames()
        
        # Text animation state
        self.text_animation_timer = 0.0
        self.text_current_frame = 0

        # Button definitions: (top_left_x, top_left_y, width, height)
        self.button_rects: Dict[Difficulty, pygame.Rect] = {
            Difficulty.EASY: pygame.Rect(114, 385, 356, 336),
            Difficulty.MEDIUM: pygame.Rect(557, 385, 356, 336),
            Difficulty.HARD: pygame.Rect(1007, 385, 356, 336),
            Difficulty.EXTREME: pygame.Rect(1453, 385, 356, 336),
        }

        self.options = list(Difficulty)
        self.selected_index = 0
        self.hover_index: Optional[int] = None

        self.on_select: Optional[Callable[[Difficulty], None]] = None
        self.on_cancel: Optional[Callable[[], None]] = None

    def _load_sprite_sheet(self) -> pygame.Surface:
        """Load the difficulty selection sprite sheet."""
        try:
            sheet = pygame.image.load("asset/SelectDifficultyPage-Sheet.png").convert_alpha()
            return sheet
        except Exception as e:
            print(f"Warning: Failed to load difficulty sprite sheet: {e}")
            # Create placeholder
            placeholder = pygame.Surface((self.FRAME_WIDTH * self.NUM_FRAMES, self.FRAME_HEIGHT), pygame.SRCALPHA)
            placeholder.fill((50, 50, 50, 255))
            return placeholder

    def _split_frames(self) -> List[pygame.Surface]:
        """Split sprite sheet into individual frames."""
        frames = []
        for i in range(self.NUM_FRAMES):
            x = i * self.FRAME_WIDTH
            frame = self.sprite_sheet.subsurface((x, 0, self.FRAME_WIDTH, self.FRAME_HEIGHT)).copy()
            frames.append(frame)
        return frames

    def _load_text_sprite_sheet(self) -> pygame.Surface:
        """Load the difficulty text sprite sheet."""
        try:
            sheet = pygame.image.load("asset/SelectDifficultyText-Sheet.png").convert_alpha()
            return sheet
        except Exception as e:
            print(f"Warning: Failed to load difficulty text sprite sheet: {e}")
            # Create placeholder
            placeholder = pygame.Surface((self.TEXT_FRAME_WIDTH * self.TEXT_NUM_FRAMES, self.TEXT_FRAME_HEIGHT), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100, 255))
            return placeholder

    def _split_text_frames(self) -> List[pygame.Surface]:
        """Split text sprite sheet into individual frames."""
        frames = []
        for i in range(self.TEXT_NUM_FRAMES):
            x = i * self.TEXT_FRAME_WIDTH
            frame = self.text_sprite_sheet.subsurface((x, 0, self.TEXT_FRAME_WIDTH, self.TEXT_FRAME_HEIGHT)).copy()
            frames.append(frame)
        return frames

    def show(self):
        self.is_visible = True
        # Reset text animation when showing
        self.text_animation_timer = 0.0
        self.text_current_frame = 0

    def hide(self):
        self.is_visible = False
        self.hover_index = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_visible:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_index = (self.selected_index - 1) % len(self.options)
                self.hover_index = self.selected_index
                return True
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_index = (self.selected_index + 1) % len(self.options)
                self.hover_index = self.selected_index
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
        """Find which difficulty option is at the given position."""
        for idx, difficulty in enumerate(self.options):
            if self.button_rects[difficulty].collidepoint(pos):
                return idx
        return None

    def _update_hover(self, pos):
        """Update hover state based on mouse position."""
        idx = self._option_index_at(pos)
        self.hover_index = idx
        if idx is not None:
            self.selected_index = idx

    def _get_current_frame_index(self) -> int:
        """Get the frame index to display based on hover state.
        
        Frame mapping:
        0: No hover
        1: Easy hover
        2: Medium hover
        3: Hard hover
        4: Extreme hover
        """
        if self.hover_index is None:
            return 0  # No hover frame
        return self.hover_index + 1  # +1 because frame 0 is no hover

    def _confirm_selection(self):
        difficulty = self.options[self.selected_index]
        if self.on_select:
            self.on_select(difficulty)

    def update(self, dt: float):
        """Update text animation with normal loop."""
        if not self.is_visible:
            return
        
        # Update text animation timer
        self.text_animation_timer += dt
        
        # Advance frame when timer exceeds frame duration
        if self.text_animation_timer >= self.TEXT_ANIMATION_SPEED:
            self.text_animation_timer = 0.0
            
            # Normal loop: forward and wrap around
            self.text_current_frame += 1
            if self.text_current_frame >= self.TEXT_NUM_FRAMES:
                # Reached end, loop back to start
                self.text_current_frame = 0

    def draw(self, surface: pygame.Surface):
        if not self.is_visible:
            return

        # Get the appropriate frame based on hover state
        frame_index = self._get_current_frame_index()
        current_frame = self.frames[frame_index]

        # Scale frame to screen size if needed
        if current_frame.get_size() != (self.screen_width, self.screen_height):
            scaled_frame = pygame.transform.scale(current_frame, (self.screen_width, self.screen_height))
            surface.blit(scaled_frame, (0, 0))
        else:
            surface.blit(current_frame, (0, 0))

        # Draw animated text at top middle
        if self.text_frames:
            text_frame = self.text_frames[self.text_current_frame]
            # Position at top middle of screen
            text_x = (self.screen_width - self.TEXT_FRAME_WIDTH) // 2
            text_y = 50  # Top margin
            surface.blit(text_frame, (text_x, text_y))

