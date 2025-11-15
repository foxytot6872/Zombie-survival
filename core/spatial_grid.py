"""
Spatial grid for efficient entity queries.
Used for turret targeting and enemy separation forces.
"""
from typing import List
import pygame


class SpatialGrid:
    """
    Spatial grid for efficient spatial queries.
    Divides the world into cells for O(1) lookups instead of O(N) scans.
    """
    
    def __init__(self, cell_size=128):
        """
        Initialize spatial grid.
        Args:
            cell_size: Size of each grid cell in pixels (default 128)
        """
        self.cell_size = cell_size
        self.grid = {}  # {(cell_x, cell_y): [entities]}
    
    def clear(self):
        """Clear all entities from the grid"""
        self.grid.clear()
    
    def insert(self, entity):
        """
        Insert an entity into the grid based on its position.
        Args:
            entity: Entity with .pos attribute (Vector2 or tuple)
        """
        if not hasattr(entity, 'pos'):
            return
        
        pos = entity.pos
        cx = int(pos.x // self.cell_size)
        cy = int(pos.y // self.cell_size)
        key = (cx, cy)
        
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(entity)
    
    def get_nearby(self, pos, radius_cells=1):
        """
        Get all entities in nearby cells.
        Args:
            pos: Position to search around (Vector2 or tuple)
            radius_cells: How many cells to search in each direction (default 1 = 3x3 area)
        Returns:
            List of entities in nearby cells
        """
        if not hasattr(pos, 'x'):
            pos = pygame.Vector2(pos)
        
        cx = int(pos.x // self.cell_size)
        cy = int(pos.y // self.cell_size)
        
        result = []
        for dx in range(-radius_cells, radius_cells + 1):
            for dy in range(-radius_cells, radius_cells + 1):
                key = (cx + dx, cy + dy)
                if key in self.grid:
                    result.extend(self.grid[key])
        
        return result

