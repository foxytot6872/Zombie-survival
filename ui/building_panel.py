"""
Building panel UI for upgrade and repair.
"""
import pygame
from typing import Optional, Callable
from world.building import Building, BuildState

class BuildingPanel:
    """Building panel UI for upgrade and repair"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080, upgrade_panel_frames=None, upgrade_panel_darken_frames=None):
        """
        Initialize building panel.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            upgrade_panel_frames: List of 3 frames for upgrade progress panel
            upgrade_panel_darken_frames: List of 3 darkened frames for upgrade progress panel
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        self.is_visible = False
        self.selected_building: Optional[Building] = None
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
        
        # Draw panel background
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
        y_offset += line_height - 25  # Reduced spacing to move upgrade panel up
        
        # Buttons (store rects for click detection)
        self.button_rects = {}
        
        # Upgrade panel using progress frames
        # Check if this is a wood wall that can be upgraded to iron
        from world.buildings.wall_wood import WallWood
        can_upgrade_to_iron = isinstance(building, WallWood) and building.state == BuildState.ACTIVE
        can_upgrade_tier = building.tier < building.TIER_MAX and building.state == BuildState.ACTIVE
        
        # Show upgrade panel if can upgrade and progress < 3 (not yet at tier upgrade)
        # Initialize upgrade_progress if not set (backwards compatibility)
        if not hasattr(building, 'upgrade_progress'):
            building.upgrade_progress = 0
        
        if (can_upgrade_to_iron or can_upgrade_tier) and self.upgrade_panel_frames and building.upgrade_progress < 3:
            # Calculate upgrade cost and affordability (per progress step)
            if can_upgrade_to_iron:
                upgrade_cost = self._get_wall_upgrade_cost()
            else:
                upgrade_cost = self._get_upgrade_cost(building)
            
            can_afford = (resources.wood >= upgrade_cost.wood and
                         resources.iron >= upgrade_cost.iron and
                         resources.food >= upgrade_cost.food)
            
            # Select frame based on upgrade progress (0, 1, 2)
            frame_index = min(building.upgrade_progress, len(self.upgrade_panel_frames) - 1)
            
            # Get a frame to calculate dimensions (we'll choose the right one later)
            temp_frame = self.upgrade_panel_frames[frame_index] if frame_index < len(self.upgrade_panel_frames) else self.upgrade_panel_frames[0]
            
            # Scale frame to fit panel if needed (max width is panel width - 20 for padding)
            max_width = self.panel_rect.width - 20
            original_width = temp_frame.get_width()
            original_height = temp_frame.get_height()
            
            scale_factor = 1.0
            if original_width > max_width:
                scale_factor = max_width / original_width
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
            else:
                new_width = original_width
                new_height = original_height
            
            # Position upgrade panel
            upgrade_panel_x = self.panel_rect.x + (self.panel_rect.width - new_width) // 2
            upgrade_panel_y = y_offset
            
            # Calculate clickable area position on screen
            # Define clickable area in original image coordinates: (62, 216) to (318, 332)
            clickable_left_original = 62
            clickable_top_original = 216
            clickable_width_original = 318 - 62  # 256
            clickable_height_original = 332 - 216  # 116
            
            # Scale clickable area to match scaled image
            clickable_left_scaled = int(clickable_left_original * scale_factor)
            clickable_top_scaled = int(clickable_top_original * scale_factor)
            clickable_width_scaled = int(clickable_width_original * scale_factor)
            clickable_height_scaled = int(clickable_height_original * scale_factor)
            
            # Calculate clickable area position on screen
            clickable_x = upgrade_panel_x + clickable_left_scaled
            clickable_y = upgrade_panel_y + clickable_top_scaled
            
            # Store clickable area rect for click detection (not the full panel)
            self.upgrade_panel_rect = pygame.Rect(clickable_x, clickable_y, clickable_width_scaled, clickable_height_scaled)
            
            # Check if mouse is hovering over the upgrade panel
            is_hovering = False
            if mouse_pos:
                is_hovering = self.upgrade_panel_rect.collidepoint(mouse_pos)
            
            # Choose which frame set to use (normal or darkened)
            # Use darkened frames if can't afford or hovering
            use_darkened = not can_afford or is_hovering
            if use_darkened and self.upgrade_panel_darken_frames and frame_index < len(self.upgrade_panel_darken_frames):
                original_frame = self.upgrade_panel_darken_frames[frame_index]
            else:
                original_frame = self.upgrade_panel_frames[frame_index] if frame_index < len(self.upgrade_panel_frames) else self.upgrade_panel_frames[0]
            
            # Scale the chosen frame
            if scale_factor != 1.0:
                current_frame = pygame.transform.smoothscale(original_frame, (new_width, new_height))
            else:
                current_frame = original_frame
            
            # Draw upgrade panel frame
            surface.blit(current_frame, (upgrade_panel_x, upgrade_panel_y))
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

