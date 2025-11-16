"""
Collision map system for fast tile-based collision detection.
Uses a simple 2D grid: 0 = walkable, 1 = solid.
"""
from typing import List


class CollisionMap:
    """
    Fast tile-based collision map.
    Maps grid coordinates to solid (1) or walkable (0) states.
    """
    
    def __init__(self, width: int, height: int, tile_size: int):
        """
        Initialize collision map.
        Args:
            width: Map width in tiles
            height: Map height in tiles
            tile_size: Size of each tile in pixels (e.g., 32)
        """
        self.width = width
        self.height = height
        self.tile_size = tile_size
        # 0 = walkable, 1 = solid
        # data[x][y] where x is column (width), y is row (height)
        self.data: List[List[int]] = [[0 for _ in range(height)] for _ in range(width)]
    
    def set_solid(self, gx: int, gy: int):
        """
        Mark a tile as solid (collision).
        Args:
            gx: Grid x coordinate
            gy: Grid y coordinate
        """
        if 0 <= gx < self.width and 0 <= gy < self.height:
            self.data[gx][gy] = 1
    
    def set_empty(self, gx: int, gy: int):
        """
        Mark a tile as walkable (no collision).
        Args:
            gx: Grid x coordinate
            gy: Grid y coordinate
        """
        if 0 <= gx < self.width and 0 <= gy < self.height:
            self.data[gx][gy] = 0
    
    def is_solid(self, gx: int, gy: int) -> bool:
        """
        Check if a tile is solid.
        Args:
            gx: Grid x coordinate
            gy: Grid y coordinate
        Returns:
            True if solid, False if walkable or out of bounds
        """
        if 0 <= gx < self.width and 0 <= gy < self.height:
            return self.data[gx][gy] == 1
        return False  # Out of bounds is not solid (enemies can leave map)
    
    def clear(self):
        """Clear all tiles (mark all as walkable)."""
        self.data = [[0 for _ in range(self.height)] for _ in range(self.width)]
    
    def set_footprint_solid(self, gx: int, gy: int, footprint_w: int, footprint_h: int):
        """
        Mark a building footprint as solid.
        Args:
            gx: Grid x coordinate (top-left)
            gy: Grid y coordinate (top-left)
            footprint_w: Footprint width in tiles
            footprint_h: Footprint height in tiles
        """
        for dx in range(footprint_w):
            for dy in range(footprint_h):
                self.set_solid(gx + dx, gy + dy)
    
    def set_footprint_empty(self, gx: int, gy: int, footprint_w: int, footprint_h: int):
        """
        Mark a building footprint as walkable.
        Args:
            gx: Grid x coordinate (top-left)
            gy: Grid y coordinate (top-left)
            footprint_w: Footprint width in tiles
            footprint_h: Footprint height in tiles
        """
        for dx in range(footprint_w):
            for dy in range(footprint_h):
                self.set_empty(gx + dx, gy + dy)

