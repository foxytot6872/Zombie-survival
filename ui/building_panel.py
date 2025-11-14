"""
Building panel UI for upgrade and repair.
"""
import pygame
from typing import Optional, Callable
from world.building import Building, BuildState

class BuildingPanel:
    """Building panel UI for upgrade and repair"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080, upgrade_panel_frames=None, upgrade_panel_darken_frames=None, panel_background_frames=None):
        """
        Initialize building panel.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            upgrade_panel_frames: List of 3 frames for upgrade progress panel
            upgrade_panel_darken_frames: List of 3 darkened frames for upgrade progress panel
            panel_background_frames: List of 3 frames (497x742 each) for building detail panel background
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        self.is_visible = False
        self.selected_building: Optional[Building] = None
        
        # Set panel size based on background frames if available
        self.panel_background_frames = panel_background_frames if panel_background_frames else []
        if self.panel_background_frames and len(self.panel_background_frames) > 0:
            bg_width, bg_height = self.panel_background_frames[0].get_size()
            self.panel_rect = pygame.Rect(0, 0, bg_width, bg_height)
        else:
            self.panel_rect = pygame.Rect(0, 0, 300, 400)
        
        self.panel_rect.bottomright = (screen_width - 10, screen_height - 10)
        self.button_rects = {}  # Store button rects for click detection
        
        self.upgrade_panel_frames = upgrade_panel_frames if upgrade_panel_frames else []
        self.upgrade_panel_darken_frames = upgrade_panel_darken_frames if upgrade_panel_darken_frames else []
        self.upgrade_panel_rect = None  # Will be set when drawing
        
        self.on_upgrade: Optional[Callable] = None
        self.on_repair: Optional[Callable] = None
        self.on_sell: Optional[Callable] = None
    
    def show(self, building: Building):
        """Show building panel"""
        self.is_visible = True
        self.selected_building = building
    
    def hide(self):
        """Hide building panel"""
        self.is_visible = False
        self.selected_building = None
    
    def handle_event(self, event: pygame.event.Event, mouse_pos) -> Optional[str]:
        """
        Handle event.
        Args:
            event: Pygame event
            mouse_pos: Mouse position tuple
        Returns:
            Button name if clicked, None otherwise
        """
        if not self.is_visible or not self.selected_building:
            return None
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if clicking outside panel - close it
            if not self.panel_rect.collidepoint(mouse_pos):
                self.hide()
                return "close"
            
            # Check button clicks
            if hasattr(self, 'button_rects'):
                for button_name, button_rect in self.button_rects.items():
                    if button_rect.collidepoint(mouse_pos):
                        return button_name
        
        return None
    
    def draw(self, surface: pygame.Surface, resources, mouse_pos=None):
        """Draw building panel"""
        if not self.is_visible or not self.selected_building:
            return
        
        building = self.selected_building
        
        # Draw panel background using upgrade panel asset - select frame based on upgrade progress
        # Initialize upgrade_progress if not set (backwards compatibility)
        if not hasattr(building, 'upgrade_progress'):
            building.upgrade_progress = 0
        
        # Select frame based on upgrade progress (0, 1, 2) or tier if at max progress
        if self.panel_background_frames and len(self.panel_background_frames) > 0:
            # Use upgrade_progress to select frame (0, 1, 2)
            frame_index = min(building.upgrade_progress, len(self.panel_background_frames) - 1)
            current_background = self.panel_background_frames[frame_index]
            surface.blit(current_background, self.panel_rect)
        else:
            # Fallback: simple background if frames not loaded
            panel_bg = pygame.Surface((self.panel_rect.width, self.panel_rect.height), pygame.SRCALPHA)
            panel_bg.fill((50, 50, 50, 230))
            surface.blit(panel_bg, self.panel_rect)
            # Draw panel border
            pygame.draw.rect(surface, (200, 200, 200), self.panel_rect, 3)
        
        # Draw building info
        y_offset = self.panel_rect.y + 20
        line_height = 30
        
        # Building name
        building_name = building.TYPE_ID.replace('_', ' ').title()
        name_surface = self.font_large.render(building_name, True, (255, 255, 255))
        surface.blit(name_surface, (self.panel_rect.x + 10, y_offset))
        y_offset += line_height + 10
        
        # HP bar
        hp_text = f"HP: {building.hp} / {building.max_hp}"
        hp_surface = self.font_medium.render(hp_text, True, (255, 255, 255))
        surface.blit(hp_surface, (self.panel_rect.x + 10, y_offset))
        y_offset += line_height
        
        # Draw HP bar
        hp_bar_rect = pygame.Rect(self.panel_rect.x + 10, y_offset, self.panel_rect.width - 20, 20)
        hp_percent = building.hp / building.max_hp if building.max_hp > 0 else 0
        hp_color = (0, 255, 0) if hp_percent > 0.5 else (255, 255, 0) if hp_percent > 0.25 else (255, 0, 0)
        pygame.draw.rect(surface, (0, 0, 0), hp_bar_rect)
        pygame.draw.rect(surface, hp_color, (hp_bar_rect.x, hp_bar_rect.y, int(hp_bar_rect.width * hp_percent), hp_bar_rect.height))
        y_offset += line_height + 10
        
        # Tier
        tier_text = f"Tier: {building.tier} / {building.TIER_MAX}"
        tier_surface = self.font_medium.render(tier_text, True, (255, 255, 255))
        surface.blit(tier_surface, (self.panel_rect.x + 10, y_offset))
        
        # Buttons (store rects for click detection)
        self.button_rects = {}
        
        # Upgrade clickable area - coordinates (42, 404) to (450, 541) relative to panel background
        # Check if this is a wood wall that can be upgraded to iron
        from world.buildings.wall_wood import WallWood
        can_upgrade_to_iron = isinstance(building, WallWood) and building.state == BuildState.ACTIVE
        can_upgrade_tier = building.tier < building.TIER_MAX and building.state == BuildState.ACTIVE
        
        # Initialize upgrade_progress if not set (backwards compatibility)
        if not hasattr(building, 'upgrade_progress'):
            building.upgrade_progress = 0
        
        # Set up upgrade clickable area if building can be upgraded
        if can_upgrade_to_iron or can_upgrade_tier:
            # Clickable area coordinates relative to panel background: (42, 404) to (450, 541)
            clickable_left = 42
            clickable_top = 404
            clickable_width = 450 - 42  # 408
            clickable_height = 541 - 404  # 137
            
            # Calculate clickable area position on screen (relative to panel position)
            clickable_x = self.panel_rect.x + clickable_left
            clickable_y = self.panel_rect.y + clickable_top
            
            # Store clickable area rect for click detection
            self.upgrade_panel_rect = pygame.Rect(clickable_x, clickable_y, clickable_width, clickable_height)
            
            # Register upgrade button
            if can_upgrade_to_iron:
                self.button_rects["upgrade_to_iron"] = self.upgrade_panel_rect
            else:
                self.button_rects["upgrade"] = self.upgrade_panel_rect
    
    def _get_upgrade_cost(self, building: Building):
        """Get upgrade cost for building (per progress step, not per tier)"""
        from world.building import Cost
        base_cost = building.COST
        # Cost increases with tier, but is per progress step (1/3 of tier upgrade cost)
        upgrade_mult = 1.25  # 25% increase per tier
        tier_cost_mult = upgrade_mult * building.tier
        # Divide by 3 since it takes 3 upgrades to reach next tier
        return Cost(
            wood=int(base_cost.wood * tier_cost_mult / 3),
            iron=int(base_cost.iron * tier_cost_mult / 3),
            food=int(base_cost.food * tier_cost_mult / 3)
        )
    
    def _get_repair_cost(self, building: Building):
        """Get repair cost for building"""
        from world.building import Cost
        hp_needed = building.max_hp - building.hp
        # 1 wood per 5 HP
        wood_cost = max(1, hp_needed // 5)
        return Cost(wood=wood_cost, iron=0, food=0)
    
    def _get_wall_upgrade_cost(self):
        """Get upgrade cost for wood wall → iron wall"""
        from world.building import Cost
        return Cost(wood=10, iron=40, food=0)

