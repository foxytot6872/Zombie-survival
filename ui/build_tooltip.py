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

    def __init__(self, item_config: Dict, screen_size: Tuple[int, int]):
        pygame.font.init()
        self.item_config = item_config
        self.screen_width, self.screen_height = screen_size
        self.title_font = pygame.font.Font(None, 32)
        self.body_font = pygame.font.Font(None, 24)
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

    def _render_tooltip(self, title: str, cost_dict: Dict[str, int], resources, missing_research: List[str]) -> pygame.Surface:
        lines: List[Tuple[str, Tuple[int, int, int]]] = []
        lines.append((title, self.TEXT_COLOR))
        lines.append(("Cost:", self.INFO_COLOR))

        def resource_line(label: str, value: int, current: int):
            color = self.TEXT_COLOR if current >= value else self.WARNING_COLOR
            return (f" - {label}: {value}", color)

        lines.append(resource_line("Wood", cost_dict.get("wood", 0), resources.wood))
        lines.append(resource_line("Iron", cost_dict.get("iron", 0), resources.iron))
        coins_cost = cost_dict.get("coins", 0)
        if coins_cost:
            lines.append(resource_line("Coins", coins_cost, getattr(resources, "coins", 0)))

        if missing_research:
            lines.append(("Required Research:", self.INFO_COLOR))
            for req in missing_research:
                lines.append((f" ❌ {req}", self.WARNING_COLOR))

        padding = 10
        line_height = self.body_font.get_linesize()
        width = max(self.title_font.size(lines[0][0])[0], max((self.body_font.size(text)[0] for text, _ in lines[1:]), default=0))
        width += padding * 2
        height = padding * 2 + line_height * len(lines)

        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        tooltip_rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(surface, self.BG_COLOR, tooltip_rect, border_radius=8)
        pygame.draw.rect(surface, self.BORDER_COLOR, tooltip_rect, width=2, border_radius=8)

        y = padding
        for idx, (text, color) in enumerate(lines):
            font = self.title_font if idx == 0 else self.body_font
            rendered = font.render(text, True, color)
            surface.blit(rendered, (padding, y))
            y += line_height
        return surface

    def _render_upgrade_tooltip(self, info: Dict, cost_dict: Dict[str, int], resources, difficulty) -> pygame.Surface:
        target_tier = info.get("target_tier", "?")
        target_step = info.get("target_step", 1)
        step_total = info.get("step_total", 3)
        title = f"Next Upgrade: Tier {target_tier} (Step {target_step}/{step_total})"

        lines: List[Tuple[str, Tuple[int, int, int]]] = [
            (title, self.TEXT_COLOR),
            ("Cost:", self.INFO_COLOR),
        ]

        def resource_line(label: str, value: int, current: int):
            color = self.TEXT_COLOR if current >= value else self.WARNING_COLOR
            return (f" - {label}: {value}", color)

        lines.append(resource_line("Wood", cost_dict.get("wood", 0), resources.wood))
        lines.append(resource_line("Iron", cost_dict.get("iron", 0), resources.iron))
        coins_cost = cost_dict.get("coins", 0)
        if coins_cost:
            lines.append(resource_line("Coins", coins_cost, getattr(resources, "coins", 0)))

        diff_label = difficulty.name.title() if isinstance(difficulty, Difficulty) else str(difficulty)
        lines.append((f"Difficulty: {diff_label}", self.INFO_COLOR))

        return self._render_lines(lines)

    def _render_max_upgrade_tooltip(self) -> pygame.Surface:
        lines = [
            ("MAX LEVEL", self.TEXT_COLOR),
            ("No further upgrades", self.INFO_COLOR),
        ]
        return self._render_lines(lines)

    def _render_lines(self, lines: List[Tuple[str, Tuple[int, int, int]]]) -> pygame.Surface:
        padding = 10
        line_height = self.body_font.get_linesize()
        width = max(self.title_font.size(lines[0][0])[0], max((self.body_font.size(text)[0] for text, _ in lines[1:]), default=0))
        width += padding * 2
        height = padding * 2 + line_height * len(lines)

        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        tooltip_rect = pygame.Rect(0, 0, width, height)
        pygame.draw.rect(surface, self.BG_COLOR, tooltip_rect, border_radius=8)
        pygame.draw.rect(surface, self.BORDER_COLOR, tooltip_rect, width=2, border_radius=8)

        y = padding
        for idx, (text, color) in enumerate(lines):
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

