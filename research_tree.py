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
<<<<<<< Updated upstream
SECTION_BG = (32, 32, 32)  # Darker background (#202020)
SECTION_BORDER = (100, 100, 100)  # Thicker borders
TEXT_COLOR = (220, 220, 220)
LOCKED_FILL = (40, 40, 40)  # Dark gray for locked
LOCKED_BORDER = (80, 80, 80)
LOCKED_UNAFFORDABLE_FILL = (25, 25, 25)  # Darker gray for unaffordable
LOCKED_UNAFFORDABLE_BORDER = (60, 60, 60)
UNLOCKABLE_FILL = (50, 100, 50)  # Light green for unlockable
UNLOCKABLE_BORDER = (100, 200, 120)
UNLOCKED_FILL = (60, 120, 60)  # Green for unlocked
UNLOCKED_BORDER = (120, 220, 120)
LINE_LOCKED = (60, 60, 60, 80)  # Semi-transparent
LINE_UNLOCKABLE = (100, 200, 120, 80)
LINE_UNLOCKED = (120, 220, 120, 80)
TOOLTIP_BG = (20, 20, 20)
TOOLTIP_BORDER = (140, 140, 140)

NODE_WIDTH = 180  # 20% bigger (150 * 1.2)
NODE_HEIGHT = 72  # 20% bigger (60 * 1.2)
NODE_RADIUS = 6  # Rounded corners
=======
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
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
# Persist node states between openings (deprecated - now uses ResearchManager)
=======
# Persist node states between openings
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    tier: int = 1
    state: str = "locked"
    rect: pygame.Rect = field(init=False)
    scale: float = 1.0  # For unlock animation
    flash_timer: float = 0.0  # For click feedback
    flash_color: Optional[Tuple[int, int, int]] = None
=======
    state: str = "locked"
    rect: pygame.Rect = field(init=False)
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
        
        # Animation state
        self.fade_alpha = 0.0
        self.fade_direction = 1.0  # 1.0 = fading in, -1.0 = fading out
        self.zoom_scale = 1.0
        
        # Fonts
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 26)
        self.font_large = pygame.font.Font(None, 36)
        self.font_bold = pygame.font.Font(None, 24)  # For node names
=======

        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 26)
        self.font_large = pygame.font.Font(None, 36)
>>>>>>> Stashed changes

        self.panel_rect = self._build_panel_rect()
        self.sections = self._build_sections()
        self.nodes: Dict[str, ResearchNode] = {}
<<<<<<< Updated upstream
        self._create_nodes_from_json()
=======
        self._create_nodes()
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
        padding = 8  # Internal padding for sections

        sections = {}
        sections["resource"] = pygame.Rect(
            self.panel_rect.x + margin + padding,
            self.panel_rect.y + header + padding,
            section_width - padding * 2,
            section_height - padding * 2,
        )
        sections["turret"] = pygame.Rect(
            sections["resource"].right + margin + padding * 2,
            sections["resource"].y,
            section_width - padding * 2,
            section_height - padding * 2,
        )
        sections["npc"] = pygame.Rect(
            self.panel_rect.x + margin + padding,
            sections["resource"].bottom + margin + padding * 2,
            section_width - padding * 2,
            section_height - padding * 2,
        )
        sections["base"] = pygame.Rect(
            sections["npc"].right + margin + padding * 2,
            sections["npc"].y,
            section_width - padding * 2,
            section_height - padding * 2,
=======

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
>>>>>>> Stashed changes
        )
        return sections

    # ------------------------------------------------------------------
<<<<<<< Updated upstream
    # Node creation from JSON
    # ------------------------------------------------------------------
    def _create_nodes_from_json(self):
        """Load nodes from research.json and position them by tier."""
        if not self.research_manager:
            print("Warning: No research manager provided, cannot load research tree")
            return
        
        research_defs = self.research_manager.research_defs
        
        # Group by category and tier
        by_category_tier: Dict[str, Dict[int, List[Tuple[str, Dict]]]] = {
            "resource": {}, "turret": {}, "npc": {}, "base": {}, "hq": {}
        }
        
        for key, data in research_defs.items():
            category = data.get("category", "resource")
            tier = data.get("tier", 1)
            if category not in by_category_tier:
                category = "resource"  # Fallback
            if tier not in by_category_tier[category]:
                by_category_tier[category][tier] = []
            by_category_tier[category][tier].append((key, data))
        
        # Position nodes within sections by tier
        for category, section_rect in self.sections.items():
            if category == "base":
                # Merge hq and base
                hq_items = by_category_tier.get("hq", {})
                base_items = by_category_tier.get("base", {})
                all_items = {}
                for tier in set(list(hq_items.keys()) + list(base_items.keys())):
                    all_items[tier] = (hq_items.get(tier, []) + base_items.get(tier, []))
                tier_items = all_items
            else:
                tier_items = by_category_tier.get(category, {})
            
            if not tier_items:
                continue
            
            # Calculate positions: tier 1 at top, tier 4 at bottom
            max_tier = max(tier_items.keys()) if tier_items else 1
            tier_spacing = (section_rect.height - 16) // max(1, max_tier)
            padding = 8
            
            for tier in sorted(tier_items.keys()):
                items = tier_items[tier]
                # Horizontal layout within tier
                item_spacing = (section_rect.width - 16) // max(1, len(items))
                y_pos = section_rect.y + padding + (tier - 1) * tier_spacing + tier_spacing // 2
                
                for idx, (key, data) in enumerate(items):
                    x_pos = section_rect.x + padding + idx * item_spacing + item_spacing // 2
                    
                    node = ResearchNode(
                        node_id=key,
                        name=data.get("name", key),
                        description=data.get("description", ""),
                        cost=data.get("cost_coins", 0),
                        position=(x_pos, y_pos),
                        parents=data.get("prerequisites", []),
                        category=category,
                        tier=tier
                    )
                    self.nodes[key] = node
        
=======
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

>>>>>>> Stashed changes
        self.update_node_states(force=True)

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def update_node_states(self, force: bool = False):
<<<<<<< Updated upstream
        """Update node states based on ResearchManager and prerequisites."""
        coins = getattr(self.resources, "coins", 0)
        
        for node in self.nodes.values():
            # Check if purchased in ResearchManager
            if self.research_manager and self.research_manager.is_research_purchased(node.node_id):
                node.state = "unlocked"
                continue
            
            # Check prerequisites
            parent_unlocked = all(
                (self.research_manager and self.research_manager.is_research_purchased(parent_id)) or
                (parent_id in self.nodes and self.nodes[parent_id].state == "unlocked")
                for parent_id in node.parents
=======
        coins = getattr(self.resources, "coins", 0)
        for node in self.nodes.values():
            if GLOBAL_NODE_STATES.get(node.node_id) == "unlocked":
                node.state = "unlocked"
                continue

            parent_unlocked = all(
                self.nodes[parent_id].state == "unlocked" for parent_id in node.parents
>>>>>>> Stashed changes
            )
            if not node.parents:
                parent_unlocked = True

            if parent_unlocked:
<<<<<<< Updated upstream
                if coins >= node.cost:
                    node.state = "unlockable"
                else:
                    node.state = "locked_unaffordable"  # Can't afford
            else:
                node.state = "locked"  # Prerequisites not met

    def attempt_unlock(self, node: ResearchNode):
        """Attempt to unlock a research node."""
        coins = getattr(self.resources, "coins", 0)
        
        # Check prerequisites
        if node.state == "locked":
            # Prerequisites not met - red flash
            node.flash_timer = 0.15
            node.flash_color = (255, 0, 0)
            return
        
        # Check affordability
        if coins < node.cost:
            # Can't afford - yellow flash
            node.flash_timer = 0.15
            node.flash_color = (255, 255, 0)
            return
        
        # Try to unlock via ResearchManager
        if self.research_manager and self.research_manager.unlock(node.node_id):
            # Success - animate unlock
            node.state = "unlocked"
            node.scale = 1.1  # Start animation
            node.flash_timer = 0.0
            self._play_unlock_sound()
            self.update_node_states()
        else:
            # Failed (shouldn't happen if checks passed)
            node.flash_timer = 0.15
            node.flash_color = (255, 0, 0)
    
    def _play_unlock_sound(self):
        """Placeholder for unlock sound."""
        # TODO: Integrate with sound system
        pass

    def apply_research_effect(self, node: ResearchNode):
        """Apply research effects (now handled by ResearchManager.unlock)."""
        # Effects are now applied in ResearchManager.unlock()
=======
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
>>>>>>> Stashed changes
        print(f"[ResearchTree] Unlocked {node.name}")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def open_loop(self):
<<<<<<< Updated upstream
        """Open the research tree with fade-in animation."""
=======
>>>>>>> Stashed changes
        was_paused = self.game_state_manager.is_paused() if self.game_state_manager else False
        if self.game_state_manager and not was_paused:
            self.game_state_manager.pause()

        self.running = True
<<<<<<< Updated upstream
        self.fade_alpha = 0.0
        self.fade_direction = 1.0
        
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
                self.fade_direction = -1.0  # Start fade out
                return
            # Zoom controls
            if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.zoom_scale = min(1.1, self.zoom_scale + 0.1)
            elif event.key == pygame.K_MINUS:
                self.zoom_scale = max(0.9, self.zoom_scale - 0.1)
=======
                self.running = False
                return
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
        """Update animations and node states."""
        # Fade animation
        if self.fade_direction > 0:  # Fading in
            self.fade_alpha = min(255, self.fade_alpha + dt * 1700)  # 150ms to fade in
        else:  # Fading out
            self.fade_alpha = max(0, self.fade_alpha - dt * 1700)
            if self.fade_alpha <= 0:
                self.running = False
        
        # Update node animations
        for node in self.nodes.values():
            # Unlock scale animation
            if node.scale > 1.0:
                node.scale = max(1.0, node.scale - dt * 1.0)  # 0.1s to return to normal
            
            # Flash timer
            if node.flash_timer > 0:
                node.flash_timer = max(0, node.flash_timer - dt)
                if node.flash_timer <= 0:
                    node.flash_color = None
        
=======
>>>>>>> Stashed changes
        self.update_node_states()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
<<<<<<< Updated upstream
        # Apply fade
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((*OVERLAY_COLOR[:3], int(self.fade_alpha * OVERLAY_COLOR[3] / 255)))
        self.screen.blit(overlay, (0, 0))

        # Apply zoom (simple scale - center the panel)
        if self.zoom_scale != 1.0:
            # Create scaled surface
            scaled_width = int(self.panel_rect.width * self.zoom_scale)
            scaled_height = int(self.panel_rect.height * self.zoom_scale)
            scaled_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
            # Draw to scaled surface (we'll handle this by adjusting coordinates)
            # For simplicity, we'll just adjust the panel rect
            zoom_offset_x = (self.panel_rect.width - scaled_width) // 2
            zoom_offset_y = (self.panel_rect.height - scaled_height) // 2
        else:
            zoom_offset_x = 0
            zoom_offset_y = 0

=======
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

>>>>>>> Stashed changes
        panel = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        panel.fill(PANEL_COLOR)
        self.screen.blit(panel, self.panel_rect)
        pygame.draw.rect(self.screen, SECTION_BORDER, self.panel_rect, 3)

        title = self.font_large.render("RESEARCH TREE", True, (255, 255, 255))
        self.screen.blit(title, (self.panel_rect.centerx - title.get_width() // 2, self.panel_rect.y + 20))

        coins_text = self.font_medium.render(f"Coins: {int(getattr(self.resources, 'coins', 0))}", True, (255, 215, 0))
        self.screen.blit(coins_text, (self.panel_rect.x + 30, self.panel_rect.y + 30))

<<<<<<< Updated upstream
        # ESC hint in top right
        esc_hint = self.font_small.render("Press ESC to close", True, (180, 180, 180))
        self.screen.blit(esc_hint, (self.panel_rect.right - esc_hint.get_width() - 20, self.panel_rect.y + 20))

=======
>>>>>>> Stashed changes
        section_titles = {
            "resource": "RESOURCE TREE",
            "turret": "TURRET TREE",
            "npc": "NPC TREE",
            "base": "HQ / BASE TREE",
        }

        for key, rect in self.sections.items():
<<<<<<< Updated upstream
            # Draw section background with darker color and thicker border
            pygame.draw.rect(self.screen, SECTION_BG, rect)
            pygame.draw.rect(self.screen, SECTION_BORDER, rect, 4)  # Thicker border
            label = self.font_medium.render(section_titles[key], True, TEXT_COLOR)
            self.screen.blit(label, (rect.centerx - label.get_width() // 2, rect.y - 28))
            
            # Draw tier labels
            self._draw_tier_labels(key, rect)
=======
            pygame.draw.rect(self.screen, SECTION_BG, rect)
            pygame.draw.rect(self.screen, SECTION_BORDER, rect, 2)
            label = self.font_medium.render(section_titles[key], True, TEXT_COLOR)
            self.screen.blit(label, (rect.centerx - label.get_width() // 2, rect.y - 28))
>>>>>>> Stashed changes

        self._draw_connections()
        self._draw_nodes()
        self._draw_tooltip()
<<<<<<< Updated upstream
        
        # Minimap placeholder (simple box in bottom right)
        minimap_rect = pygame.Rect(self.panel_rect.right - 120, self.panel_rect.bottom - 80, 100, 60)
        pygame.draw.rect(self.screen, (40, 40, 40), minimap_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), minimap_rect, 2)
        minimap_text = self.font_small.render("Overview", True, (150, 150, 150))
        self.screen.blit(minimap_text, (minimap_rect.centerx - minimap_text.get_width() // 2, minimap_rect.y + 5))

    def _draw_tier_labels(self, category: str, section_rect: pygame.Rect):
        """Draw tier labels inside section."""
        # Get tiers for this category
        tiers = set()
        for node in self.nodes.values():
            if node.category == category or (category == "base" and node.category in ("base", "hq")):
                tiers.add(node.tier)
        
        if not tiers:
            return
        
        max_tier = max(tiers)
        tier_spacing = (section_rect.height - 16) // max(1, max_tier)
        padding = 8
        
        for tier in sorted(tiers):
            y_pos = section_rect.y + padding + (tier - 1) * tier_spacing + tier_spacing // 2
            tier_label = self.font_small.render(f"Tier {tier}", True, (150, 150, 150))
            self.screen.blit(tier_label, (section_rect.x + 5, y_pos - 10))
    
    def _draw_connections(self):
        """Draw connection lines between nodes."""
        for node in self.nodes.values():
            for parent_id in node.parents:
                if parent_id not in self.nodes:
                    continue
                parent = self.nodes[parent_id]
                
                # Determine line color
                if node.state == "unlocked" and parent.state == "unlocked":
                    color = LINE_UNLOCKED[:3]
                elif node.state == "unlockable" and parent.state == "unlocked":
                    color = LINE_UNLOCKABLE[:3]
                else:
                    color = LINE_LOCKED[:3]
                
                start = parent.rect.center
                end = node.rect.center
                
                # Draw semi-transparent line (3px thick)
                line_surface = pygame.Surface((abs(end[0] - start[0]) + 6, abs(end[1] - start[1]) + 6), pygame.SRCALPHA)
                rel_start = (3, 3)
                rel_end = (abs(end[0] - start[0]) + 3, abs(end[1] - start[1]) + 3)
                pygame.draw.line(line_surface, (*color, 80), rel_start, rel_end, 3)
                self.screen.blit(line_surface, (min(start[0], end[0]) - 3, min(start[1], end[1]) - 3))

    def _draw_rounded_rect(self, surface, color, rect, radius, border_width=0):
        """Draw a rounded rectangle (fallback to regular rect if border_radius not supported)."""
        try:
            if border_width > 0:
                pygame.draw.rect(surface, color, rect, border_width, border_radius=radius)
            else:
                pygame.draw.rect(surface, color, rect, 0, border_radius=radius)
        except TypeError:
            # Fallback for older pygame versions
            if border_width > 0:
                pygame.draw.rect(surface, color, rect, border_width)
            else:
                pygame.draw.rect(surface, color, rect)
    
    def _draw_nodes(self):
        """Draw research nodes with improved visuals."""
=======

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
>>>>>>> Stashed changes
        mouse_pos = pygame.mouse.get_pos()
        self._update_hover_node(mouse_pos)

        for node in self.nodes.values():
<<<<<<< Updated upstream
            # Determine colors based on state
=======
>>>>>>> Stashed changes
            if node.state == "unlocked":
                fill = UNLOCKED_FILL
                border = UNLOCKED_BORDER
            elif node.state == "unlockable":
                fill = UNLOCKABLE_FILL
                border = UNLOCKABLE_BORDER
<<<<<<< Updated upstream
            elif node.state == "locked_unaffordable":
                fill = LOCKED_UNAFFORDABLE_FILL
                border = LOCKED_UNAFFORDABLE_BORDER
            else:
                fill = LOCKED_FILL
                border = LOCKED_BORDER
            
            # Apply scale for unlock animation
            if node.scale != 1.0:
                scaled_rect = pygame.Rect(
                    node.rect.centerx - (node.rect.width * node.scale) // 2,
                    node.rect.centery - (node.rect.height * node.scale) // 2,
                    int(node.rect.width * node.scale),
                    int(node.rect.height * node.scale)
                )
            else:
                scaled_rect = node.rect
            
            # Draw drop shadow
            shadow_rect = scaled_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 100))
            self.screen.blit(shadow_surface, shadow_rect.topleft)
            
            # Draw node with rounded corners
            self._draw_rounded_rect(self.screen, fill, scaled_rect, NODE_RADIUS)
            self._draw_rounded_rect(self.screen, border, scaled_rect, NODE_RADIUS, 3)
            
            # Flash effect
            if node.flash_timer > 0 and node.flash_color:
                flash_alpha = int(255 * (node.flash_timer / 0.15))
                flash_surface = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
                flash_surface.fill((*node.flash_color, flash_alpha))
                self.screen.blit(flash_surface, scaled_rect.topleft)
                self._draw_rounded_rect(self.screen, node.flash_color, scaled_rect, NODE_RADIUS, 3)

            # Draw checkmark for unlocked
            if node.state == "unlocked":
                check = self.font_small.render("✓", True, (255, 255, 255))
                self.screen.blit(check, (scaled_rect.right - 20, scaled_rect.y + 8))

            # Center text
            name_surface = self.font_bold.render(node.name, True, TEXT_COLOR)
            name_rect = name_surface.get_rect(centerx=scaled_rect.centerx, y=scaled_rect.y + 12)
            self.screen.blit(name_surface, name_rect)
            
            cost_surface = self.font_small.render(f"{node.cost} c", True, (200, 200, 200))
            cost_rect = cost_surface.get_rect(centerx=scaled_rect.centerx, y=scaled_rect.y + 35)
            self.screen.blit(cost_surface, cost_rect)

            # Hover highlight
            if node == self.hover_node:
                # Brighten background by 10%
                bright_fill = tuple(min(255, int(c * 1.1)) for c in fill[:3])
                hover_surface = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
                hover_surface.fill((*bright_fill, 50))
                self.screen.blit(hover_surface, scaled_rect.topleft)
                # White outline
                self._draw_rounded_rect(self.screen, (255, 255, 255), scaled_rect, NODE_RADIUS, 2)
=======
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
>>>>>>> Stashed changes

    def _update_hover_node(self, mouse_pos: Tuple[int, int]):
        self.hover_node = None
        for node in self.nodes.values():
            if node.rect.collidepoint(mouse_pos):
                self.hover_node = node
                break

    def _draw_tooltip(self):
<<<<<<< Updated upstream
        """Draw tooltip with description when hovering over node."""
=======
>>>>>>> Stashed changes
        node = self.hover_node
        if not node:
            return

<<<<<<< Updated upstream
        lines = [node.name]
        if node.description:
            lines.append(node.description)
        lines.append(f"Cost: {node.cost} coins")
        
        # Add modifier info if available
        if self.research_manager and node.node_id in self.research_manager.research_defs:
            modifiers = self.research_manager.research_defs[node.node_id].get("modifiers", {})
            if modifiers:
                mod_lines = []
                for mod_key, mod_value in modifiers.items():
                    if isinstance(mod_value, (int, float)):
                        if mod_value > 1.0:
                            mod_lines.append(f"+{int((mod_value - 1.0) * 100)}% {mod_key.replace('_', ' ')}")
                        else:
                            mod_lines.append(f"{int((1.0 - mod_value) * 100)}% {mod_key.replace('_', ' ')}")
                if mod_lines:
                    lines.append("")
                    lines.extend(mod_lines)
        
        padding = 8
        width = max(self.font_small.render(line, True, TEXT_COLOR).get_width() for line in lines if line) + padding * 2
        height = len([l for l in lines if l]) * 20 + padding * 2

        tooltip_rect = pygame.Rect(
            min(max(node.rect.centerx - width // 2, self.panel_rect.x + 10), self.panel_rect.right - width - 10),
            node.rect.bottom + 10,  # Below the node
=======
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
>>>>>>> Stashed changes
            width,
            height,
        )
        pygame.draw.rect(self.screen, TOOLTIP_BG, tooltip_rect)
        pygame.draw.rect(self.screen, TOOLTIP_BORDER, tooltip_rect, 2)

        y = tooltip_rect.y + padding
        for line in lines:
<<<<<<< Updated upstream
            if line:  # Skip empty lines
                surf = self.font_small.render(line, True, TEXT_COLOR)
                self.screen.blit(surf, (tooltip_rect.x + padding, y))
                y += 20
=======
            surf = self.font_small.render(line, True, TEXT_COLOR)
            self.screen.blit(surf, (tooltip_rect.x + padding, y))
            y += 20
>>>>>>> Stashed changes


def open_research_tree(screen, world, research_manager=None, game_state_manager=None):
    """Helper to create the ResearchTreeUI and open it."""
    ui = ResearchTreeUI(screen, world, research_manager, game_state_manager)
    ui.open_loop()

