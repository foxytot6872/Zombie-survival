from __future__ import annotations

import pygame
from typing import Dict, List, Optional, Tuple, Type

from difficulty_config import Difficulty
from economy import scale_cost as scale_build_cost
from upgrade_config import get_next_turret_upgrade, scale_upgrade_cost
from world.building import Building


class BuildTooltipManager:
    BG_COLOR = (58, 63, 71)
    BORDER_COLOR = (107, 199, 255)
    TEXT_COLOR = (235, 240, 250)
    WARNING_COLOR = (255, 120, 120)
    INFO_COLOR = (140, 210, 255)

    def __init__(self, item_config: Dict, screen_size: Tuple[int, int], 
                 font_blue=None, font_red=None, font_yellow=None,
                 yellow_number_frames=None, red_number_frames=None, blue_number_frames=None):
        pygame.font.init()
        self.item_config = item_config
        self.screen_width, self.screen_height = screen_size
        # Use custom fonts if available, otherwise fallback to default
        self.title_font = font_blue if font_blue else pygame.font.Font(None, 32)
        self.body_font = font_blue if font_blue else pygame.font.Font(None, 24)
        self.warning_font = font_red if font_red else pygame.font.Font(None, 24)  # Red for warnings
        # Number font frames (17x22 each, 0-9)
        self.yellow_number_frames = yellow_number_frames if yellow_number_frames else []
        self.red_number_frames = red_number_frames if red_number_frames else []
        self.blue_number_frames = blue_number_frames if blue_number_frames else []
        self.visible = False
        self.surface: Optional[pygame.Surface] = None
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.current_item_key: Optional[str] = None
        self.difficulty = Difficulty.EASY

    def set_difficulty(self, difficulty: Difficulty):
        self.difficulty = difficulty

    def show_build_tooltip(
        self,
        building_class: Type[Building],
        button_rect: pygame.Rect,
        resources,
        research_manager,
        world=None,
        difficulty: Optional[Difficulty] = None,
    ):
        item_key = building_class.__name__
        cfg = self.item_config.get(item_key, {})
        display_name = cfg.get("name", item_key)
        difficulty = difficulty or self.difficulty
        self.difficulty = difficulty

        base_cost_override = cfg.get("base_cost")
        if base_cost_override:
            cost_dict = scale_build_cost(base_cost_override, difficulty, cost_type="build")
            if world and hasattr(world, 'modifiers'):
                cost_mult = world.modifiers.get("build_cost_mult", 1.0)
                for key in ("wood", "iron", "food"):
                    cost_dict[key] = int(cost_dict.get(key, 0) * cost_mult)
        else:
            scaled_cost = building_class.get_scaled_cost(world=world, difficulty=difficulty)
            cost_dict = {"wood": scaled_cost.wood, "iron": scaled_cost.iron, "food": scaled_cost.food, "coins": scaled_cost.coins}

        requires = cfg.get("requires", [])
        requires_display = cfg.get("requires_display", requires)
        missing_research: List[str] = []
        for idx, req in enumerate(requires):
            if not research_manager or not research_manager.is_unlocked(req):
                display = requires_display[idx] if idx < len(requires_display) else req
                missing_research.append(display)

        self.surface = self._render_tooltip(display_name, cost_dict, resources, missing_research)
        self.rect = self._position_tooltip(button_rect, self.surface.get_size())
        self.visible = True
        self.current_item_key = item_key

    def show_upgrade_tooltip(
        self,
        building: Building,
        button_rect: pygame.Rect,
        resources,
        difficulty,
    ):
        info = get_next_turret_upgrade(building)
        if not info or info.get("is_max"):
            self.surface = self._render_max_upgrade_tooltip()
        else:
            scaled_cost = scale_upgrade_cost(info["base_cost"], difficulty)
            self.surface = self._render_upgrade_tooltip(info, scaled_cost, resources, difficulty)
        self.rect = self._position_tooltip(button_rect, self.surface.get_size())
        self.visible = True
        self.current_item_key = "upgrade_button"

    def hide_tooltip(self):
        self.visible = False
        self.current_item_key = None

    def draw(self, surface: pygame.Surface):
        if self.visible and self.surface:
            surface.blit(self.surface, self.rect.topleft)

    def _draw_number(self, surface: pygame.Surface, number: int, x: int, y: int, color: str = "yellow", scale_to_font=None):
        """
        Draw a number using sprite frames.
        Args:
            surface: Surface to draw on
            number: Number to draw
            x: X position
            y: Y position
            color: Color to use
            scale_to_font: Optional font to scale numbers to match (CustomFont or pygame.font.Font)
        """
        if color == "red":
            number_frames = self.red_number_frames
        elif color == "blue":
            number_frames = self.blue_number_frames
        else:  # default to yellow
            number_frames = self.yellow_number_frames
        
        if not number_frames or len(number_frames) < 10:
            return
        
        # Scale numbers to match font size if provided
        if scale_to_font:
            # Get target height from font
            if hasattr(scale_to_font, 'letter_height'):
                target_height = scale_to_font.letter_height  # CustomFont
            elif hasattr(scale_to_font, 'get_height'):
                target_height = scale_to_font.get_height()  # pygame.font.Font
            else:
                target_height = 24  # Fallback
            
            # Original number frame size is 22 pixels tall
            original_height = 22
            scale_factor = target_height / original_height if original_height > 0 else 1.0
        else:
            scale_factor = 1.0
        
        number_str = str(number)
        current_x = x
        for digit_char in number_str:
            digit = int(digit_char)
            if 0 <= digit <= 9:
                digit_frame = number_frames[digit]
                
                # Scale if needed
                if scale_factor != 1.0:
                    scaled_width = int(digit_frame.get_width() * scale_factor)
                    scaled_height = int(digit_frame.get_height() * scale_factor)
                    digit_frame = pygame.transform.scale(digit_frame, (scaled_width, scaled_height))
                
                surface.blit(digit_frame, (current_x, y))
                # Reduce gap between digits by using actual width minus 2px overlap
                current_x += digit_frame.get_width() - 2
    
    def _render_tooltip(self, title: str, cost_dict: Dict[str, int], resources, missing_research: List[str]) -> pygame.Surface:
        # Title and header lines (text only)
        text_lines: List[Tuple[str, Tuple[int, int, int]]] = []
        text_lines.append((title, self.TEXT_COLOR))
        text_lines.append(("Cost:", self.INFO_COLOR))
        
        # Resource lines with numbers (label, value, text_color, number_color)
        resource_lines: List[Tuple[str, int, Tuple[int, int, int], str]] = []

        def resource_line(label: str, value: int, current: int):
            text_color = self.TEXT_COLOR if current >= value else self.WARNING_COLOR
            number_color = "yellow" if current >= value else "red"
            return (f" - {label}: ", value, text_color, number_color)

        resource_lines.append(resource_line("Wood", cost_dict.get("wood", 0), resources.wood))
        resource_lines.append(resource_line("Iron", cost_dict.get("iron", 0), resources.iron))
        coins_cost = cost_dict.get("coins", 0)
        if coins_cost:
            resource_lines.append(resource_line("Coins", coins_cost, getattr(resources, "coins", 0)))

        if missing_research:
            text_lines.append(("Required Research:", self.INFO_COLOR))
            for req in missing_research:
                text_lines.append((f" ❌ {req}", self.WARNING_COLOR))

        padding = 10
        line_height = self.body_font.get_linesize() if hasattr(self.body_font, 'get_linesize') else 24
        
        # Calculate width including numbers
        first_line_width = self.title_font.size(text_lines[0][0])[0] if hasattr(self.title_font, 'size') else 0
        text_widths = [self.body_font.size(text)[0] if hasattr(self.body_font, 'size') else 0 for text, _ in text_lines[1:]]
        resource_widths = []
        # Get font height for scaling
        if hasattr(self.body_font, 'letter_height'):
            font_height = self.body_font.letter_height
        elif hasattr(self.body_font, 'get_height'):
            font_height = self.body_font.get_height()
        else:
            font_height = 24
        scale_factor = font_height / 22.0 if 22 > 0 else 1.0
        for label_text, value, text_color, number_color in resource_lines:
            label_width = self.body_font.size(label_text)[0] if hasattr(self.body_font, 'size') else 0
            number_width = int(len(str(value)) * 17 * scale_factor)  # Scaled width
            resource_widths.append(label_width + number_width)
        
        width = max([first_line_width] + text_widths + resource_widths, default=0)
        width += padding * 2
        total_lines = len(text_lines) + len(resource_lines)
        height = padding * 2 + line_height * total_lines

        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        tooltip_rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(surface, self.BG_COLOR, tooltip_rect, border_radius=8)
        pygame.draw.rect(surface, self.BORDER_COLOR, tooltip_rect, width=2, border_radius=8)

        y = padding
        # Draw text lines
        for idx, (text, color) in enumerate(text_lines):
            if color == self.WARNING_COLOR:
                font = self.warning_font
            else:
                font = self.title_font if idx == 0 else self.body_font
            rendered = font.render(text, True, color)
            surface.blit(rendered, (padding, y))
            y += line_height
        
        # Draw resource lines with numbers
        for label_text, value, text_color, number_color in resource_lines:
            # Draw label
            font = self.body_font
            if text_color == self.WARNING_COLOR:
                font = self.warning_font
            label_surface = font.render(label_text, True, text_color)
            surface.blit(label_surface, (padding, y))
            
            # Draw number - scale to match font size
            number_x = padding + label_surface.get_width()
            # Get font height for vertical centering
            if hasattr(font, 'letter_height'):
                font_height = font.letter_height
            elif hasattr(font, 'get_height'):
                font_height = font.get_height()
            else:
                font_height = 24
            number_y = y + (line_height - font_height) // 2  # Center vertically
            self._draw_number(surface, value, number_x, number_y, color=number_color, scale_to_font=font)
            y += line_height
        
        return surface

    def _render_upgrade_tooltip(self, info: Dict, cost_dict: Dict[str, int], resources, difficulty) -> pygame.Surface:
        target_tier = info.get("target_tier", "?")
        target_step = info.get("target_step", 1)
        step_total = info.get("step_total", 3)
        title = f"Next Upgrade: Tier {target_tier} (Step {target_step}/{step_total})"

        # Title and header lines (text only)
        text_lines: List[Tuple[str, Tuple[int, int, int]]] = [
            (title, self.TEXT_COLOR),
            ("Cost:", self.INFO_COLOR),
        ]
        
        # Resource lines with numbers (label, value, text_color, number_color)
        resource_lines: List[Tuple[str, int, Tuple[int, int, int], str]] = []

        def resource_line(label: str, value: int, current: int):
            text_color = self.TEXT_COLOR if current >= value else self.WARNING_COLOR
            number_color = "yellow" if current >= value else "red"
            return (f" - {label}: ", value, text_color, number_color)

        resource_lines.append(resource_line("Wood", cost_dict.get("wood", 0), resources.wood))
        resource_lines.append(resource_line("Iron", cost_dict.get("iron", 0), resources.iron))
        coins_cost = cost_dict.get("coins", 0)
        if coins_cost:
            resource_lines.append(resource_line("Coins", coins_cost, getattr(resources, "coins", 0)))

        diff_label = difficulty.name.title() if isinstance(difficulty, Difficulty) else str(difficulty)
        text_lines.append((f"Difficulty: {diff_label}", self.INFO_COLOR))

        # Use similar rendering as _render_tooltip
        padding = 10
        line_height = self.body_font.get_linesize() if hasattr(self.body_font, 'get_linesize') else 24
        
        # Calculate width including numbers
        first_line_width = self.title_font.size(text_lines[0][0])[0] if hasattr(self.title_font, 'size') else 0
        text_widths = [self.body_font.size(text)[0] if hasattr(self.body_font, 'size') else 0 for text, _ in text_lines[1:]]
        resource_widths = []
        # Get font height for scaling
        if hasattr(self.body_font, 'letter_height'):
            font_height = self.body_font.letter_height
        elif hasattr(self.body_font, 'get_height'):
            font_height = self.body_font.get_height()
        else:
            font_height = 24
        scale_factor = font_height / 22.0 if 22 > 0 else 1.0
        for label_text, value, text_color, number_color in resource_lines:
            label_width = self.body_font.size(label_text)[0] if hasattr(self.body_font, 'size') else 0
            number_width = int(len(str(value)) * 17 * scale_factor)  # Scaled width
            resource_widths.append(label_width + number_width)
        
        width = max([first_line_width] + text_widths + resource_widths, default=0)
        width += padding * 2
        total_lines = len(text_lines) + len(resource_lines)
        height = padding * 2 + line_height * total_lines

        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        tooltip_rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(surface, self.BG_COLOR, tooltip_rect, border_radius=8)
        pygame.draw.rect(surface, self.BORDER_COLOR, tooltip_rect, width=2, border_radius=8)

        y = padding
        # Draw text lines
        for idx, (text, color) in enumerate(text_lines):
            if color == self.WARNING_COLOR:
                font = self.warning_font
            else:
                font = self.title_font if idx == 0 else self.body_font
            rendered = font.render(text, True, color)
            surface.blit(rendered, (padding, y))
            y += line_height
        
        # Draw resource lines with numbers
        for label_text, value, text_color, number_color in resource_lines:
            # Draw label
            font = self.body_font
            if text_color == self.WARNING_COLOR:
                font = self.warning_font
            label_surface = font.render(label_text, True, text_color)
            surface.blit(label_surface, (padding, y))
            
            # Draw number - scale to match font size
            number_x = padding + label_surface.get_width()
            # Get font height for vertical centering
            if hasattr(font, 'letter_height'):
                font_height = font.letter_height
            elif hasattr(font, 'get_height'):
                font_height = font.get_height()
            else:
                font_height = 24
            number_y = y + (line_height - font_height) // 2  # Center vertically
            self._draw_number(surface, value, number_x, number_y, color=number_color, scale_to_font=font)
            y += line_height
        
        return surface

    def _render_max_upgrade_tooltip(self) -> pygame.Surface:
        lines = [
            ("MAX LEVEL", self.TEXT_COLOR),
            ("No further upgrades", self.INFO_COLOR),
        ]
        return self._render_lines(lines)

    def _render_lines(self, lines: List[Tuple[str, Tuple[int, int, int]]]) -> pygame.Surface:
        padding = 10
        # Get line height from body font
        line_height = self.body_font.get_linesize() if hasattr(self.body_font, 'get_linesize') else 24
        if hasattr(self.body_font, 'size'):
            # For custom font, get size using size method
            first_line_size = self.title_font.size(lines[0][0]) if hasattr(self.title_font, 'size') else (self.title_font.get_rect(lines[0][0]).width, line_height)
        else:
            first_line_size = self.title_font.get_rect(lines[0][0]).size if hasattr(self.title_font, 'get_rect') else (0, line_height)
        
        width = max(first_line_size[0], max((self.body_font.size(text)[0] if hasattr(self.body_font, 'size') else (self.body_font.get_rect(text).width if hasattr(self.body_font, 'get_rect') else 0) for text, _ in lines[1:]), default=0))
        width += padding * 2
        height = padding * 2 + line_height * len(lines)

        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        tooltip_rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(surface, self.BG_COLOR, tooltip_rect, border_radius=8)
        pygame.draw.rect(surface, self.BORDER_COLOR, tooltip_rect, width=2, border_radius=8)

        y = padding
        for idx, (text, color) in enumerate(lines):
            # Use warning font (red) for warning color, title font for first line, body font for others
            if color == self.WARNING_COLOR:
                font = self.warning_font
            else:
                font = self.title_font if idx == 0 else self.body_font
            rendered = font.render(text, True, color)
            surface.blit(rendered, (padding, y))
            y += line_height
        return surface

    def _position_tooltip(self, button_rect: pygame.Rect, size: Tuple[int, int]) -> pygame.Rect:
        width, height = size
        x = button_rect.centerx - width // 2
        y = button_rect.top - height - 8

        if x < 8:
            x = 8
        if x + width > self.screen_width - 8:
            x = self.screen_width - width - 8
        if y < 8:
            y = button_rect.bottom + 8
        if y + height > self.screen_height - 8:
            y = self.screen_height - height - 8

        return pygame.Rect(int(x), int(y), width, height)

