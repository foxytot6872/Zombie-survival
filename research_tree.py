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
SECTION_BG = (32, 32, 32)  # Darker background (#202020)
SECTION_BORDER = (100, 100, 100)  # Thicker borders
TEXT_COLOR = (220, 220, 220)
LOCKED_FILL = (40, 40, 40)  # Dark gray for locked
LOCKED_BORDER = (80, 80, 80)
LOCKED_UNAFFORDABLE_FILL = (25, 25, 25)  # Darker gray for unaffordable
LOCKED_UNAFFORDABLE_BORDER = (60, 60, 60)
UNLOCKABLE_FILL = (200, 200, 50)  # Yellow for unlockable
UNLOCKABLE_BORDER = (240, 240, 120)
UNLOCKED_FILL = (60, 120, 60)  # Green for unlocked
UNLOCKED_BORDER = (120, 220, 120)
LINE_LOCKED = (60, 60, 60, 80)  # Semi-transparent
LINE_UNLOCKABLE = (100, 200, 120, 80)
LINE_UNLOCKED = (120, 220, 120, 80)
TOOLTIP_BG = (20, 20, 20)
TOOLTIP_BORDER = (140, 140, 140)

NODE_WIDTH = 220  # From provided node sheet frame size
NODE_HEIGHT = 90  # From provided node sheet frame size
NODE_RADIUS = 6  # Rounded corners
ICON_SIZE = 40
DEBUG_RESEARCH_SPRITES = True  # Enable debug logs for missing node sprites


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

RESEARCH_BUILDING_UPGRADES: Dict[str, List[Tuple[str, int]]] = {}

# Persist node states between openings (deprecated - now uses ResearchManager)
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
    tier: int = 1
    state: str = "locked"
    rect: pygame.Rect = field(init=False)
    scale: float = 1.0  # For unlock animation
    flash_timer: float = 0.0  # For click feedback
    flash_color: Optional[Tuple[int, int, int]] = None

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
        
        # Animation state
        self.fade_alpha = 0.0
        self.fade_direction = 1.0  # 1.0 = fading in, -1.0 = fading out
        self.zoom_scale = 1.0
        
        # Fonts
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 26)
        self.font_large = pygame.font.Font(None, 36)
        self.font_bold = pygame.font.Font(None, 24)  # For node names

        self.panel_rect = self._build_panel_rect()
        # Optional panel image background (reuse ResearchPanel look)
        self.panel_image = None
        try:
            import os
            img_path = os.path.join('asset', 'hud', 'ResearchPanel.png')
            if os.path.exists(img_path):
                self.panel_image = pygame.image.load(img_path).convert_alpha()
        except Exception:
            self.panel_image = None
        self.sections = self._build_sections()
        self.nodes: Dict[str, ResearchNode] = {}
        self.node_sprites: Dict[str, pygame.Surface] = {}
        self._missing_sprite_logged = set()
        self._create_nodes_from_json()

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
        padding = 8
        section_width = (self.panel_rect.width - margin * 3) // 2
        section_height = (self.panel_rect.height - header - margin * 2)

        sections = {}
        sections["agriculture"] = pygame.Rect(
            self.panel_rect.x + margin + padding,
            self.panel_rect.y + header + padding,
            section_width - padding * 2,
            section_height - padding * 2,
        )
        sections["ballistic"] = pygame.Rect(
            sections["agriculture"].right + margin + padding * 2,
            sections["agriculture"].y,
            section_width - padding * 2,
            section_height - padding * 2,
        )
        return sections

    # ------------------------------------------------------------------
    # Node creation from JSON
    # ------------------------------------------------------------------
    def _create_nodes_from_json(self):
        """Load nodes from research.json and position them by branch and tier."""
        if not self.research_manager:
            print("Warning: No research manager provided, cannot load research tree")
            return

        research_defs = self.research_manager.research_defs

        def get_branch(node_id: str, seen=None) -> str:
            """Determine branch by tracing prerequisites to root."""
            if seen is None:
                seen = set()
            if node_id in seen:
                return "agriculture"
            seen.add(node_id)
            if node_id in ("agriculture", "ballistic_engineering"):
                return "agriculture" if node_id == "agriculture" else "ballistic"
            data = research_defs.get(node_id, {})
            parents = data.get("prerequisites", [])
            for p in parents:
                branch = get_branch(p, seen)
                if branch in ("agriculture", "ballistic"):
                    return branch
            return "agriculture"

        # Group by branch and tier
        by_branch_tier: Dict[str, Dict[int, List[Tuple[str, Dict]]]] = {"agriculture": {}, "ballistic": {}}
        for key, data in research_defs.items():
            tier = data.get("tier", 1)
            branch = get_branch(key)
            if tier not in by_branch_tier[branch]:
                by_branch_tier[branch][tier] = []
            by_branch_tier[branch][tier].append((key, data))

        # Layout: 5 tiers vertically per section
        for branch, section_rect in self.sections.items():
            tier_items = by_branch_tier.get(branch, {})
            if not tier_items:
                continue
            max_tier = 5
            tier_spacing = (section_rect.height - 16) // max(1, max_tier)
            padding = 8

            for tier in range(1, max_tier + 1):
                items = tier_items.get(tier, [])
                if not items:
                    continue
                # Horizontal layout within tier
                item_spacing = (section_rect.width - 16) // max(1, len(items))
                y_pos = section_rect.y + padding + (tier - 1) * tier_spacing + tier_spacing // 2

                for idx, (key, data) in enumerate(items):
                    x_pos = section_rect.x + padding + idx * item_spacing + item_spacing // 2
                    node = ResearchNode(
                        node_id=key,
                        name=data.get("name", key),
                        description=data.get("description", ""),
                        cost=data.get("cost", data.get("cost_coins", 0)),
                        position=(x_pos, y_pos),
                        parents=data.get("prerequisites", []),
                        category=branch,
                        tier=tier,
                    )
                    self.nodes[key] = node
                    # Preload node sprite
                    self._ensure_node_sprite_loaded(key)

        self.update_node_states(force=True)

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def update_node_states(self, force: bool = False):
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
            )
            if not node.parents:
                parent_unlocked = True

            if parent_unlocked:
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
        print(f"[ResearchTree] Unlocked {node.name}")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def open_loop(self):
        """Open the research tree with fade-in animation."""
        was_paused = self.game_state_manager.is_paused() if self.game_state_manager else False
        if self.game_state_manager and not was_paused:
            self.game_state_manager.pause()

        self.running = True
        self.fade_alpha = 0.0
        self.fade_direction = 1.0
        
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
                self.fade_direction = -1.0  # Start fade out
                return
            # Zoom controls
            if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.zoom_scale = min(1.1, self.zoom_scale + 0.1)
            elif event.key == pygame.K_MINUS:
                self.zoom_scale = max(0.9, self.zoom_scale - 0.1)

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
        
        self.update_node_states()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
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

        # Draw panel background (image if available, else fallback box)
        if self.panel_image:
            if self.panel_image.get_size() != (self.panel_rect.width, self.panel_rect.height):
                scaled = pygame.transform.smoothscale(self.panel_image, (self.panel_rect.width, self.panel_rect.height))
                self.screen.blit(scaled, self.panel_rect)
            else:
                self.screen.blit(self.panel_image, self.panel_rect)
        else:
            panel = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
            panel.fill(PANEL_COLOR)
            self.screen.blit(panel, self.panel_rect)
        pygame.draw.rect(self.screen, SECTION_BORDER, self.panel_rect, 3)

        title = self.font_large.render("RESEARCH TREE", True, (255, 255, 255))
        self.screen.blit(title, (self.panel_rect.centerx - title.get_width() // 2, self.panel_rect.y + 20))

        coins_text = self.font_medium.render(f"Coins: {int(getattr(self.resources, 'coins', 0))}", True, (255, 215, 0))
        self.screen.blit(coins_text, (self.panel_rect.x + 30, self.panel_rect.y + 30))

        # ESC hint in top right
        esc_hint = self.font_small.render("Press ESC to close", True, (180, 180, 180))
        self.screen.blit(esc_hint, (self.panel_rect.right - esc_hint.get_width() - 20, self.panel_rect.y + 20))

        section_titles = {
            "agriculture": "AGRICULTURE BRANCH",
            "ballistic": "BALLISTIC ENGINEERING BRANCH",
        }

        for key, rect in self.sections.items():
            # Draw section background with darker color and thicker border
            pygame.draw.rect(self.screen, SECTION_BG, rect)
            pygame.draw.rect(self.screen, SECTION_BORDER, rect, 4)  # Thicker border
            label = self.font_medium.render(section_titles[key], True, TEXT_COLOR)
            self.screen.blit(label, (rect.centerx - label.get_width() // 2, rect.y - 28))
            
            # Draw tier labels
            self._draw_tier_labels(key, rect)

        self._draw_connections()
        self._draw_nodes()
        self._draw_tooltip()
        
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
            if node.category == category:
                tiers.add(node.tier)
        
        if not tiers:
            return
        
        max_tier = 5
        tier_spacing = (section_rect.height - 16) // max(1, max_tier)
        padding = 8
        
        for tier in range(1, max_tier + 1):
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
        mouse_pos = pygame.mouse.get_pos()
        self._update_hover_node(mouse_pos)

        for node in self.nodes.values():
            # Determine frame based on state:
            # 0 = not researched yet (unlockable)
            # 1 = researched (unlocked)
            # 2 = cannot research yet (locked or unaffordable)
            if node.state == "unlocked":
                frame_index = 1
            elif node.state == "unlockable":
                frame_index = 0
            else:
                frame_index = 2

            # Apply scale for unlock animation
            if node.scale != 1.0:
                scaled_rect = pygame.Rect(
                    node.rect.centerx - int(node.rect.width * node.scale) // 2,
                    node.rect.centery - int(node.rect.height * node.scale) // 2,
                    int(node.rect.width * node.scale),
                    int(node.rect.height * node.scale),
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

            # Draw sprite frame
            sprite = self._ensure_node_sprite_loaded(node.node_id)
            if sprite:
                frame_surface = self._get_node_frame(sprite, frame_index)
                if scaled_rect.size != frame_surface.get_size():
                    frame_surface = pygame.transform.smoothscale(frame_surface, scaled_rect.size)
                self.screen.blit(frame_surface, scaled_rect.topleft)
            else:
                # Fallback rectangle if sprite missing
                self._draw_rounded_rect(self.screen, (60, 60, 60), scaled_rect, NODE_RADIUS)
                self._draw_rounded_rect(self.screen, (120, 120, 120), scaled_rect, NODE_RADIUS, 2)

            # Flash effect
            if node.flash_timer > 0 and node.flash_color:
                flash_alpha = int(255 * (node.flash_timer / 0.15))
                flash_surface = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
                flash_surface.fill((*node.flash_color, flash_alpha))
                self.screen.blit(flash_surface, scaled_rect.topleft)
                self._draw_rounded_rect(self.screen, node.flash_color, scaled_rect, NODE_RADIUS, 3)

            # Hover highlight
            if node == self.hover_node:
                outline = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
                outline.fill((255, 255, 255, 30))
                self.screen.blit(outline, scaled_rect.topleft)
                self._draw_rounded_rect(self.screen, (255, 255, 255), scaled_rect, NODE_RADIUS, 2)

    def _update_hover_node(self, mouse_pos: Tuple[int, int]):
        self.hover_node = None
        for node in self.nodes.values():
            if node.rect.collidepoint(mouse_pos):
                self.hover_node = node
                break

    def _draw_tooltip(self):
        """Draw tooltip with description when hovering over node."""
        node = self.hover_node
        if not node:
            return

        lines = [node.name]
        if node.description:
            lines.append(node.description)
        if node.cost and node.state != "unlocked":
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
            width,
            height,
        )
        pygame.draw.rect(self.screen, TOOLTIP_BG, tooltip_rect)
        pygame.draw.rect(self.screen, TOOLTIP_BORDER, tooltip_rect, 2)

        y = tooltip_rect.y + padding
        for line in lines:
            if line:  # Skip empty lines
                surf = self.font_small.render(line, True, TEXT_COLOR)
                self.screen.blit(surf, (tooltip_rect.x + padding, y))
                y += 20

    # ------------------------------------------------------------------
    # Sprite helpers
    # ------------------------------------------------------------------
    def _ensure_node_sprite_loaded(self, node_id: str) -> Optional[pygame.Surface]:
        """Load and cache the spritesheet for a node if available."""
        if node_id in self.node_sprites:
            return self.node_sprites[node_id]
        # Try to load from asset/hud/ResearchNode/{node_id}.png
        import os
        # First, try new naming scheme: PascalCase + 'Node-Sheet.png'
        filename_new = self._node_id_to_sprite_filename(node_id)
        candidates = [
            os.path.join("asset", "hud", "ResearchNode", filename_new),
            # Fallbacks: lowercase id-based names as previously
            os.path.join("asset", "hud", "ResearchNode", f"{node_id}.png"),
            os.path.join("asset", "hud", "ResearchNode", f"{node_id}.PNG"),
        ]
        surface = None
        for path in candidates:
            try:
                if os.path.exists(path):
                    surface = pygame.image.load(path).convert_alpha()
                    break
            except Exception:
                continue
        if surface is None:
            self.node_sprites[node_id] = None
            if DEBUG_RESEARCH_SPRITES and node_id not in self._missing_sprite_logged:
                print(f"[ResearchTreeUI] WARNING: No sprite found for node '{node_id}'. Tried filenames:")
                for p in candidates:
                    print(f"  - {p}")
                self._missing_sprite_logged.add(node_id)
            return None
        self.node_sprites[node_id] = surface
        return surface

    def _get_node_frame(self, sheet: pygame.Surface, frame_index: int) -> pygame.Surface:
        """Extract a frame from a 3-frame horizontal spritesheet (220x90 each)."""
        frame_index = max(0, min(2, frame_index))
        frame_w, frame_h = NODE_WIDTH, NODE_HEIGHT
        x = frame_index * frame_w
        rect = pygame.Rect(x, 0, frame_w, frame_h)
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), rect)
        return frame

    def _node_id_to_sprite_filename(self, node_id: str) -> str:
        """
        Convert a snake_case node_id to PascalCase 'NameNode-Sheet.png' with overrides.
        Examples:
          - agriculture -> ArgricultureNode-Sheet.png (override spelling)
          - ballistic_engineering -> BalisticEngineeringNode-Sheet.png (override spelling)
          - advanced_fire_control_system -> AdvanceControlSystemNode-Sheet.png (override form)
          - basic_woodworking -> BasicWoodworkingNode-Sheet.png
        """
        overrides = {
            "agriculture": "ArgricultureNode-Sheet.png",
            "ballistic_engineering": "BalisticEngineeringNode-Sheet.png",
            "advanced_fire_control_system": "AdvanceControlSystemNode-Sheet.png",
            "sleeping_quarters": "SleepingQuarterNode-Sheet.png",
            "recruitment": "RecruimentNode-Sheet.png",
            "structural_reinforcement": "StructuralReinforcement-Sheet.png",
            "refined_alloy_techniques": "RefinedAlloyTechniqueNode-Sheet.png",
            "combat_droids": "CombatDroidNode-Sheet.png",
            "improved_target_acquisition": "ImproveTargetAquisitionNode-Sheet.png",
            "flamethrower_tech": "FlamethrowerTech-Sheet.png",
            "electromagnetic_rail_system": "EletromagneticRailSystem-Sheet.png",
            "advanced_wood_processing": "AdvanceWoodProcessing-Sheet.png",
        }
        if node_id in overrides:
            return overrides[node_id]

        # Default conversion: snake_case -> PascalCase + 'Node-Sheet.png'
        parts = [p for p in node_id.split("_") if p]
        pascal = "".join(part.capitalize() for part in parts)
        return f"{pascal}Node-Sheet.png"


def open_research_tree(screen, world, research_manager=None, game_state_manager=None):
    """Helper to create the ResearchTreeUI and open it."""
    ui = ResearchTreeUI(screen, world, research_manager, game_state_manager)
    ui.open_loop()

