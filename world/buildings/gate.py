"""Gate building."""
from world.building import Building, Cost, BuildState, TILE
import pygame

class Gate(Building):
    """Gate - passable defensive structure (enemies can path through)."""
    TYPE_ID = "gate"
    BASE_HP = 300
    BUILD_TIME = 2.0
    COST = Cost(wood=30, iron=10)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    PASSABLE = True  # Gates are passable for pathfinding
    
    def __init__(self, grid_pos, tier=1, uid=None):
        super().__init__(grid_pos, tier, uid)
        # Gates can be passable but still block placement
        self.passable = True
    
    def draw(self, surface: pygame.Surface):
        """Draw gate with distinctive appearance"""
        w, h = self.FOOTPRINT
        # Update image size if needed
        if self.image.get_size() != (w * TILE, h * TILE):
            self.image = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
        
        # Clear image
        self.image.fill((0, 0, 0, 0))
        
        # Draw gate (different from wall - lighter, with opening indicator)
        if self.state == BuildState.DESTROYED:
            color = (80, 30, 30)  # Dark red when destroyed
        else:
            color = (120, 100, 80)  # Brown/beige for gate
        
        # Draw main gate
        pygame.draw.rect(self.image, color, (0, 0, w * TILE, h * TILE))
        # Draw border (lighter than wall)
        pygame.draw.rect(self.image, (150, 130, 100), (0, 0, w * TILE, h * TILE), 2)
        # Draw opening indicator (vertical lines to show it's a gate)
        center_x = w * TILE // 2
        pygame.draw.line(self.image, (100, 80, 60), (center_x, 4), (center_x, h * TILE - 4), 2)
        
        # HP bar if damaged
        if self.state == BuildState.ACTIVE and self.hp < self.max_hp:
            hp_pct = self.hp / self.max_hp if self.max_hp > 0 else 1.0
            hp_color = (0, 255, 0) if hp_pct > 0.6 else (255, 255, 0) if hp_pct > 0.3 else (255, 0, 0)
            bar_height = 4
            bar_y = h * TILE - bar_height - 2
            bar_width = w * TILE - 4
            # Background bar
            pygame.draw.rect(self.image, (0, 0, 0), (2, bar_y, bar_width, bar_height))
            # HP bar
            hp_bar_width = int(bar_width * hp_pct)
            if hp_bar_width > 0:
                pygame.draw.rect(self.image, hp_color, (2, bar_y, hp_bar_width, bar_height))
        
        # Update rect position
        self.rect = self.image.get_rect(center=self.pos)
        surface.blit(self.image, self.rect)

