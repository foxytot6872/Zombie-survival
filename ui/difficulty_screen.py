"""Difficulty selection screen."""
from __future__ import annotations

import pygame
from typing import Callable, Dict, Optional

from difficulty_config import Difficulty, DIFFICULTY_CONFIG, DifficultySettings


class SelectDifficultyScreen:
    """Simple difficulty selection screen with keyboard/mouse support."""

    OPTION_HEIGHT = 120
    OPTION_WIDTH = 600

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_visible = False
        self.font_title = pygame.font.Font(None, 72)
        self.font_option = pygame.font.Font(None, 48)
        self.font_desc = pygame.font.Font(None, 32)
        self.background = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.background.fill((0, 0, 0, 180))

        self.options = list(Difficulty)
        self.selected_index = 0
        self.hover_index: Optional[int] = None

        self.option_rects: Dict[Difficulty, pygame.Rect] = {}
        self._layout_options()

        self.on_select: Optional[Callable[[Difficulty], None]] = None
        self.on_cancel: Optional[Callable[[], None]] = None

    def _layout_options(self):
        total_height = len(self.options) * self.OPTION_HEIGHT + (len(self.options) - 1) * 20
        top = (self.screen_height - total_height) // 2
        left = (self.screen_width - self.OPTION_WIDTH) // 2

        for idx, difficulty in enumerate(self.options):
            rect = pygame.Rect(left, top + idx * (self.OPTION_HEIGHT + 20), self.OPTION_WIDTH, self.OPTION_HEIGHT)
            self.option_rects[difficulty] = rect

    def show(self):
        self.is_visible = True

    def hide(self):
        self.is_visible = False
        self.hover_index = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_visible:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.options)
                return True
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.options)
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
        for idx, difficulty in enumerate(self.options):
            if self.option_rects[difficulty].collidepoint(pos):
                return idx
        return None

    def _update_hover(self, pos):
        idx = self._option_index_at(pos)
        self.hover_index = idx
        if idx is not None:
            self.selected_index = idx

    def _confirm_selection(self):
        difficulty = self.options[self.selected_index]
        if self.on_select:
            self.on_select(difficulty)

    def update(self, dt: float):
        # Placeholder for future animation hooks
        return

    def draw(self, surface: pygame.Surface):
        if not self.is_visible:
            return

        surface.blit(self.background, (0, 0))

        title = self.font_title.render("Select Difficulty", True, (255, 255, 255))
        surface.blit(title, (self.screen_width // 2 - title.get_width() // 2, 100))

        for idx, difficulty in enumerate(self.options):
            rect = self.option_rects[difficulty]
            settings: DifficultySettings = DIFFICULTY_CONFIG[difficulty]

            is_selected = idx == self.selected_index
            border_color = (255, 215, 0) if is_selected else (160, 160, 160)
            fill_color = (40, 40, 60) if is_selected else (25, 25, 35)

            pygame.draw.rect(surface, fill_color, rect, border_radius=12)
            pygame.draw.rect(surface, border_color, rect, width=3, border_radius=12)

            name_surface = self.font_option.render(settings.name, True, (255, 255, 255))
            surface.blit(name_surface, (rect.x + 20, rect.y + 15))

            desc_surface = self.font_desc.render(settings.description, True, (200, 200, 200))
            surface.blit(desc_surface, (rect.x + 20, rect.y + 65))

