"""
Pixel-art friendly Research Tree UI for the Zombie Survival game.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OVERLAY_COLOR = (0, 0, 0, 200)
PANEL_COLOR = (26, 26, 26, 245)
SECTION_BG = (40, 40, 40)
SECTION_BORDER = (70, 70, 70)
TEXT_COLOR = (220, 220, 220)
LOCKED_FILL = (30, 30, 30)
LOCKED_BORDER = (80, 80, 80)
UNLOCKABLE_FILL = (30, 70, 30)
UNLOCKABLE_BORDER = (80, 200, 120)
UNLOCKED_FILL = (60, 60, 20)
UNLOCKED_BORDER = (220, 200, 120)
LINE_LOCKED = (60, 60, 60)
LINE_UNLOCKABLE = (80, 200, 120)
LINE_UNLOCKED = (220, 200, 120)
TOOLTIP_BG = (20, 20, 20)
TOOLTIP_BORDER = (140, 140, 140)

NODE_WIDTH = 150
NODE_HEIGHT = 60
ICON_SIZE = 40


def _load_icon(*paths: str) -> pygame.Surface:
    surface = None
    for path in paths:
        try:
            surface = pygame.image.load(path).convert_alpha()
            break
        except Exception:
            continue

    if surface is None:
        surface = pygame.Surface((ICON_SIZE, ICON_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(surface, (120, 120, 120), surface.get_rect(), 1)

    if surface.get_width() != ICON_SIZE or surface.get_height() != ICON_SIZE:
        surface = pygame.transform.scale(surface, (ICON_SIZE, ICON_SIZE))
    return surface


ICON_MAP: Dict[str, pygame.Surface] = {
    "smelter": _load_icon("asset/smelter/Bricks_01.png", "asset/smelter/Bricks_01-Sheet.png"),
    "alloy": _load_icon("asset/smelter/Bricks_02.png", "asset/smelter/Bricks_02-Sheet.png"),
    "forge": _load_icon("asset/smelter/Bricks_03.png", "asset/smelter/Bricks_03-Sheet.png"),
}

RESEARCH_BUILDING_UPGRADES: Dict[str, List[Tuple[str, int]]] = {
    "sawmill": [("smelter", 1)],
    "alloy": [("smelter", 2)],
    "forge": [("smelter", 3)],
}

# Persist node states between openings
GLOBAL_NODE_STATES: Dict[str, str] = {}


@dataclass
class ResearchNode:
    node_id: str
    name: str
    description: str
    cost: int
    position: Tuple[int, int]
    parents: List[str]
    category: str
    state: str = "locked"
    rect: pygame.Rect = field(init=False)

    def __post_init__(self):
        x, y = self.position
        self.rect = pygame.Rect(x - NODE_WIDTH // 2, y - NODE_HEIGHT // 2, NODE_WIDTH, NODE_HEIGHT)


class ResearchTreeUI:
    """Handles drawing and interaction for the research tree screen."""

    def __init__(
        self,
        screen: pygame.Surface,
        world,
        research_manager=None,
        game_state_manager=None,
    ):
        self.screen = screen
        self.width, self.height = self.screen.get_size()
        self.world = world
        self.resources = getattr(world, "resources", world)
        self.research_manager = research_manager
        self.game_state_manager = game_state_manager

        self.clock = pygame.time.Clock()
        self.running = False
        self.hover_node: Optional[ResearchNode] = None
        self.tooltip_surface: Optional[pygame.Surface] = None

        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 26)
        self.font_large = pygame.font.Font(None, 36)

        self.panel_rect = self._build_panel_rect()
        self.sections = self._build_sections()
        self.nodes: Dict[str, ResearchNode] = {}
        self._create_nodes()

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _build_panel_rect(self) -> pygame.Rect:
        panel_width = int(self.width * 0.85)
        panel_height = int(self.height * 0.85)
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2
        return pygame.Rect(panel_x, panel_y, panel_width, panel_height)

    def _build_sections(self) -> Dict[str, pygame.Rect]:
        margin = 20
        header = 70
        section_width = (self.panel_rect.width - margin * 3) // 2
        section_height = (self.panel_rect.height - header - margin * 3) // 2

        sections = {}
        sections["resource"] = pygame.Rect(
            self.panel_rect.x + margin,
            self.panel_rect.y + header,
            section_width,
            section_height,
        )
        sections["turret"] = pygame.Rect(
            sections["resource"].right + margin,
            sections["resource"].y,
            section_width,
            section_height,
        )
        sections["npc"] = pygame.Rect(
            self.panel_rect.x + margin,
            sections["resource"].bottom + margin,
            section_width,
            section_height,
        )
        sections["base"] = pygame.Rect(
            sections["npc"].right + margin,
            sections["npc"].y,
            section_width,
            section_height,
        )
        return sections

    # ------------------------------------------------------------------
    # Node creation
    # ------------------------------------------------------------------
    def _create_nodes(self):
        node_specs = []

        def add_node(node_id, name, desc, cost, category, rel_x, rel_y, parents):
            section = self.sections[category]
            pos = (section.x + rel_x, section.y + rel_y)
            state = GLOBAL_NODE_STATES.get(node_id, "locked")
            node_specs.append(ResearchNode(node_id, name, desc, cost, pos, parents, category, state))

        # Resource tree
        add_node("sawmill", "Sawmill", "Unlock sawmill building.", 100, "resource", 140, 90, [])
        add_node("adv_wood", "Advanced Woodcutting", "+15% wood income.", 200, "resource", 330, 90, ["sawmill"])
        add_node("lumber_bot", "Auto Lumber Bot", "Automated wood harvesting.", 350, "resource", 520, 90, ["adv_wood"])

        add_node("smelter", "Smelter", "Unlock smelter building.", 120, "resource", 140, 230, [])
        add_node("alloy", "Alloy Research", "Improved iron yield.", 220, "resource", 330, 230, ["smelter"])
        add_node("forge", "High-Tech Forge", "Unlock high tier materials.", 380, "resource", 520, 230, ["alloy"])

        # Turret tree (vertical)
        turret_section = self.sections["turret"]
        tx = turret_section.centerx - turret_section.x
        add_node("turret_t1", "Tier 1 Turret", "Basic projectile turret.", 150, "turret", tx, 80, [])
        add_node("turret_t2", "Tier 2 Turret", "Enhanced damage.", 250, "turret", tx, 190, ["turret_t1"])
        add_node("railgun", "Railgun Turret", "Long-range piercing shot.", 400, "turret", tx, 300, ["turret_t2"])
        add_node("flamethrower", "Flamethrower Tower", "Area denial flames.", 500, "turret", tx, 410, ["railgun"])

        # NPC tree (horizontal)
        npc_section = self.sections["npc"]
        npc_y = npc_section.y + npc_section.height // 2
        add_node("worker_plus", "Worker NPC +1", "Add another worker slot.", 120, "npc", 120, npc_y - npc_section.y, [])
        add_node("npc_eff", "NPC Efficiency +10%", "Workers gather faster.", 220, "npc", 310, npc_y - npc_section.y, ["worker_plus"])
        add_node("gather_speed", "Gathering Speed +20%", "Further gather boost.", 320, "npc", 500, npc_y - npc_section.y, ["npc_eff"])
        add_node("combat_npc", "Combat NPC", "Unlock guard NPC patrol.", 420, "npc", 690, npc_y - npc_section.y, ["gather_speed"])

        # HQ/Base tree
        base_section = self.sections["base"]
        add_node("hq_reinforce", "HQ Reinforcement", "+20% HQ HP.", 180, "base", 150, 90, [])
        add_node("perimeter", "Perimeter Walls", "Unlock perimeter upgrades.", 260, "base", 150, 210, ["hq_reinforce"])
        add_node("auto_repair", "Auto-Repair System", "Slow passive repairs.", 320, "base", 320, 330, ["perimeter"])
        add_node("radar", "Radar System", "Reveal incoming hordes.", 320, "base", 480, 330, ["perimeter"])

        for node in node_specs:
            self.nodes[node.node_id] = node

        self.update_node_states(force=True)

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def update_node_states(self, force: bool = False):
        coins = getattr(self.resources, "coins", 0)
        for node in self.nodes.values():
            if GLOBAL_NODE_STATES.get(node.node_id) == "unlocked":
                node.state = "unlocked"
                continue

            parent_unlocked = all(
                self.nodes[parent_id].state == "unlocked" for parent_id in node.parents
            )
            if not node.parents:
                parent_unlocked = True

            if parent_unlocked:
                node.state = "unlockable" if coins >= node.cost else "locked"
            else:
                node.state = "locked"

        if force:
            for node in self.nodes.values():
                saved_state = GLOBAL_NODE_STATES.get(node.node_id)
                if saved_state == "unlocked":
                    node.state = "unlocked"

    def attempt_unlock(self, node: ResearchNode):
        if node.state != "unlockable":
            return
        if getattr(self.resources, "coins", 0) < node.cost:
            return
        if not self.resources.spend_coins(node.cost):
            return

        node.state = "unlocked"
        GLOBAL_NODE_STATES[node.node_id] = "unlocked"
        self.apply_research_effect(node)
        self.update_node_states()

    def apply_research_effect(self, node: ResearchNode):
        """Placeholder hook for future gameplay integration."""
        if self.research_manager:
            self.research_manager.unlocked.add(node.node_id)

        if self.world:
            targets = RESEARCH_BUILDING_UPGRADES.get(node.node_id, [])
            for building_type, level in targets:
                if hasattr(self.world, "upgrade_buildings"):
                    self.world.upgrade_buildings(building_type, level)
        print(f"[ResearchTree] Unlocked {node.name}")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def open_loop(self):
        was_paused = self.game_state_manager.is_paused() if self.game_state_manager else False
        if self.game_state_manager and not was_paused:
            self.game_state_manager.pause()

        self.running = True
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            pygame.display.flip()

        if self.game_state_manager and not was_paused:
            self.game_state_manager.resume()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_r):
                self.running = False
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if event.button == 3:  # Right-click closes
                self.running = False
                return
            if event.button == 1:
                for node in self.nodes.values():
                    if node.rect.collidepoint(mouse_pos):
                        self.attempt_unlock(node)
                        break

        if event.type == pygame.MOUSEMOTION:
            self._update_hover_node(event.pos)

    def update(self, dt: float):
        self.update_node_states()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        panel.fill(PANEL_COLOR)
        self.screen.blit(panel, self.panel_rect)
        pygame.draw.rect(self.screen, SECTION_BORDER, self.panel_rect, 3)

        title = self.font_large.render("RESEARCH TREE", True, (255, 255, 255))
        self.screen.blit(title, (self.panel_rect.centerx - title.get_width() // 2, self.panel_rect.y + 20))

        coins_text = self.font_medium.render(f"Coins: {int(getattr(self.resources, 'coins', 0))}", True, (255, 215, 0))
        self.screen.blit(coins_text, (self.panel_rect.x + 30, self.panel_rect.y + 30))

        section_titles = {
            "resource": "RESOURCE TREE",
            "turret": "TURRET TREE",
            "npc": "NPC TREE",
            "base": "HQ / BASE TREE",
        }

        for key, rect in self.sections.items():
            pygame.draw.rect(self.screen, SECTION_BG, rect)
            pygame.draw.rect(self.screen, SECTION_BORDER, rect, 2)
            label = self.font_medium.render(section_titles[key], True, TEXT_COLOR)
            self.screen.blit(label, (rect.centerx - label.get_width() // 2, rect.y - 28))

        self._draw_connections()
        self._draw_nodes()
        self._draw_tooltip()

        hint = self.font_small.render("Press ESC or Right Click to close", True, (180, 180, 180))
        self.screen.blit(
            hint,
            (self.panel_rect.centerx - hint.get_width() // 2, self.panel_rect.bottom - 30),
        )

    def _draw_connections(self):
        for node in self.nodes.values():
            for parent_id in node.parents:
                parent = self.nodes[parent_id]
                if node.state == "unlocked" and parent.state == "unlocked":
                    color = LINE_UNLOCKED
                elif node.state == "unlockable" and parent.state == "unlocked":
                    color = LINE_UNLOCKABLE
                else:
                    color = LINE_LOCKED
                start = parent.rect.center
                end = node.rect.center
                pygame.draw.line(self.screen, color, start, end, 4)

    def _draw_nodes(self):
        mouse_pos = pygame.mouse.get_pos()
        self._update_hover_node(mouse_pos)

        for node in self.nodes.values():
            if node.state == "unlocked":
                fill = UNLOCKED_FILL
                border = UNLOCKED_BORDER
            elif node.state == "unlockable":
                fill = UNLOCKABLE_FILL
                border = UNLOCKABLE_BORDER
            else:
                fill = LOCKED_FILL
                border = LOCKED_BORDER

            pygame.draw.rect(self.screen, fill, node.rect)
            pygame.draw.rect(self.screen, border, node.rect, 3)

            if node.state == "unlocked":
                check = self.font_small.render("✓", True, (255, 255, 255))
                self.screen.blit(check, (node.rect.right - 18, node.rect.y + 8))

            icon = ICON_MAP.get(node.node_id)
            if icon:
                icon_rect = icon.get_rect()
                icon_rect.centery = node.rect.centery
                icon_rect.x = node.rect.x + 6
                self.screen.blit(icon, icon_rect)
                text_x = icon_rect.right + 6
            else:
                text_x = node.rect.centerx - NODE_WIDTH // 2 + 10

            name_surface = self.font_small.render(node.name, True, TEXT_COLOR)
            self.screen.blit(name_surface, (text_x, node.rect.y + 8))
            cost_surface = self.font_small.render(f"{node.cost} c", True, (200, 200, 200))
            self.screen.blit(cost_surface, (text_x, node.rect.y + 30))

            if node == self.hover_node:
                pygame.draw.rect(self.screen, (255, 255, 255), node.rect, 2)

    def _update_hover_node(self, mouse_pos: Tuple[int, int]):
        self.hover_node = None
        for node in self.nodes.values():
            if node.rect.collidepoint(mouse_pos):
                self.hover_node = node
                break

    def _draw_tooltip(self):
        node = self.hover_node
        if not node:
            return

        lines = [
            node.name,
            node.description,
            f"Cost: {node.cost} coins",
            f"State: {node.state.title()}",
        ]
        padding = 8
        width = max(self.font_small.render(line, True, TEXT_COLOR).get_width() for line in lines) + padding * 2
        height = len(lines) * 20 + padding * 2

        tooltip_rect = pygame.Rect(
            min(max(node.rect.centerx - width // 2, self.panel_rect.x + 10), self.panel_rect.right - width - 10),
            self.panel_rect.bottom - height - 20,
            width,
            height,
        )
        pygame.draw.rect(self.screen, TOOLTIP_BG, tooltip_rect)
        pygame.draw.rect(self.screen, TOOLTIP_BORDER, tooltip_rect, 2)

        y = tooltip_rect.y + padding
        for line in lines:
            surf = self.font_small.render(line, True, TEXT_COLOR)
            self.screen.blit(surf, (tooltip_rect.x + padding, y))
            y += 20


def open_research_tree(screen, world, research_manager=None, game_state_manager=None):
    """Helper to create the ResearchTreeUI and open it."""
    ui = ResearchTreeUI(screen, world, research_manager, game_state_manager)
    ui.open_loop()

