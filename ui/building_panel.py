"""
Building panel UI for upgrade and repair.
"""
import pygame
from typing import Optional, Callable
from world.building import Building, BuildState

class BuildingPanel:
    """Building panel UI for upgrade and repair"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        """
        Initialize building panel.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
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
    
    def draw(self, surface: pygame.Surface, resources):
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
        y_offset += line_height + 20
        
        # Buttons (store rects for click detection)
        button_height = 40
        button_spacing = 10
        self.button_rects = {}
        
        # Upgrade button
        # Check if this is a wood wall that can be upgraded to iron
        from world.buildings.wall_wood import WallWood
        can_upgrade_to_iron = isinstance(building, WallWood) and building.state == BuildState.ACTIVE
        
        if can_upgrade_to_iron:
            # Special upgrade for wood wall → iron wall
            upgrade_cost = self._get_wall_upgrade_cost()
            can_afford = (resources.wood >= upgrade_cost.wood and
                         resources.iron >= upgrade_cost.iron and
                         resources.food >= upgrade_cost.food)
            upgrade_rect = pygame.Rect(self.panel_rect.x + 10, y_offset, self.panel_rect.width - 20, button_height)
            upgrade_color = (100, 200, 100) if can_afford else (100, 100, 100)
            pygame.draw.rect(surface, upgrade_color, upgrade_rect)
            pygame.draw.rect(surface, (255, 255, 255), upgrade_rect, 2)
            upgrade_text = f"Upgrade → Iron"
            upgrade_text_surface = self.font_medium.render(upgrade_text, True, (255, 255, 255))
            text_rect = upgrade_text_surface.get_rect(center=upgrade_rect.center)
            surface.blit(upgrade_text_surface, text_rect)
            self.button_rects["upgrade_to_iron"] = upgrade_rect
            y_offset += button_height + button_spacing
        elif building.tier < building.TIER_MAX and building.state == BuildState.ACTIVE:
            # Regular tier upgrade
            upgrade_rect = pygame.Rect(self.panel_rect.x + 10, y_offset, self.panel_rect.width - 20, button_height)
            upgrade_cost = self._get_upgrade_cost(building)
            can_afford = (resources.wood >= upgrade_cost.wood and
                         resources.iron >= upgrade_cost.iron and
                         resources.food >= upgrade_cost.food)
            upgrade_color = (100, 200, 100) if can_afford else (100, 100, 100)
            pygame.draw.rect(surface, upgrade_color, upgrade_rect)
            pygame.draw.rect(surface, (255, 255, 255), upgrade_rect, 2)
            upgrade_text = f"Upgrade (Tier {building.tier + 1})"
            upgrade_text_surface = self.font_medium.render(upgrade_text, True, (255, 255, 255))
            text_rect = upgrade_text_surface.get_rect(center=upgrade_rect.center)
            surface.blit(upgrade_text_surface, text_rect)
            self.button_rects["upgrade"] = upgrade_rect
            y_offset += button_height + button_spacing
        
        # Repair button
        if building.hp < building.max_hp and building.state == BuildState.ACTIVE:
            repair_rect = pygame.Rect(self.panel_rect.x + 10, y_offset, self.panel_rect.width - 20, button_height)
            repair_cost = self._get_repair_cost(building)
            can_afford = (resources.wood >= repair_cost.wood and
                         resources.iron >= repair_cost.iron and
                         resources.food >= repair_cost.food)
            repair_color = (200, 200, 100) if can_afford else (100, 100, 100)
            pygame.draw.rect(surface, repair_color, repair_rect)
            pygame.draw.rect(surface, (255, 255, 255), repair_rect, 2)
            repair_text = f"Repair ({repair_cost.wood} wood)"
            repair_text_surface = self.font_medium.render(repair_text, True, (255, 255, 255))
            text_rect = repair_text_surface.get_rect(center=repair_rect.center)
            surface.blit(repair_text_surface, text_rect)
            self.button_rects["repair"] = repair_rect
            y_offset += button_height + button_spacing
        
        # Sell button (not available for HQ)
        if building.state == BuildState.ACTIVE:
            # Check if this is HQ - don't show sell button for HQ
            from world.buildings.hq import HQ
            if not isinstance(building, HQ):
                sell_rect = pygame.Rect(self.panel_rect.x + 10, y_offset, self.panel_rect.width - 20, button_height)
                sell_color = (200, 100, 100)
                pygame.draw.rect(surface, sell_color, sell_rect)
                pygame.draw.rect(surface, (255, 255, 255), sell_rect, 2)
                sell_text = "Sell (60% refund)"
                sell_text_surface = self.font_medium.render(sell_text, True, (255, 255, 255))
                text_rect = sell_text_surface.get_rect(center=sell_rect.center)
                surface.blit(sell_text_surface, text_rect)
                self.button_rects["sell"] = sell_rect
    
    def _get_upgrade_cost(self, building: Building):
        """Get upgrade cost for building"""
        from world.building import Cost
        base_cost = building.COST
        upgrade_mult = 1.25  # 25% increase per tier
        return Cost(
            wood=int(base_cost.wood * upgrade_mult * building.tier),
            iron=int(base_cost.iron * upgrade_mult * building.tier),
            food=int(base_cost.food * upgrade_mult * building.tier)
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

