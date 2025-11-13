"""Housing building."""
from world.building import Building, Cost, BuildState, TILE
import pygame

class Housing(Building):
    """Housing - provides population capacity."""
    TYPE_ID = "housing"
    BASE_HP = 150
    BUILD_TIME = 3.0
    COST = Cost(wood=50, iron=20)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    
    # Class-level image (set from main.py after loading)
    building_image = None
    
    def __init__(self, grid_pos, tier=1, uid=None, building_image=None):
        super().__init__(grid_pos, tier, uid)
        # Use provided image or class-level image
        self.building_image = building_image if building_image is not None else Housing.building_image
    
    def draw(self, surface: pygame.Surface):
        """Draw housing with custom image"""
        w, h = self.FOOTPRINT
        # Make the house image bigger - scale it to 1.75x the tile size
        scale_factor = 1.75
        display_width = int(w * TILE * scale_factor)
        display_height = int(h * TILE * scale_factor)
        
        # Update image size to accommodate larger house
        if self.image.get_size() != (display_width, display_height):
            self.image = pygame.Surface((display_width, display_height), pygame.SRCALPHA)
        
        # Clear image
        self.image.fill((0, 0, 0, 0))
        
        # Draw building image if available
        if self.building_image:
            # Scale image to be bigger than the tile
            scaled_image = pygame.transform.smoothscale(self.building_image, (display_width, display_height))
            self.image.blit(scaled_image, (0, 0))
        else:
            # Fallback to default drawing
            color = (120, 120, 120) if self.state != BuildState.DESTROYED else (80, 30, 30)
            pygame.draw.rect(self.image, color, (0, 0, display_width, display_height))
        
        # Draw construction progress bar
        if self.state == BuildState.CONSTRUCTING:
            progress_pct = self.progress / self.BUILD_TIME if self.BUILD_TIME > 0 else 0.0
            bar_height = 4
            bar_y = display_height - bar_height - 2
            bar_width = display_width - 4
            # Background bar
            pygame.draw.rect(self.image, (0, 0, 0), (2, bar_y, bar_width, bar_height))
            # Progress bar
            progress_width = int(bar_width * progress_pct)
            if progress_width > 0:
                pygame.draw.rect(self.image, (100, 200, 100), (2, bar_y, progress_width, bar_height))
        
        # Draw HP bar if damaged
        if self.state == BuildState.ACTIVE and self.hp < self.max_hp:
            hp_pct = self.hp / self.max_hp if self.max_hp > 0 else 1.0
            hp_color = (0, 255, 0) if hp_pct > 0.6 else (255, 255, 0) if hp_pct > 0.3 else (255, 0, 0)
            bar_height = 4
            bar_y = display_height - bar_height - 2
            bar_width = display_width - 4
            # Background bar
            pygame.draw.rect(self.image, (0, 0, 0), (2, bar_y, bar_width, bar_height))
            # HP bar
            hp_bar_width = int(bar_width * hp_pct)
            if hp_bar_width > 0:
                pygame.draw.rect(self.image, hp_color, (2, bar_y, hp_bar_width, bar_height))
        
        # Update rect position (centered on the building's position)
        self.rect = self.image.get_rect(center=self.pos)
        surface.blit(self.image, self.rect)

