"""Wall building."""
from world.building import Building, Cost, BuildState, TILE
import pygame

class Wall(Building):
    """Wall - defensive structure (blocks pathfinding)."""
    TYPE_ID = "wall"
    BASE_HP = 280
    BUILD_TIME = 1.2
    COST = Cost(wood=20, iron=5)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    PASSABLE = False  # Walls block pathfinding
    
    def draw(self, surface: pygame.Surface):
        """Draw wall with distinctive appearance"""
        w, h = self.FOOTPRINT
        # Update image size if needed
        if self.image.get_size() != (w * TILE, h * TILE):
            self.image = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
        
        # Clear image
        self.image.fill((0, 0, 0, 0))
        
        # Draw wall (grey/stone color)
        if self.state == BuildState.DESTROYED:
            color = (80, 30, 30)  # Dark red when destroyed
        else:
            color = (100, 100, 100)  # Grey for wall
        
        # Draw main wall
        pygame.draw.rect(self.image, color, (0, 0, w * TILE, h * TILE))
        # Draw border
        pygame.draw.rect(self.image, (150, 150, 150), (0, 0, w * TILE, h * TILE), 2)
        # Draw stone texture (simple pattern)
        for i in range(2):
            for j in range(2):
                x = i * (w * TILE // 2)
                y = j * (h * TILE // 2)
                pygame.draw.rect(self.image, (80, 80, 80), (x + 2, y + 2, w * TILE // 2 - 4, h * TILE // 2 - 4), 1)
        
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

