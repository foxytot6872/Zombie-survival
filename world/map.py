"""
Grid-based map system for building placement and footprint checking.
"""
from typing import Set, Tuple

class Grid:
    """Grid system for managing building placement and collisions."""
    
    TILE = 32  # Tile size in pixels
    
    def __init__(self, width: int, height: int, screen_width: int = 1920, screen_height: int = 1080, upper_fraction: float = 0.6667):
        """
        Initialize grid with dimensions in tiles.
        Args:
            width: Grid width in tiles
            height: Grid height in tiles
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            upper_fraction: Fraction of screen that is upper zone (0.0-1.0)
        """
        self.width = width
        self.height = height
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen_h = screen_height  # Alias for compatibility
        self.upper_fraction = upper_fraction
        self.tile = self.TILE  # Alias for compatibility
        # Set of (x, y) tuples that are blocked
        self.blocked_tiles: Set[Tuple[int, int]] = set()
    
    def is_blocked(self, x: int, y: int, check_passable: bool = False, building_group=None) -> bool:
        """
        Check if a tile at (x, y) is blocked.
        Args:
            x: Tile x coordinate
            y: Tile y coordinate
            check_passable: If True, check if building at this position is passable (like gates)
            building_group: Building group to check for passable buildings
        Returns:
            True if blocked, False if passable
        """
        # First check if tile is in blocked set
        if (x, y) in self.blocked_tiles:
            # If check_passable is True, verify if there's a passable building here
            if check_passable and building_group:
                # Check if there's a gate or other passable building at this position
                for building in building_group:
                    if (hasattr(building, 'grid_x') and hasattr(building, 'grid_y') and
                        building.grid_x == x and building.grid_y == y):
                        # Check if building is passable
                        if hasattr(building, 'PASSABLE') and building.PASSABLE:
                            return False  # Gate is passable, don't block
                        elif hasattr(building, 'passable') and building.passable:
                            return False  # Building is passable
            return True  # Blocked
        return False  # Not blocked
    
    def set_blocked(self, x: int, y: int, blocked: bool = True):
        """Set a tile as blocked or unblocked."""
        if blocked:
            self.blocked_tiles.add((x, y))
        else:
            self.blocked_tiles.discard((x, y))
    
    def set_footprint_blocked(self, grid_pos: Tuple[int, int], footprint: Tuple[int, int], blocked: bool = True):
        """Set all tiles in a footprint as blocked or unblocked."""
        gx, gy = grid_pos
        w, h = footprint
        for x in range(gx, gx + w):
            for y in range(gy, gy + h):
                self.set_blocked(x, y, blocked)
    
    def clear(self):
        """Clear all blocked tiles."""
        self.blocked_tiles.clear()
    
    def get_split_y_px(self) -> int:
        """Get the pixel Y coordinate for the upper/lower zone split."""
        return int(self.screen_h * self.upper_fraction)
    
    def px_to_tile(self, px: int) -> int:
        """Convert pixel coordinate to tile coordinate."""
        return px // self.TILE
    
    def tile_to_px(self, tile: int) -> int:
        """Convert tile coordinate to pixel coordinate."""
        return tile * self.TILE
    
    def block_tiles(self, tiles: Set[Tuple[int, int]], blocked: bool = True):
        """Block or unblock multiple tiles at once."""
        for x, y in tiles:
            self.set_blocked(x, y, blocked)

