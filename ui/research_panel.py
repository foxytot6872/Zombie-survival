"""
Research panel UI component with node-based tech tree.
"""
import os

import pygame

from research_tree import ResearchNode

# Connection line colors (pixel-art style, thick lines)
# Hex colors converted to RGB: Red #e12c27, Yellow #efcb59, Blue #4ed3ff
LINE_LOCKED = (225, 44, 39)  # Red #e12c27 for not unlocked
LINE_UNLOCKABLE = (239, 203, 89)  # Yellow #efcb59 for unlockable path
LINE_UNLOCKED = (78, 211, 255)  # Blue #4ed3ff for unlocked
LINE_WIDTH = 10  # Thick pixel-art lines


class ResearchPanel:
    """Popup research panel overlay that renders the node-based tech tree over the game."""
    
    def __init__(self, world, research_manager, screen_width: int = 1920, screen_height: int = 1080, font_large=None, font_medium=None, font_small=None, custom_font_yellow=None, yellow_number_frames=None):
        """
        Initialize research panel.
        Args:
            world: World object
            research_manager: ResearchManager instance
            screen_width: Screen width
            screen_height: Screen height
            font_large: Optional pygame.font.Font for large text (defaults to system font)
            font_medium: Optional pygame.font.Font for medium text (defaults to system font)
            font_small: Optional pygame.font.Font for small text (defaults to system font)
            custom_font_yellow: Optional CustomFont for yellow text rendering
            yellow_number_frames: Optional list of yellow number frames (17x22 each, 0-9)
        """
        self.world = world
        self.research = research_manager
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        
        # Load panel background image if available
        self.panel_image = None
        try:
            img_path = os.path.join('asset', 'hud', 'ResearchPanel.png')
            if os.path.exists(img_path):
                self.panel_image = pygame.image.load(img_path).convert_alpha()
        except Exception as e:
            print(f"Warning: Could not load ResearchPanel.png: {e}")
            self.panel_image = None
        
        # Panel dimensions (use native image size if present, otherwise default)
        if self.panel_image:
            panel_width, panel_height = self.panel_image.get_size()
        else:
            panel_width = 900
            panel_height = 700
        panel_x = (screen_width - panel_width) // 2
        panel_y = (screen_height - panel_height) // 2
        self.rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Fonts
        self.font_large = font_large if font_large else pygame.font.Font(None, 36)
        self.font_medium = font_medium if font_medium else pygame.font.Font(None, 28)
        self.font_small = font_small if font_small else pygame.font.Font(None, 24)
        
        # Custom font for coins display
        self.custom_font_yellow = custom_font_yellow
        # Number font frames (17x22 each, 0-9)
        self.yellow_number_frames = yellow_number_frames if yellow_number_frames else []
        
        # Node data (tree inside panel)
        self.nodes = {}  # node_id -> ResearchNode
        self.node_sprites = {}  # node_id -> spritesheet surface
        self._missing_sprite_logged = set()

        # Debug drag state (for interactively positioning nodes)
        self._debug_drag_node = None
        self._debug_drag_offset = (0, 0)
    
    def toggle(self):
        """Toggle panel visibility."""
        self.visible = not self.visible
    
    def hide(self):
        """Hide the panel."""
        self.visible = False
    
    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _build_tree_layout(self):
        """Create nodes at fixed coordinates that match the reference layout (no auto layout)."""
        research_defs = self.research.research_defs
        if not research_defs:
            return
        
        # If nodes already exist, update their prerequisites from JSON (so lines reflect JSON changes)
        if self.nodes:
            for key, node in self.nodes.items():
                if key in research_defs:
                    # Update prerequisites from JSON so connection lines reflect current JSON state
                    node.parents = research_defs[key].get("prerequisites", [])
            return

        # Absolute positions taken from the reference layout (panel artwork coordinates)
        positions = {
            # Agriculture branch
            "agriculture": (511, 155),
            "basic_woodworking": (547, 274),
            "recruitment": (276, 276),
            "sleeping_quarters": (276, 397),
            "perimeter_fortification": (635, 385),
            "advanced_wood_processing": (404, 532),
            "structural_reinforcement": (740, 502),
            "self_sealing_technology": (416, 661),
            "automation": (594, 814),
            "computer_engineering": (976, 782),
            "combat_droids": (674, 951),
            "high_bandwidth": (977, 946),
            "high_heat_forgecraft": (830, 641),
            "refined_alloy_techniques": (958, 353),
            "metalworking_fundamentals": (838, 199),

            # Ballistic branch
            "ballistic_engineering": (1356, 198),
            "multibarrel_mechanism": (1621, 347),
            "advanced_fire_control_system": (1659, 599),
            "improved_target_acquisition": (1387, 452),
            "high_caliber_round": (1116, 520),
            "battle_computer_overclock": (1367, 650),
            "electromagnetic_rail_system": (1276, 866),
            "flamethrower_tech": (1564, 950),
        }

        # Create nodes only for those with defined positions
        for key, data in research_defs.items():
            if key not in positions:
                continue
            x, y = positions[key]
            node = ResearchNode(
                node_id=key,
                name=data.get("name", key),
                description=data.get("description", ""),
                cost=data.get("cost", data.get("cost_coins", 0)),
                position=(x, y),
                parents=data.get("prerequisites", []),
                category="agriculture" if key in (
                    "agriculture",
                    "basic_woodworking",
                    "sleeping_quarters",
                    "metalworking_fundamentals",
                    "perimeter_fortification",
                    "advanced_wood_processing",
                    "self_sealing_technology",
                    "automation",
                    "recruitment",
                    "structural_reinforcement",
                    "refined_alloy_techniques",
                    "high_heat_forgecraft",
                    "computer_engineering",
                    "combat_droids",
                    "high_bandwidth",
                ) else "ballistic",
                tier=data.get("tier", 1),
            )
            self.nodes[key] = node
            self._ensure_node_sprite_loaded(key)

        self._update_node_states()

    def _update_node_states(self):
        """Update node states based on ResearchManager and prerequisites."""
        if not self.nodes:
            return
        coins = self.world.resources.coins
        for node in self.nodes.values():
            if self.research.is_research_purchased(node.node_id):
                node.state = "unlocked"
                continue
            parent_unlocked = all(self.research.is_research_purchased(p) for p in node.parents) if node.parents else True
            if parent_unlocked:
                if coins >= node.cost:
                    node.state = "unlockable"
                else:
                    node.state = "locked_unaffordable"
            else:
                node.state = "locked"

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface, show_ui_rectangles: bool = False):
        """Draw the research panel and the node-based tech tree."""
        if not self.visible:
            return
        
        # Draw semi-transparent background overlay (world remains visible behind)
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # DEBUG: panel placement
        if show_ui_rectangles:
            panel_overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            panel_overlay.fill((128, 255, 128, 80))
            screen.blit(panel_overlay, self.rect)
        
        # Draw panel background using themed asset
        if self.panel_image:
            if self.panel_image.get_size() != (self.rect.width, self.rect.height):
                scaled = pygame.transform.smoothscale(self.panel_image, (self.rect.width, self.rect.height))
                screen.blit(scaled, self.rect)
            else:
                screen.blit(self.panel_image, self.rect)
        else:
            panel_bg = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            panel_bg.fill((40, 40, 40, 240))
            screen.blit(panel_bg, self.rect)
        
        # Coins display in top-left of panel
        coins_value = int(self.world.resources.coins)
        coins_x = self.rect.x + 50
        coins_y = self.rect.y + 50
        
        # Draw "Coins: " label using custom font if available
        label_text = "Coins: "
        if self.custom_font_yellow:
            label_surface = self.custom_font_yellow.render(label_text, True, (255, 215, 0))
        else:
            label_surface = self.font_medium.render(label_text, True, (255, 215, 0))
        screen.blit(label_surface, (coins_x, coins_y))
        
        # Draw coin value using number fonts
        if self.yellow_number_frames and len(self.yellow_number_frames) >= 10:
            # Get font height for vertical centering
            if hasattr(self.font_medium, 'letter_height'):
                font_height = self.font_medium.letter_height
            elif hasattr(self.font_medium, 'get_height'):
                font_height = self.font_medium.get_height()
            else:
                font_height = 28
            # Scale number frames to match font size
            scale_factor = font_height / 22.0 if 22 > 0 else 1.0
            
            number_x = coins_x + label_surface.get_width()
            number_y = coins_y + (font_height - int(22 * scale_factor)) // 2 + 3  # Move down 3px
            
            # Draw number using scaled frames
            number_str = str(coins_value)
            current_x = number_x
            for digit_char in number_str:
                digit = int(digit_char)
                if 0 <= digit <= 9:
                    digit_frame = self.yellow_number_frames[digit]
                    if scale_factor != 1.0:
                        scaled_width = int(digit_frame.get_width() * scale_factor)
                        scaled_height = int(digit_frame.get_height() * scale_factor)
                        digit_frame = pygame.transform.scale(digit_frame, (scaled_width, scaled_height))
                    screen.blit(digit_frame, (current_x, number_y))
                    # Reduce gap between digits by using actual width minus 2px overlap
                    current_x += digit_frame.get_width() - 2
        else:
            # Fallback to text rendering if number frames not available
            value_text = str(coins_value)
            value_surface = self.font_medium.render(value_text, True, (255, 215, 0))
            screen.blit(value_surface, (coins_x + label_surface.get_width(), coins_y))

        # Build and update tree nodes, then draw them
        self._build_tree_layout()
        self._update_node_states()
        self._draw_connections(screen)  # Draw lines before nodes (so lines appear behind)
        self._draw_nodes(screen)
        self._draw_tooltip(screen)
    
    def _draw_connections(self, screen: pygame.Surface):
        """Draw thick pixel-art connection lines between nodes based on prerequisites."""
        if not self.nodes:
            return
        
        for node in self.nodes.values():
            for parent_id in node.parents:
                if parent_id not in self.nodes:
                    continue
                parent = self.nodes[parent_id]
                
                # Determine line color based on node states
                # Blue for unlocked, Yellow for unlockable, Red for locked
                if node.state == "unlocked" and parent.state == "unlocked":
                    color = LINE_UNLOCKED  # Blue
                elif node.state == "unlockable" and parent.state == "unlocked":
                    color = LINE_UNLOCKABLE  # Yellow
                else:
                    color = LINE_LOCKED  # Red
                
                # Get node center positions
                start = parent.rect.center
                end = node.rect.center
                
                # Draw thick pixel-art line directly on surface (no transparency)
                pygame.draw.line(screen, color, start, end, LINE_WIDTH)
    
    def _draw_nodes(self, screen: pygame.Surface):
        """Draw research nodes as clickable buttons using spritesheets."""
        if not self.nodes:
            return
        mouse_pos = pygame.mouse.get_pos()
        for node in self.nodes.values():
            if node.state == "unlocked":
                frame_index = 1
            elif node.state == "unlockable":
                frame_index = 0
            else:
                frame_index = 2

            sprite = self._ensure_node_sprite_loaded(node.node_id)
            rect = node.rect
            if sprite:
                frame_surface = self._get_node_frame(sprite, frame_index)
                if rect.size != frame_surface.get_size():
                    frame_surface = pygame.transform.smoothscale(frame_surface, rect.size)
                screen.blit(frame_surface, rect.topleft)
            else:
                # Fallback simple rect if sprite is missing
                fallback = pygame.Surface(rect.size, pygame.SRCALPHA)
                fallback.fill((60, 60, 60, 220))
                screen.blit(fallback, rect.topleft)
                pygame.draw.rect(screen, (120, 120, 120), rect, 2)

            # Hover outline
            if rect.collidepoint(mouse_pos):
                hover = pygame.Surface(rect.size, pygame.SRCALPHA)
                hover.fill((255, 255, 255, 40))
                screen.blit(hover, rect.topleft)
                pygame.draw.rect(screen, (255, 255, 255), rect, 2)

    def _draw_tooltip(self, screen: pygame.Surface):
        """Draw tooltip near hovered node, similar to research_tree UI."""
        if not self.nodes:
            return
        mouse_pos = pygame.mouse.get_pos()
        hovered = None
        for node in self.nodes.values():
            if node.rect.collidepoint(mouse_pos):
                hovered = node
                break
        if not hovered:
            return

        lines = [hovered.name]
        if hovered.description:
            lines.append(hovered.description)
        if hovered.cost and hovered.state != "unlocked":
            lines.append(f"Cost: {hovered.cost} coins")

        if hovered.node_id in self.research.research_defs:
            modifiers = self.research.research_defs[hovered.node_id].get("modifiers", {})
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
        width = max(self.font_small.render(line, True, (255, 255, 255)).get_width() for line in lines if line) + padding * 2
        height = len([l for l in lines if l]) * 20 + padding * 2

        tooltip_rect = pygame.Rect(
            min(max(hovered.rect.centerx - width // 2, self.rect.x + 10), self.rect.right - width - 10),
            hovered.rect.bottom + 10,
            width,
            height,
        )
        pygame.draw.rect(screen, (20, 20, 20), tooltip_rect)
        pygame.draw.rect(screen, (140, 140, 140), tooltip_rect, 2)

        y = tooltip_rect.y + padding
        for line in lines:
            if line:
                surf = self.font_small.render(line, True, (220, 220, 220))
                screen.blit(surf, (tooltip_rect.x + padding, y))
                y += 20

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------
    def debug_handle_drag(self, mouse_pos: tuple, is_mouse_down: bool):
        """
        Debug helper to drag nodes around with the mouse and print coordinates.
        Only used when debug mode is active.
        """
        if not self.visible or not self.nodes:
            return

        if is_mouse_down:
            # Start drag if none active and cursor is over a node
            if self._debug_drag_node is None:
                for node in self.nodes.values():
                    if node.rect.collidepoint(mouse_pos):
                        self._debug_drag_node = node
                        # Store offset so node doesn't snap its center to cursor immediately
                        dx = mouse_pos[0] - node.rect.centerx
                        dy = mouse_pos[1] - node.rect.centery
                        self._debug_drag_offset = (dx, dy)
                        break
            else:
                # Update active drag node position
                dx, dy = self._debug_drag_offset
                cx = mouse_pos[0] - dx
                cy = mouse_pos[1] - dy
                self._debug_drag_node.rect.center = (cx, cy)
        else:
            # Mouse released: if we were dragging, print final coordinates
            if self._debug_drag_node is not None:
                cx, cy = self._debug_drag_node.rect.center
                print(f"[ResearchPanel][DEBUG] Node '{self._debug_drag_node.node_id}' position: ({cx}, {cy})")
                self._debug_drag_node = None

    def handle_click(self, mouse_pos: tuple) -> bool:
        """
        Handle mouse click on panel.
        Args:
            mouse_pos: Mouse position (x, y)
        Returns:
            True if click was handled, False otherwise
        """
        if not self.visible:
            return False

        # Clicking outside closes panel
        if not self.rect.collidepoint(mouse_pos):
            self.hide()
            return True

        # Clicking inside panel: check node buttons
        for node in self.nodes.values():
            if node.rect.collidepoint(mouse_pos):
                # Only allow unlock if affordable and prerequisites met
                if self.research.can_research(node.node_id):
                    if self.research.unlock(node.node_id):
                        # Node unlocked, update states
                        self._update_node_states()
                else:
                    # Could show feedback later
                    pass
                return True

        return False
    
    def handle_key(self, key) -> bool:
        """
        Handle keyboard input.
        Args:
            key: Key code (e.g., pygame.K_ESCAPE)
        Returns:
            True if key was handled, False otherwise
        """
        if key == pygame.K_ESCAPE and self.visible:
            self.hide()
            return True
        return False

    # ------------------------------------------------------------------
    # Sprite helpers (shared naming scheme with research_tree)
    # ------------------------------------------------------------------
    def _ensure_node_sprite_loaded(self, node_id: str):
        """Load and cache the spritesheet for a node if available."""
        if node_id in self.node_sprites:
            return self.node_sprites[node_id]

        filename_new = self._node_id_to_sprite_filename(node_id)
        candidates = [
            os.path.join("asset", "hud", "ResearchNode", filename_new),
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
            if node_id not in self._missing_sprite_logged:
                print(f"[ResearchPanel] WARNING: No sprite found for node '{node_id}'. Tried:")
                for p in candidates:
                    print(f"  - {p}")
                self._missing_sprite_logged.add(node_id)
            return None
        self.node_sprites[node_id] = surface
        return surface

    def _get_node_frame(self, sheet: pygame.Surface, frame_index: int) -> pygame.Surface:
        """Extract a frame from a 3-frame horizontal spritesheet (220x90 each)."""
        from research_tree import NODE_WIDTH, NODE_HEIGHT
        frame_index = max(0, min(2, frame_index))
        frame_w, frame_h = NODE_WIDTH, NODE_HEIGHT
        x = frame_index * frame_w
        rect = pygame.Rect(x, 0, frame_w, frame_h)
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), rect)
        return frame

    def _node_id_to_sprite_filename(self, node_id: str) -> str:
        """Match research_tree sprite naming rules and overrides."""
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
        parts = [p for p in node_id.split("_") if p]
        pascal = "".join(part.capitalize() for part in parts)
        return f"{pascal}Node-Sheet.png"