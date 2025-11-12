"""Base wall class with shared logic."""
from world.building import Building, Cost, BuildState, TILE
import pygame

class WallBase(Building):
    """Base class for walls - shared functionality."""
    FOOTPRINT = (1, 1)
    PASSABLE = False  # Walls block pathfinding
    
    def __init__(self, grid_pos, wall_tiles=None, building_group=None, tier=1, uid=None):
        super().__init__(grid_pos, tier=tier, uid=uid)
        # Store wall tiles dictionary (3x3 grid)
        self.wall_tiles = wall_tiles  # Dictionary: {(col, row): tile_surface}
        self.building_group = building_group  # Reference to building group for neighbor checking
        # Update image size
        w, h = self.FOOTPRINT
        self.image = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
    
    def _has_wall_neighbor(self, dx, dy, building_group):
        """Check if there's a wall neighbor at offset (dx, dy)."""
        if building_group is None:
            return False
        
        neighbor_x = self.grid_x + dx
        neighbor_y = self.grid_y + dy
        
        # Check all buildings at that position
        for building in building_group:
            if (hasattr(building, 'grid_x') and hasattr(building, 'grid_y') and
                building.grid_x == neighbor_x and building.grid_y == neighbor_y):
                # Check if it's a wall (wood or iron)
                if (hasattr(building, 'TYPE_ID') and 
                    building.TYPE_ID in ('wall_wood', 'wall_iron') and
                    building.state == BuildState.ACTIVE):
                    return True
        return False
    
    def _get_wall_tile_index(self, building_group):
        """
        Determine which tile to use based on neighboring walls.
        Returns (col, row) tuple for tile selection.
        
        Tile map layout (3x3 grid, 96x96 pixels):
        [0,0] [1,0] [2,0]  - Top-left corner, Top edge, Top-right corner
        [0,1] [1,1] [2,1]  - Left vertical edge, Center, Right vertical edge
        [0,2] [1,2] [2,2]  - Bottom-left corner, Bottom edge, Bottom-right corner
        
        The four corners are corner pieces.
        The first and last of the middle row ([0,1] and [2,1]) are vertical pieces.
        """
        # Check neighbors: up, down, left, right
        has_up = self._has_wall_neighbor(0, -1, building_group)
        has_down = self._has_wall_neighbor(0, 1, building_group)
        has_left = self._has_wall_neighbor(-1, 0, building_group)
        has_right = self._has_wall_neighbor(1, 0, building_group)
        
        # Priority 1: Check corners first (when both perpendicular neighbors exist)
        if has_up and has_left:
            # Top-left corner
            return (0, 0)
        elif has_up and has_right:
            # Top-right corner
            return (2, 0)
        elif has_down and has_left:
            # Bottom-left corner
            return (0, 2)
        elif has_down and has_right:
            # Bottom-right corner
            return (2, 2)
        # Priority 2: Check vertical edges ([0,1] and [2,1] - first and last of middle row)
        elif has_left:
            # Left vertical edge (has left neighbor)
            return (0, 1)
        elif has_right:
            # Right vertical edge (has right neighbor)
            return (2, 1)
        # Priority 3: Check horizontal edges
        elif has_up:
            # Top edge (has up neighbor)
            return (1, 0)
        elif has_down:
            # Bottom edge (has down neighbor)
            return (1, 2)
        else:
            # No neighbors (isolated wall) - use center
            return (1, 1)
    
    def carry_over_hp(self, new_max_hp: int) -> int:
        """Helper when upgrading; preserves damage proportion."""
        if self.max_hp > 0:
            ratio = max(0.0, min(1.0, self.hp / self.max_hp))
        else:
            ratio = 1.0
        return int(ratio * new_max_hp)
    
    def _update_tile_selection(self):
        """Update the wall's displayed tile based on neighbors. Called when neighbors change."""
        # This will be called each frame in draw(), so the tile selection is always current
        pass  # Tile selection happens dynamically in draw()
    
    def draw(self, surface: pygame.Surface):
        """Draw wall with appropriate tile based on neighbors."""
        w, h = self.FOOTPRINT
        # Update image size if needed
        if self.image.get_size() != (w * TILE, h * TILE):
            self.image = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
        
        # Clear image
        self.image.fill((0, 0, 0, 0))
        
        # Get the building group (try self.building_group or use a fallback)
        building_group = getattr(self, 'building_group', None)
        
        # Draw wall tile if available (tile selection happens dynamically each frame)
        if self.wall_tiles and self.state != BuildState.DESTROYED:
            # Determine which tile to use based on neighbors
            tile_index = self._get_wall_tile_index(building_group)
            tile = self.wall_tiles.get(tile_index)
            
            if tile:
                # Blit the appropriate tile
                self.image.blit(tile, (0, 0))
            else:
                # Fallback: use center tile if requested tile not found
                center_tile = self.wall_tiles.get((1, 1))
                if center_tile:
                    self.image.blit(center_tile, (0, 0))
        else:
            # Fallback to colored rectangle if no tiles or destroyed
            if self.state == BuildState.DESTROYED:
                color = (80, 30, 30)  # Dark red when destroyed
            else:
                # Use different colors for wood vs iron
                if hasattr(self, '_is_iron') and self._is_iron:
                    color = (120, 120, 140)  # Slightly bluish grey for iron
                else:
                    color = (100, 80, 60)  # Brownish for wood
            
            # Draw main wall
            pygame.draw.rect(self.image, color, (0, 0, w * TILE, h * TILE))
            # Draw border
            border_color = (180, 180, 200) if (hasattr(self, '_is_iron') and self._is_iron) else (150, 130, 100)
            pygame.draw.rect(self.image, border_color, (0, 0, w * TILE, h * TILE), 2)
        
        # Construction overlay
        if self.state == BuildState.CONSTRUCTING:
            overlay = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Semi-transparent dark overlay
            self.image.blit(overlay, (0, 0))
            # Draw progress bar
            pct = self.progress / self.BUILD_TIME if self.BUILD_TIME > 0 else 1.0
            bar_height = 4
            bar_y = h * TILE - bar_height - 2
            bar_width = w * TILE - 4
            pygame.draw.rect(self.image, (200, 220, 80), (2, bar_y, int(bar_width * pct), bar_height))
        
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

