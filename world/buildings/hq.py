"""HQ (Headquarters) building."""
from world.building import Building, Cost, BuildState, TILE
import pygame

class HQ(Building):
    """Headquarters - main base building."""
    TYPE_ID = "hq"
    BASE_HP = 2000
    BUILD_TIME = 0.0  # Spawns active (no construction time)
    COST = Cost()  # No cost for initial HQ
    FOOTPRINT = (2, 2)
    TIER_MAX = 1  # No upgrades for now
    
    def __init__(self, grid_pos, tier=1, uid=None):
        super().__init__(grid_pos, tier, uid)
        # HQ spawns immediately active
        self.state = BuildState.ACTIVE
        self.hp = self.max_hp
        self.progress = 0.0
    
    def update(self, dt, world=None):
        """Update HQ - optional tiny regen during day"""
        super().update(dt, world)
        
        # Optional: slow auto-repair during DAY (configurable)
        # Check if it's day time (from wave manager or world)
        is_day = False
        if world:
            # Check wave manager state if available
            if hasattr(world, 'wave_manager'):
                is_day = world.wave_manager.state == "DAY"
            elif hasattr(world, 'is_day'):
                is_day = world.is_day
        
        # Small regen during day (configurable, default ~30 HP/min)
        if is_day and self.state == BuildState.ACTIVE and self.hp < self.max_hp:
            regen_rate = 0.5  # HP per second (~30 HP/min)
            self.hp = min(self.max_hp, self.hp + regen_rate * dt)
    
    def draw(self, surface: pygame.Surface):
        """Draw HQ with distinctive appearance"""
        w, h = self.FOOTPRINT
        # Update image size if needed
        if self.image.get_size() != (w * TILE, h * TILE):
            self.image = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
        
        # Clear image
        self.image.fill((0, 0, 0, 0))
        
        # Draw HQ with distinctive blue/grey color (different from other buildings)
        if self.state == BuildState.DESTROYED:
            color = (80, 30, 30)  # Dark red when destroyed
        else:
            color = (50, 100, 150)  # Blue-grey for HQ
        
        # Draw main building
        pygame.draw.rect(self.image, color, (0, 0, w * TILE, h * TILE))
        # Draw border
        pygame.draw.rect(self.image, (100, 150, 200), (0, 0, w * TILE, h * TILE), 3)
        # Draw cross symbol in center to indicate HQ
        center_x, center_y = w * TILE // 2, h * TILE // 2
        cross_size = 10
        pygame.draw.line(self.image, (200, 200, 255), 
                        (center_x - cross_size, center_y), 
                        (center_x + cross_size, center_y), 3)
        pygame.draw.line(self.image, (200, 200, 255), 
                        (center_x, center_y - cross_size), 
                        (center_x, center_y + cross_size), 3)
        
        # HP bar (always show for HQ since it's important)
        if self.state == BuildState.ACTIVE:
            hp_pct = self.hp / self.max_hp if self.max_hp > 0 else 1.0
            hp_color = (0, 255, 0) if hp_pct > 0.6 else (255, 255, 0) if hp_pct > 0.3 else (255, 0, 0)
            bar_height = 6
            bar_y = h * TILE - bar_height - 2
            bar_width = w * TILE - 4
            # Background bar
            pygame.draw.rect(self.image, (0, 0, 0), (2, bar_y, bar_width, bar_height))
            # HP bar (always draw, even at full HP)
            hp_bar_width = int(bar_width * hp_pct)
            if hp_bar_width > 0:
                pygame.draw.rect(self.image, hp_color, (2, bar_y, hp_bar_width, bar_height))
        
        # Update rect position
        self.rect = self.image.get_rect(center=self.pos)
        surface.blit(self.image, self.rect)
    
    def on_destroy(self):
        """Called when HQ is destroyed"""
        # Nothing special - game_state handles GAME OVER
        pass

